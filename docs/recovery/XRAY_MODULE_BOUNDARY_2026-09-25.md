# Xray 独立重构边界（设计检查点，尚未迁移）

日期：2026-09-25。目标不是换一套功能，而是在忠实恢复的发布版行为可编译、可回归后，把 Xray 与持续变化的 FongMi app 代码分离。原始 `README.md` 是功能意图，发布 APK 是已发版行为基准；`recovery/legacy-src/` 暂不作为未来架构直接发布。当前 `xray/` 是普通 app 工程已依赖的早期实验模块，不是忠实恢复完成品；固定上游的 faithful 组装采用原始 app/service/AIDL，不包含 `:xray`。

## 以实际依赖确定代码归属

已逐个查看 `recovery/legacy-src/com/fongmi/android/tv/xray/legacy/` 的 23 个 Java 文件的 import 和 FongMi 完整限定名引用。除 `LegacyXrayBitmapLoader` 引用 `PlayerManager`，`LegacyXrayServiceClient` 引用同一 Xray AIDL/Service 外，其他文件没有直接引用 FongMi app 类；但无直接 import 不代表没有媒体库/Android 依赖，也不代表可以免测试迁移。

| 目标归属 | faithful 基准文件 / 逻辑 | 与上游更新的边界 |
| --- | --- | --- |
| Xray Android library（首轮迁移建议，20 类） | `LegacyLibXrayApi`、`LegacyXrayServiceClient`、`LegacyXraySessionController`、`LegacyXraySettingsController`、`LegacyXrayRuntimeConfigFactory`、证书/分享链接/安全配置、代际门、服务调用及通用 SOCKS HTTP 资源、公开目的地拦截器等；加原 `XrayService` 与 `IXrayService`/`IXrayCallback` AIDL。 | Android/OkHttp/libXray 是模块自己的明确依赖；服务须维持独立 `:xray`，先保留原 AIDL 包名/参数与 operation ID 语义，避免同轮迁移又更换协议。 |
| FongMi 播放适配层（3 类 + 上游接线） | `LegacyXrayBitmapLoader` 直接依赖 `PlayerManager`；`LegacyXraySchemeGuardDataSource` 直接依赖 Media3 `DataSource`；`LegacyXrayPlaybackAddress` 含 FongMi 直播 `.strm`、YouTube 重定向的场景规则。`PlayerManager`、Exo/mpv 播放器工厂、`PlaybackService`、VOD/Live 会话控制器及播放器菜单仍是 app 适配点。 | 不让模块导入上游 `PlayerManager`、Media3 自定义 AAR 或 Home/Live/Video Activity；app 通过窄接口消费会话状态、端口、SOCKS 地址与通用策略。DRM、字幕、弹幕、封面/下载/切换重置仍需逐条对照行为矩阵。 |
| app 的电视网络恢复 | `TvNetworkLifecycle`、Home 网络代际与稳定检测、`BaseLoader.clear`、`catvod` `OkHttp`/`OkDns` 的正常 API 客户端重建及 Spider 生命周期。 | 它处理长期后台后普通 API/DNS 的陈旧状态，不能因提取 Xray 而整体迁入代理模块；播放器独立客户端不应在该路径被整体清理。 |
| 设置、导入及资源适配 | `SettingXrayActivity`、设置入口、手机 LAN 导入 action/网页、菜单和 strings/layout/Manifest 的服务声明属于 FongMi UI；设置操作控制器可留在 Xray 模块。 | UI 可重做接线但需保留保存/删除/测试、45 秒超时、分享链接和遥控器入口。 |

这不是文件数即完成度：恢复覆盖层还有 51 个上游覆盖文件、24 个独立 Xray Java 与 2 个 AIDL；其中大量上游文件包含非 Xray 的历史改动，不能直接全部移走或把整个 FongMi fork 称作模块。

目前实验性 `xray/src/main/aidl/com/fingmi/xray/service/IXrayService.aidl` 与 faithful 的 `recovery/legacy-src/aidl/com/fongmi/android/tv/xray/IXrayService.aidl` 具有相同的六种方法形状，但 **Binder interface descriptor 包名不同**。发布版 `uz3`/`dz3` 的 descriptor 是 `com.fongmi.android.tv.xray.IXrayService` / `.IXrayCallback`；迁移不能把“参数一样”误当作二进制协议兼容。第一阶段优先沿用 faithful 包名/AIDL，若将来改 descriptor，必须成对更换服务与客户端并单独回归 Binder 进程死亡、超时和旧回调。

## 最小、可回滚的迁移顺序

1. 先满足 faithful 基线门槛：验证固定上游源码与 AAR、取得 libXray AAR、APK 编译，并按行为矩阵在 TV 上跑关键路径；记录基线 SHA 和结果。
2. 保留 `recovery/legacy-src/` 为只读对照，优先把无 FongMi 类依赖的核心与服务/AIDL 搬入 Android library，尽量保留类/API/包名和 service 进程；不在同一提交重写状态机。
3. 仅在 app 建立窄适配：播放会话开始/结束、流媒体/侧请求网络注入、封面与设置/导入入口。按 VOD、直播、切换、失败/超时、Binder 死亡和后台恢复分别回归。
4. 完成同一套回归后才清理重复实现与重命名；以后上游 FongMi 更新时，只检查 app 适配点和其专属网络恢复补丁，模块自己的 Xray 核心变化单独审查。

## 未解决的门槛

- 当前未编译 faithful APK、未跑 TV；没有发布 APK 运行等价证明。不能直接启用实验性 `xray/` 替换 24 类恢复基准。
- 现有两个 ABI 各十个播放器原生库与候选 AAR 同 SHA-256，但 38 项 Java 方法仅是选取检查；资源和完整 Java/原生 API、`libXray.aar` 未完成。
- 需明确 Android Gradle module 的 AIDL 生成、Manifest 的 `:xray` 合并、libXray 二进制来源及上游 FongMi 与本模块的依赖方向；目前此文只固定归属和验收门槛，不宣称已有新接口或完成迁移。


## 实验模块会话收尾的静态对齐（仍未迁移）

对照发布版行为恢复层，本轮发现并修正当前 `xray/` 中旧 STOP 超时误断新 RUNNING 会话、STOP 成功后不主动断 Binder、START 成功后过早丢失 active ID 致 Binder 死亡无法通知会话三项问题；当前连接失败也清除旧 cleanup timer。修改只改善实验模块局部控制流，**不表示它能替换 faithful 源码**。尤其 AIDL descriptor 仍不同，配置/安全/网络路径尚需独立比对，Android 编译与电视回归未做。

## 分享链接归一化器的静态对齐（实验模块）

把 `xray/.../XrayShareLinkNormalizer.java` 的实现与双 ABI 原始 DEX 校正过的 `LegacyXrayShareLinkNormalizer.java` 对齐，仅替换包名和类名；核对归一化后的源码逐字节相同。原实验实现对 Hysteria2 重复 `ports`、`mport` 百分号原始字节、默认端口与 pin/obfs 顺序、authority hopping 的逗号编码，以及 VMess base64 片段存在行为漂移。普通 app 已依赖 `:xray`，该改动会影响普通 app 的 Xray 路径；没有 Java 编译或真机验证。迁移前还须核 AIDL descriptor 和其余配置/服务依赖。

## 服务与传输安全的后续静态核对

实验性 `XrayService` 已把 VALIDATE/TEST 的端口分配、配置创建纳入原版同样的绑定错误重试区间；START/STOP 回调无法投递且清理失败时改为带 operation ID 的 `cancelInternal`，旧回调不会直接杀掉新会话；工作线程设为 daemon，与恢复层一致。`XrayShareLinkSecurity` 对齐了证书存储值原样 ASCII 比较、WebSocket `type`/`host` 的精确小写键和 IPv6 字面地址检查。这是局部静态对齐，实验模块的证书重置、查询重写、AIDL descriptor 以及完整配置等仍须核对；没有编译或设备验证。

续查配置生成时，实验类原先少一次证书处理后的链接归一化，已对齐恢复层。实验传输安全类的查询重写与恢复类差异包括证书已有值时的键规范化、原始百分号字节保留、Hysteria2 空查询问号、TLS `security` 值小写及 IPv6 字面值；现以恢复类源码对齐，只适配模块包/类型与 `LibXrayBridge` 的 JSONArray ALPN 参数，适配后静态逐字节核对一致。配置构造本身仍有 `socksPort <= 0` 的实验性额外早停；模块其余依赖、AIDL/Manifest、APK 构建和设备行为未验。

证书存储 `XrayCertificatePins` 现直接适配 `LegacyXrayCertificateStore`（仅模块包/类名变化），其迁移和重置时的存储提交顺序、错误传播及 Android Keystore 删除与已核恢复层相同。实验 `XrayService.resetSecurityInternal` 调用该 `resetAll()` 并重建存储与安全配置帮助对象，静态控制流对齐。AIDL 协议、资源/Manifest 连接、编译和 TV 真机仍待验。

`LibXrayBridge` 的 Xray invoke 返回结构也已收紧到发布版：对象结果必须是 JSONObject，分享链接转换不得接受 JSON 字符串或用空对象替代错误；原始错误按 Unicode 代码点的空白判断后向上抛，末端服务再负责去敏。旧实验桥提前 trim/去敏可能改变端口绑定失败重试的异常文本。此次仍是源码静态对照，真实 libXray AAR 与 Android 编译尚缺。

实验错误去敏器之前缺少发布版针对 JSON 引号内敏感值的逐字符遮盖和 1024 字符截断，替换标记也不同。已适配恢复类，并保留 `sanitize(Throwable)` 兼容入口；服务异常走 `fromException`，与恢复层相同。代际门的 compareAndSet / invalidate 行为静态一致，仅名称与访问级别不同，未改。

## 两条构建路径的接线澄清

普通 `settings.gradle` 包含 `:xray`，`app/build.gradle` 有 `implementation project(':xray')`，普通 leanback `SettingXrayActivity` 直接调用模块归一化器、设置控制器和错误去敏器；模块 Manifest 声明 `com.fingmi.xray.service.XrayService` 在 `:xray` 进程。故本轮对实验模块的修正可能影响普通 app 的 Xray 功能，不能称“未接入 app”。

`recovery/legacy-src/upstream/settings.gradle` 只包含 app/catvod/chaquo/quickjs/libxray，faithful 的 leanback Manifest 声明 `com.fongmi.android.tv.xray.XrayService`，服务源在 `recovery/legacy-src/com/fongmi/android/tv/xray/`。因此**普通 app 模块的修改不等于 faithful 基准已变更或迁移完成**。两条构建路径均尚未在本地编译，普通 app 的 UI/会话/播放器接线也未完成整体验证。

服务客户端续查：实验实现原把新绑定与回调有效性共用 `connectionGeneration`；旧绑定失败后如新绑定先于主线程失败通知，通知会被吞掉。现分设 `callbackGeneration`，仅断连/失败时失效旧回调；新绑定仍用独立编号识别连接。旧连接失败分支补解绑，绑定超时仅在仍处于 binding 且尚无 service 时执行。与恢复的 `LegacyXrayServiceClient` 静态控制流对照，未做线程竞态或真机测试。

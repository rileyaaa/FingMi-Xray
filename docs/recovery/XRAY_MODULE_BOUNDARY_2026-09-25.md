# Xray 独立重构边界（设计检查点，尚未迁移）

日期：2026-09-25。目标不是换一套功能，而是在忠实恢复的发布版行为可编译、可回归后，把 Xray 与持续变化的 FongMi app 代码分离。原始 `README.md` 是功能意图，发布 APK 是已发版行为基准；`recovery/legacy-src/` 暂不作为未来架构直接发布。当前 `xray/` 是早期实验模块，不是忠实恢复完成品。

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

把 `xray/.../XrayShareLinkNormalizer.java` 的实现与双 ABI 原始 DEX 校正过的 `LegacyXrayShareLinkNormalizer.java` 对齐，仅替换包名和类名；核对归一化后的源码逐字节相同。原实验实现对 Hysteria2 重复 `ports`、`mport` 百分号原始字节、默认端口与 pin/obfs 顺序、authority hopping 的逗号编码，以及 VMess base64 片段存在行为漂移。此改动仍未接入 app；没有 Java 编译或真机验证。迁移前还须核 AIDL descriptor 和其余配置/服务依赖。

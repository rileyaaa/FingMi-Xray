# FingMi-Xray 开发与维护

本文面向维护当前 `main` 的开发者，说明**工程基线、模块接线、构建依赖、上游同步方式和验证规则**。当前开发、上游同步与后续验收基线统一为 `main`。

长期架构边界见 [PROJECT.md](PROJECT.md)。`v5.6.0-xray.5` 的恢复、native provenance 与 v7 Xray 黄金行为证据见 [RECOVERY.md](RECOVERY.md)。当前 `main` 负责架构与构建验证，v7 黄金参考负责约束 Xray 外部行为；两者不能混为旧 faithful 架构重建。

文档状态：`ORIGINAL_README.md` 是用户明确指定的冻结旧发布说明，只读不改；`AI_COLLABORATION.md` 是当前协作规则的 canonical 文档，用户调整开发限制时应同步维护。当前工程事实、长期架构和历史证据分别继续维护在本文、`PROJECT.md` 与 `RECOVERY.md`。

> **阅读顺序**：第 1–9 节为当前工程事实和操作入口；第 10 节是按日期留存的历史维护记录（不是当前状态）；第 11 节说明现行 5.6.3 与未来升级的特别约束；第 12 节统一保存上游一键升级工具说明及 5.8.7 失败复盘。当前版本以 `app/build.gradle` 为准，发布资产以 GitHub Release 和对应原始构建证据为准。

## 1. 当前工程基线

当前应用采用下列 FongMi/TV 固定公开源码基线；该提交的 `app/build.gradle` 版本名为 5.6.3：

- 上游目标 commit：`c616c0aa3613e87529791587a9f71b78c278c991`
- 上一固定基线：`4afc4473e22a7ed3d98ee12233e0c2a490061000`（5.6.3）
- 两者是直接父子 commit；新增 runtime 变化集中在 `catvod` 的 redirect-aware proxy selection/authentication。Release / APK 的更高版本号不改变本项目的公开源码上游基线。
- app `versionCode`：`563001`
- app `versionName`：`v5.6.3-xray.1`
- Java：21
- Gradle wrapper：9.7.1
- Android Gradle Plugin：9.3.1
- `compileSdk` / `targetSdk`：37
- `minSdk`：24

当前 `main` 是源码、架构和上游同步基线。Xray 外部行为则以用户长期验证稳定的 `v5.6.0-xray.5` armeabi-v7a 正式 APK 为黄金参考，并由 readable reference、source guard、JVM lifecycle test 与真实发布 native 动态 parity 映射到当前模块。正常发布不要求重新构建旧 faithful APK。

### 维护范围

当前 fork 的**业务代码维护范围只有两块**：

- Xray 播放代理；
- Android TV 网络恢复。

其他 FongMi/TV 业务功能默认跟随固定上游版本。不要为了“顺手优化”“统一风格”“低版本兼容”“播放器增强”或一般性重构去改与这两块无关的上游代码。

允许的外围修改仅限：

- 两大模块接入 FongMi 所需的最小 hook / adapter；
- 当前固定媒体二进制与上游 API 之间不可避免的最小构建 compatibility adapter；
- 构建、发布、测试 guard 与禁用上游自更新等 fork 维护基础设施。

任何超出上述范围的代码修改，在提交前都应先判断：**这个变化是否是 Xray 或 TV 网络恢复的必要条件？如果不是，默认跟随上游。** 用户允许的例外仅限像已发生的主机名崩溃一样，有明确证据、明显影响实际使用的上游故障；只做最小修补，并在下方登记，不能据理论风险扩展普通业务维护。

### 已登记的上游业务修复（升级前必读）

**当前只有一项上游业务补丁：`OkProxySelector.Policy` 空主机名崩溃，用户于 2026-10-11 明确授权。**

| 项目 | 记录 |
| --- | --- |
| 源码位置 | [`catvod/.../OkProxySelector.java`](../catvod/src/main/java/com/github/catvod/net/OkProxySelector.java) 的 `Policy` 构造方法 |
| 上游基线与触发 | 公开 5.6.3 / `c616c0aa…`；搜索后播放某些 OkHttp 接受的域名（如下划线域名），Java `URI.getHost()` 返回 null，随后 `toLowerCase()` 引发 NPE；用户日志与正式 APK 的 R8 map 已匹配 |
| 最小修改 | 从 OkHttp `HttpUrl` 读取规范化 scheme、host、有效 port，避免空主机名，并保持不同 origin 隔离；代理选择、匹配、凭据继承与重定向规则原样保留 |
| 回归入口 | [`OkProxySelectorTest.java`](../catvod/src/test/java/com/github/catvod/net/OkProxySelectorTest.java)；`./gradlew :catvod:testDebugUnitTest`，现有 14 项加两项空 host 回归共 16 项；同一回归对独立公开上游复现两项 NPE 失败 |
| 跟随上游时 | 检查上游是否已修复对应输入；若已有等价修复且上述回归通过，采用上游实现并移除本补丁，不重复保留两套处理 |

完整故障证据见[退出播放页与请求主机名崩溃记录](#2026-10-11--退出播放页与请求主机名崩溃)。此前 Glide 销毁期间清理、播放交接和缺少 decoder 的问题属于本 fork 的接线或构建遗漏，不能误记成其它上游业务修复。后续新增例外必须同样记录触发条件、证据、修改范围、回归入口和上游同步处置；执行边界见 [AI_COLLABORATION 第 9 节](AI_COLLABORATION.md#9-开发与-bug-修复范围只限-xray-和-tv-待机网络恢复)。

## 2. Gradle 模块

`settings.gradle` 中的主要模块：

| 模块 | 职责 |
| --- | --- |
| `:app` | FongMi/TV 应用、VOD / Live、播放器、UI 与项目接线 |
| `:catvod` | Spider 与普通网络基础 |
| `:chaquo` | Python / Chaquopy 相关能力 |
| `:quickjs` | QuickJS 相关能力 |
| `:libxray` | 本地 `libXray.aar` 依赖容器 |
| `:xray` | 模块化 Xray 实现 |
| `:tv-recovery` | 独立 TV 前后台网络代际与恢复协调核心 |

`:app` 直接依赖 `:xray`，`:xray` 再依赖 `:libxray`。这样可以把 Xray 的 Service、配置与网络资源从 FongMi 业务代码中分离。

`:app` 同时依赖 `:tv-recovery`；恢复模块没有对 `:app`、`:catvod` 或 `:xray` 的反向依赖。`app/src/main/java/com/fingmi/integration/` 保存项目自有的 FongMi 适配代码，属于接线层，不能把普通上游功能复制到这里长期维护。

## 3. 当前 Xray 接线

### `:xray`

当前模块源码位于 `xray/src/main/`，主要分为：

- `config/`：配置、显示与分享链接归一化；
- `core/`：`LibXrayBridge`；
- `network/`：SOCKS HTTP client、RTSP SocketFactory、destination guard；
- `security/`：证书 pin 与分享链接安全存储；
- `service/`：私有 `XrayService`、operation / generation；
- `session/`：Service client、播放会话、设置控制；
- `util/`：错误去敏。

Manifest 中的 `XrayService`：

- `android:exported="false"`
- `android:process=":xray"`
当前 runtime config 还固定以下网络边界：

- session SOCKS inbound 只监听 `127.0.0.1`；
- proxy outbound 使用 `ForceIP`，当前会话 DNS 请求通过 Xray DNS inbound 路由到 proxy outbound；
- Core routing 直接 blackhole localhost、RFC1918、link-local、ULA 等本机/私网/保留 IPv4/IPv6 范围；
- HTTP(S) 层再由 `PublicPlaybackDestinationInterceptor` 对最终目标做一次 destination guard；RTSP / RTSPT 则通过 SOCKS SocketFactory 使用 unresolved target，让目标解析留在代理侧。


### Android 运行时兼容与 native 边界

源码使用 Java 21 编译并启用 desugaring，但 Android 设备上的 `java.*` 运行时仍由 ART 提供，不能把“javac 可编译”当成“Android 12 / SDK 32 一定可调用”。

兼容策略以**不破坏上游 FongMi/TV 已验证行为**为前提：

- 不对 FongMi/TV 原样业务源码做全局低版本 API 扫描后机械改写；上游原样代码默认继续使用上游的 `minSdk`、desugaring 与实现方式；
- 低版本兼容审计只覆盖 FingMi-Xray 新增代码、TV 网络恢复新增代码，以及两者必要的上游接线；
- 如果反编译 APK 显示 `j$.*` / desugared-library 调用，恢复源码必须保留等价的 desugaring 语义，不能因为“可读性”把它改成旧 ART 不存在的直接 `java.*` 调用；
- 只有确认某个调用是本项目引入、且在目标 Android 运行时会真实 linkage failure 时才改代码；如果同一写法本来就是目标 FongMi 上游实现，则优先保持上游，除非有独立证据证明必须补丁。

当前 Xray 路径已经明确约束：

- 不使用 `StringBuilder.isEmpty()`；
- 不直接使用旧 ART 不具备的 `URLDecoder/URLEncoder` Charset overload；
- Xray 关键路径避免 `String.isBlank()`、`Set.of(...)` 等已知会造成旧 Android runtime linkage 风险的调用；
- `tests/test-xray-android-runtime-compat.py` 在 `main` 构建前扫描这些风险，并同时检查 libXray / gomobile 的 release keep rule。

`LibXrayBridge` 是 Java 与 Go JNI 的故障边界。它会把 Java linkage failure 转成可返回的 Xray 错误；`XrayService` 的 validate / test / start / stop / reset 路径以及 `XrayServiceClient` 也会收口对应 `LinkageError`。这样类似 `NoSuchMethodError`、`NoClassDefFoundError` 或 `UnsatisfiedLinkError` 时，优先向 UI 返回具体错误，而不是只显示 `Xray service process died`。

current 已按黄金发布行为移除额外的逐次 native invoke `System.err` begin/end 日志，不再为了调试向发布路径加入旧 APK 没有的噪声。native 故障继续通过 Service/client 的明确错误收口、Binder 进程状态、Android logcat 与定向 native parity / QEMU harness 定位。

release 混淆规则必须保留：

```text
-keep class libXray.** { *; }
-keep class go.** { *; }
```

### VOD / Live

Leanback `VideoActivity` 和 `LiveActivity` 直接持有 `XrayPlaybackSession`。

Activity 负责：

- 建立当前播放 identity；
- 响应用户开启 / 关闭 Xray；
- 在切集、切台、换源、换线路、刷新或播放器重建等**逻辑播放身份变化**时默认结束旧会话；用户明确开启的连续电视直播自动规则命中场景例外，仅保留代理 transport，播放身份仍推进；
- 同一播放身份内的 parser 解析结果、HTTP redirect 或 CDN URL 变化只更新当前媒体 URL，不自动停止 Xray，也不回退到直连；不支持的最终请求继续由 Xray scheme / destination guard fail-closed；
- Live 尚未建立 playback session 时，先按发布版 direct-source 规则拒绝 HTTP(S) `.strm` / YouTube indirection，成功后才清 preload 并启动 Xray；
- 把新的 `XrayHttpClient` 交给播放器；它保持发布 `pz3` 的资源语义：getter 始终返回会话持有的 OkHttp / RTSP factory，close 只负责幂等 shutdown + 异步 cancel/evict，不额外把 getter 改成同步 `IllegalStateException`；
- 在 Activity 销毁时关闭 session。

业务页面只决定“当前是什么播放身份”，不实现 Xray Core 细节。

### TV Live 自动开启规则（2026-11-24，开发源码）

`XrayLiveAutoRules` 解析两个最多 4096 字符的规则列表；空白/空项忽略，精确名称与 `*` 通配符按整串匹配（不区分英文大小写，不作为正则表达式），中英文逗号和换行均可分隔。分组或原始/显示频道名任一命中即可。`XrayPreferences` 在现有节点保存事务中一起持久化，删除节点时清除规则。Leanback 节点设置页、原扫码页面及 `XrayLiveRulesEvent` 支持独立填写规则，不读取或回传节点凭据；LAN 输入只填表单，不自动保存。

`LivePlaybackHost.prepareXrayForPlaybackChange` 默认为旧 reset hook；仅 Leanback Live 用 `XrayLiveAutoPlayback` 记录当次命中、手动 OFF、待启动播放及失败重试。新请求推进 `PlaybackIdentityGate`，连续自动命中允许 `beginLiveAuto` 保持 RUNNING/STARTING transport；解析成功并通过原 direct-source guard 后才启动/使用代理，等待 RUNNING 安装完成后再送入播放器。规则不命中、回看、换配置/引擎、owner 交接和后台/销毁按原边界停止；已取消的待播回调不能重新启动旧台。规则未配置时不改变黄金默认路径。保留原远端目的地址限制；普通解析/API 不走全局代理。新台预览和等待代理期间抑制远端 artwork/EPG；即使 Core 已就绪，当前台也必须独立通过 URL 检查才可恢复元数据。复用 transport 时显式取消旧 XML/EPG、字幕、弹幕及远程图片任务，清除播放器保留的弹幕源。XML/EPG 完成与失败结果在主线程交付前再次校验各自任务代际，防止取消前已排队的旧结果串入新台；不修改普通节目表缓存与解析规则。上述代际与 URL 请求身份校验仅由 Leanback 的 Xray 宿主显式启用，涵盖直连与自动代理的双向切换；Mobile 仍走功能新增前的 LiveData.postValue、语义匹配及清理路径，不将此修复扩展至普通直播业务。手机规则提交必须由实际设置表单确认填入才返回 HTTP 成功；缺少字段、超限、关闭/销毁设置页或 RESET_SECURITY 时拒绝。仅主线程派发，HTTP 线程有界等待，尚未派发的超时任务取消，不自动保存。手动 OFF 对当前台及其换线有效，换台重新判定。Live pending 的代理安装以真实 binding owner 而非旧 PlaySpec key 判断。自动换台取消上一身份的播放超时；URL 结果在主线程按实际请求对象二次校验，拒绝 A→B→A、同线路刷新等旧回调；前台 reclaim 与同台重复选择不覆盖同 owner 尚在解析或等待 START 的自动请求；真正 binding owner 交接时取消旧 URL 任务、清除待播状态但保留所选频道，重新进入 Live 时重新判定当前规则，防止旧解析结果绕过代理；reclaim 标记保留至 prepare 消费，以便规则不再命中时恢复台标与 EPG，仍命中则继续抑制。更换直播源时主动取消旧自动 URL/元数据任务、清理旧 artwork，并在清空频道 adapter 后解除台标抑制，即使尚未建立代理、没有 detach 回调也不会将旧显示状态带入新直播源；若 onStart 尚未取得 binding，onResume 在实际取得 owner 并恢复待播请求后再次幂等解除自动策略的 suspend，避免恢复的频道永久等待 START；尚未解析的自动请求不因重复点击 Xray 而降级为手动 pending。真正切换播放器时仍先结束 Xray；未解析完成的 URL 请求继续走普通播放，若解析完成但媒体仍被 START 或失败状态挂起，则重新提交当前频道且不重新判定自动规则，主线程在新 engine 选择后交付结果，避免丢失待播频道或一直显示加载。若清空 PlaySpec 后才结束复用的代理，播放器仍须释放持有该代理的空闲 Exo 引擎并恢复普通引擎，不能保留已关闭的 HTTP client。

`tests/test-xray-live-auto.py` 编译实际规则、自动策略、播放 session、身份和地址类，用确定性 controller/网络替身验证匹配、异步 START、连续命中复用、快速换台、手动关闭、错误重试、非代理源、后台及关闭；由 playback parity 自动调用。保留旧版绑定交接及 artwork 回归；本次功能仍需完整 Leanback 构建和真机换台验证，不代表当前正式 APK 已包含该功能。

关闭会话时先卸载播放器代理、清空会话资源引用，再幂等关闭独立 HTTP Dispatcher，异步取消请求并淘汰连接；普通 player client 不随之销毁。STOP 成功后立即解绑，已派发的 STOP 超过 1.5 秒则取消并解绑，未建立连接由 5 秒 bind timeout 收口。500 ms 仅是 controller 关闭且没有待处理 STOP 时的兜底。最后一个客户端解绑、Android 销毁 Service 后，私有进程等待停止最多 3 秒，最终调用 `killProcess` 回收 Go/native 堆；多个合法 Binder owner 尚未全部离开时不能把进程存活直接判成泄漏。HTTP 清理线程在空闲 5 秒后退出。对象可回收和应用总 RSS 立即下降不是同一指标，设备验收应同时观察 `:xray` 进程退出、连接/线程收口及多轮操作后主进程内存是否持续增长。

多个播放 Activity 交接时，由原有 `PlaybackService.claimBinding` 的旧 owner 回调先触发 Leanback 的 `onXrayBindingReplaced`，同步结束旧 Xray 身份，再执行上游 PiP 关闭和新 owner 的播放任务。不能只依赖旧 Activity 较晚的 `onStop`，因为新页可能已改变共享播放器 key，导致旧页的 owner 检查跳过代理卸载。同 owner 的重复认领不触发此钩子，Mobile 默认钩子为空；不在 `PlayerManager.start` 无条件清代理，以免误关 Live pending 时已经手动开启的新会话。

### Settings / Binder

设置页在 UDP 下提供默认关闭的 **TLS 分片**开关；仅保存一个 `tls_fragment` 布尔值，不增加参数编辑器、代理出站或依赖。用户已在自己的网络验证的预设为 `tlshello`、`80-120` 字节、`5-10` 毫秒。固定 v26.7.28 核心使用 `streamSettings.finalmask.tcp` 的 `fragment`，其中等待字段是 **`delay`**，对应旧 `freedom.fragment` 的 `interval`，不能把 v2rayN 的 `Fragment4RayItem` 原样当作核心 JSON。只分片首个 TLS ClientHello，正常后续数据不按此预设分片；它可改善部分网络的握手兼容性，本身会增加分段与等待，不承诺普遍降低延迟或提高带宽。

开关通过不可变 Request / AIDL 显式传入 validate、test 和 start，与节点及 UDP 同次保存；未保存的设置用于连接测试，播放启动读取已保存值。测试进行中改变分片选项会使旧测试结果显示“设置已修改，请重新测试”；删除节点同时清除开关。关闭或旧安装没有该键时，保留黄金默认配置；开启是用户授权的有意行为扩展。分片只作用于 TCP 类 TLS/REALITY；HY2、KCP、QUIC、无 TLS，以及 XHTTP 仅 `h3` 的 ALPN 保持原样。既有 TCP mask 保留，新增 fragment 放最前，不重复添加已有 fragment。

**DNS 边界不因分片改变。** 当前已有经代理出站的 DoH（1.1.1.1、8.8.8.8）及 TCP/53 回退，服务于代理内目标解析；节点域名引导解析仍走系统 DNS。节点地址为 IP 时，显式 SNI、WS Host 分别是 TLS/HTTP 身份，不替代连接地址。分片不能把被污染为回环的节点域名恢复成正确地址；本轮不额外增加 DoH 设置，也不把节点引导策略切到依赖同一代理的 DNS，避免启动循环。`allowInsecure=1` 且尚无受信任 pin/name 的 TLS 链接，仍先执行既有证书预探测；该独立 probe API 不携带运行配置的分片选项，不能为分片绕过证书校验。

分享链接兼容目标沿用冻结发布说明：以 **v2rayN 导出的标准单节点分享链接**作为主要兼容与测试目标；v2rayN 只是格式来源，不是工程依赖。当前 normalizer / native chain 继续由 `tests/test-v2rayn-share-chain.py`、`tests/test-v2rayn-reference-chain.py` 与发布 native parity 约束。

设置页的 VALIDATE / TEST / RESET_SECURITY 由 `XraySettingsController` 串行拥有单一 operation generation，45 秒 timeout、abandon、client replacement 与 stale callback 丢弃都在 controller/client 边界收口。

RESET_SECURITY 保持发布版顺序：先占有 reset generation 并替换 Binder client，再清本地安全配置；本地清理成功后才清 UI，最后派发远端 security reset。同步失败时会清 active generation 并再次替换 client，避免旧 Binder 状态继续持有操作。

`XrayServiceClient` 保留约 5 秒 bind timeout、remote cancel 后 unbind、Binder death / binding died / null binding / disconnect 收口，以及 ServiceConnection / callback generation 过滤。

### 播放器

`PlayerManager` 通过 `setPlaybackProxy(...)` 切换当前播放网络资源。

启用 Xray 后：

- 预加载不会复用普通直连身份；
- active proxy 强制使用能够注入该会话网络资源的 Exo engine，不让 MPV 或其它普通 engine 静默继承一个无法完整表达的代理状态；
- `ExoMediaSourceFactory` 的 HTTP / HTTPS 使用 Xray client；
- DRM license 跟随相同 DataSource；
- RTSP / RTSPT 使用 Xray SocketFactory，并以 unresolved target 交给 SOCKS 侧解析；
- 无 scheme 的本地路径以及 `file` / `asset` / `content` / `data` / `rawresource` / `android.resource` 等 Android 本地资源 scheme 仍按本地资源处理；除 HTTP(S) 与这些明确本地 scheme 外，其它泛用 DataSource scheme 在 Xray active 时 fail-closed；
- 字幕、弹幕、EPG/XML 等已经与播放身份绑定的远程旁路通过 `PlayerManager.getPlaybackHttpClient()` / `withHttpClient()` 获取当前 client；远程 MediaSession artwork 在 Xray active 时直接阻断，VOD/Live artwork/logo 也按黄金行为抑制普通远程加载。

关闭或切换身份后，播放器重新回到普通 FongMi 网络资源。真正切换播放器属于播放身份变化：Activity 先结束当前 Xray generation，再按上游规则选择新的普通 engine；不是在同一 Xray 会话中把 proxy 直接塞给 MPV。

Leanback Live / Video 的 artwork target 正常加载仍绑定 Activity；清理通过 Application 的 Glide manager 委托原 owner 取消，不能在 `onDestroy()` 中重新获取已销毁 Activity 的 manager。退出或销毁后的 Xray 回调仍先卸载播放器代理、取消元数据请求，再跳过 logo / artwork / EPG 与状态 UI 更新，避免清理期间重新发起请求。

## 4. TV 网络恢复

TV 网络恢复没有放进 `:xray`。

主要入口：

- `tv-recovery/src/main/java/com/fingmi/tvrecovery/TvNetworkLifecycle.java`
- `tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java`
- `app/src/main/java/com/fingmi/integration/recovery/FongMiNetworkRecovery.java`

`TvNetworkLifecycle` 由 Leanback `HomeActivity.initView()` 创建 `FongMiNetworkRecovery` 适配器时首次安装，随后注册 Application 级 Activity lifecycle 与 SCREEN_ON / SCREEN_OFF receiver 来生成前后台 / screen 网络代际；它不是 Application 冷启动时无条件创建的第二套网络服务。Home 持有适配器，适配器持有独立模块的 `NetworkRecoveryCoordinator`，仍只在 Home 的 `onResume()` / 窗口重新获得焦点时检查并执行每个待恢复 generation 的普通网络重建。Home 不再实现网络状态判断或资源重建流程，仅提供取消页面请求、进度显示、存活判断和刷新回调。

首次从 exported 播放页冷启动、之后才进入 Home 时，监控器可能没收到旧页面的 START。核心按 Activity 对象身份记录实际收到的 START，只由匹配的 STOP / DESTROY 移除；未知或重复 STOP 不得误扣仍可见的 Home。DESTROY 清理尚未退休的引用，正常 STOP 后幂等无动作。配置重建、SCREEN 代际与 DLNA 启停的既有规则保持不变；这是对黄金 `gn3` 整型计数的有意修复，回归由 `tests/test-tv-recovery-cold-entry.py` 编译真实核心和双 flavor 适配器执行，不将监控器迁入上游 App。

发布版 generation **只**由真实后台 / SCREEN_OFF 后重新进入前台 / SCREEN_ON 推进；前台 Wi-Fi、VPN 或默认网络切换本身不额外创建 generation。Home 也只在自身 `onResume()` / 重新获得窗口焦点时检查是否需要恢复，隐藏在其他播放页面后的 Home 不主动执行恢复。`recoveredGeneration` 只用于防止 Home 重建时漏掉尚未完成的 generation，不增加新的触发来源。

恢复过程在同一 Home coordinator 内按 generation **串行**：如果当前 Spider clear / 网络稳定轮询尚未结束，新 generation 先等待；旧流程发现 generation 已变化后才结束本轮并启动下一轮。跨 Home 重建时，旧 owner 的 close 只废弃回调和轮询，并不能取消已派发的 Spider 清理。为防止新 owner 或普通配置清理与旧任务重叠，所有 `BaseLoader.clear()` / `clear(after)` 通过 `MoreExecutors.newSequentialExecutor(Task.executor())` 共用一个专属 FIFO 队列，复用原有普通后台线程池，不另建线程池，也不占用 `BackupManager` 备份/还原及 `History.clear` 所用的 `Task.executeSerial` 队列。仍按 Jar → Python → JS 顺序清理，并在各自任务完成后 post 回调。此修正只序列化共享 loader 的清理，不新增恢复触发、全局恢复状态机或普通 Spider 业务逻辑。回归 `tests/test-tv-recovery-spider-clear.py` 已纳入现有 TV recovery 检查入口，使用实际 BaseLoader、Task、coordinator 与 JDK executor，Android / Guava / Spider 为测试替身，覆盖旧 Home 在清理中关闭、普通配置清理、新 Home 接手、迟到回调不刷新旧 owner，以及 Spider 清理与备份/历史任务的串行队列双向隔离。Guava 替身只模拟 FIFO 委派，不证明其真实库内部实现。

每一轮顺序：

1. 取消旧业务请求；
2. 重建普通 API / DNS / DoH transport，但不销毁播放器专用 client；
3. 串行清理 Spider；
4. 以约 500 ms 周期等待网络稳定，连续两次具备 Internet capability 后继续，最多约 12 次检查；
5. 刷新 Home。

DLNA 生命周期通过模块的 `Renderer` 接口接入 `com.fingmi.integration.recovery` 下 flavor-specific `TvDlnaLifecycle`：

- Leanback 实际启停 DLNA renderer；
- Mobile 为 no-op。

因此 Mobile 不需要依赖 Leanback-only 的 DLNA Service。

`tests/test-fork-module-boundaries.py` 检查两个核心模块不依赖 FongMi / catvod / 应用适配类，并编译执行真实 lifecycle、coordinator、FongMi adapter 与 Leanback/Mobile 桥；Android/HTTP/Spider 是边界替身。它覆盖冷启动、配置重建、熄屏唤醒、两次稳定检查、Home 重建、迟到清理回调、失效 owner 与 DLNA flavor 行为，已接入现有 TV recovery 验证入口。独立 Gradle 验证命令为 `bash gradlew :tv-recovery:assembleDebug :tv-recovery:testDebugUnitTest`。

TV recovery 的维护边界必须保持小。固定上游 `FongMi/TV@c616c0aa3613e87529791587a9f71b78c278c991` 下，普通 `KeepActivity`、`SiteApi`、`BaseConfig`、`VodConfig`、`LiveConfig`、`WallConfig`、`LiveParser`、`ConfigEvent` 与 `Notify` 不承担 recovery 状态机，必须保持固定上游 Git blob；`tests/test-tv-network-recovery.py` 会直接验证这一范围。待机恢复只允许在 Home/lifecycle/coordinator、普通 API/DNS/DoH reset、Spider clear、Glide 与必要的请求取消 hook 内维护。没有真机或明确黄金证据时，不得再把 Config replay、task owner、Spider lease、deferred UI/navigation 等状态扩散进普通 FongMi 业务代码。

## 5. 当前媒体兼容层

FongMi/TV 业务、UI 与播放器行为只以公开源码上游为准。任何只存在于更高版本 Release / APK、但未进入公开源码的 Dolby、MPV、ISO 或光碟导航行为都不得反向迁入 `main`。这里保留的媒体差异只允许是**让当前公开 FongMi/TV 与固定公开 FongMi/media 能正常构建所必需的最小 compatibility adapter**。

### Media3 / Libass

当前构建从固定公开 `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d` 重建 player candidate。Libass extractor 的 Matroska / ASS hook 不再由本仓库从当前源码反向打补丁重建，而是直接使用公开历史 `FongMi/media@9dae39e9689ee305c83f94bd11cf3bcecb9d6171` 的真实 `MatroskaExtractor.java`；仓库只保留当前 5.6.3 接线所需的最小 copy-constructor patch，以及公开历史中不存在、只能从发布行为恢复的 subtitle sample timestamp overload/call。

主要材料：

- `compat/media3-libass/`
- `compat/media3-libass/tests/`
- `compat/media3-libass/media-tests/`
- `scripts/build/build-libass-extractor.py`
- `scripts/build/build-libass-candidate.py`
- `scripts/build/check-libass-contract.py`
- `scripts/build/import-libass-candidate.py`

适配范围限于现有调用面所需的 native loader、Matroska / ASS hook、primary / secondary subtitle、parser / playback session、renderer / EGL-GLES 生命周期、PlayerView controller 与 subtitle sample timestamp。它是构建兼容层，不是第三套 FongMi 播放器实现。

player candidate 每次从固定公开源码现场重建 18 个 AAR，显式包含基础 `lib-decoder` 及 FFmpeg/MPEG-H 扩展。`player_candidate.py` 校验产物集合、manifest digest、关键类及 Media3 字节码符号依赖。AAR 本身不携带 Gradle 传递依赖，不能只凭依赖方 AAR 编译通过就认为运行依赖齐全；candidate 唯一外部 Media3 模块为随后由 Libass importer 按原固定摘要导入的 `media3-container-1.11.0.aar`。Android R 类仅按所属 AAR 的 Manifest/R.txt 认定为生成类。

导入完成后，`tests/test-player-startup.py` 从实际 `app/libs` 提取 class，使用 Robolectric 构建/释放真实播放器和 renderer；测试不得从 Maven 引入另一份 Media3 来补齐生产缺失。最终 `check-final-apk-media3.py` 读取所有 DEX 的 `type_ids` / `class_defs`，要求每个 Media3 类型引用都有类定义，并检查三个 JNI/public buffer 的明确保留。不能用 `strings` 找到类名代替类定义存在；签名、Manifest、native provenance 与最终 DEX 依赖均需验收。

### app adapter

app 中只保留当前公开播放器 API 与本 fork 接线所需的小型 adapter，例如 `LibassFontFile`、`DanmakuPlayerViewController`，以及 Xray 播放网络注入所需的 PlayerManager / Exo / MPV hook。不能因为 adapter 存在，就继续维护一套偏离上游的播放器功能。

### MPV 与 Release-only 证据边界

current player candidate 使用固定公开 FongMi/media 的 MPV 源码。current `MpvPlayerEngine` / `MpvUtil` 只保留当前 app 调用面所需的 secondary subtitle、font 与 config option 兼容映射。

历史上曾对高于公开源码的 Release-only Dolby、MPV stream、remote ISO、`libisoJNI.so` 和 disc-navigation 做过取证；这些材料只属于历史研究证据，**不属于 `main` 的实现目标**。current build 不得恢复这些 Release-only 功能，也不得把对应播放器行为带回公开上游代码。发现这类差异时，默认恢复公开上游实现，除非它是 Xray、TV 网络恢复或当前构建不可避免的最小兼容条件。

## 6. 二进制依赖

大型 AAR / APK / SO 不作为普通源码直接提交。`main` 的二进制处理只服务于可重复构建和 Xray provenance，不用于追平 FongMi Release-only 播放器功能。

公开 [FongMi/TV 5.6.3 构建说明](https://github.com/FongMi/TV/blob/c616c0aa3613e87529791587a9f71b78c278c991/README.md) 要求另备 `app/libs/lib-*.aar`，明确说明这些配套 AAR 未纳入 Git，单纯 clone 不包含完整播放器依赖。其公开 workflow 只有网站部署，无法据此核对上游内部 APK 构建链。旧 Release APK 下载返回 404，不等于公开源码消失或上游无法编译；本 fork 从旧 APK 提取固定 Libass native 是重构遗留输入路径，上游拥有配套 AAR 时不需要经过它。上游未公开的 AAR 制作/保存过程和旧资产删除原因不作推测。

当前可重复构建依赖：

- 从固定公开 `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`（`release-1.11.0-fongmi` 分支）现场重建的 18-AAR player candidate；该分支与仓库默认 `release` 分支不同，不能把它称为默认分支 HEAD；
- 历史 `v5.6.0-xray.5` 黄金 APK：只为 Xray API v2 Java bindings / Go JNI 提供成套 provenance，并作为 Xray 外部行为与 native parity 的黄金参考；current player / FFmpeg 不从该 APK 回灌；
- 官方 libXray v26.7.28 AAR 外层容器；
- 按固定公开 Media3 输入重建的 Libass compatibility AAR；
**当前构建债（不是上游基线）**：公开 `FongMi/TV@c616c0aa...` 明确是 5.6.3，且本项目唯一上游仍是这条公开源码线。公开 `FongMi/media@3c2c...` 不包含 `libraries/exoplayer_libass/`；Libass compatibility 使用的固定 `libmedia3ass.so` 最初取自 FongMi Release 5.6.8，现从本项目保留的已发布 APK 中读取完全相同的字节。上游原下载地址已返回 404，不再作为正常构建依赖。这只修复容器的可用性，**没有移除原生库缺少对应可重建源码的技术债**，不能称为公开上游、不能用于引入任何 5.6.8 App/播放器行为，也不能声称所有二进制输入都仅来自公开 5.6.3。

正常构建先从本仓库已发布、非草稿且符合正式版本命名的 Release 中按数字版本选择最新容器，读取两个 ABI 资产并校验 native，再进行昂贵重建；排除黄金参考和源码备份，最高版本缺少资产时失败，不静默回退。容器可被标为预览，选择不依赖 `Latest` 展示标记，报告记录实际预览状态，不把容器认定为当前正式版；信任边界仍为固定 SO 摘要，容器中的 DEX、资源和其它库不作为输入。实际 Release/资产身份与 APK 摘要单独记录，不能把本项目 APK 冒称原始上游 APK。同名替换会改变容器摘要，但不允许改变 native pin 或 Libass candidate 摘要。新发布先完成输入提取和新资产验证，之后才清理旧版。原上游 APK 的整包摘要校验模式仍供历史取证使用。

此策略依赖当前保留的正式版继续携带同一固定库；缺失或摘要不符必须停止，不能自动寻找新版上游 APK 或放宽校验。完整源码备份是 tracked tree，不含 ignored 二进制，不能承诺旧脚本或未来更换 native 后的所有历史版本永远能独立重建。

公开历史 `FongMi/media@9dae39e9689ee305c83f94bd11cf3bcecb9d6171` 曾包含一版 `libraries/exoplayer_libass/` 与 native 构建源码，但它与固定 `3c2c...` 是分叉历史，当前不能在没有 ABI 验证的情况下直接冒充 5.6.3 的可替代输入。后续清理这项构建债时，优先寻找与 5.6.3 公开源码/公开 media 可验证对应的来源；不得因为现有脚本“能构建”就继续把更高版本 Release 当长期依赖。

`libXray/**` generated bindings 与 `libgojni.so` 必须作为同一 JNI ABI 单元恢复；不能把官方旧 bindings 与黄金 API v2 JNI 单独拼接。当前 `scripts/build/build-published-libxray-aar.py` 从固定黄金 APK恢复匹配的 `libXray/**` bindings 与双 ABI JNI，同时保留官方 v26.7.28 AAR 中未经过 App R8 混淆的通用 `go/**` runtime。

最终 APK native 验证使用 ELF `PT_LOAD` runtime image，而不是 whole-file SHA：Android Gradle strip 可以改变 section metadata，但不能改变运行时 load segments。当前最终门槛核对 Xray、公开 FongMi/media 重建得到的 FFmpeg、MPEG-H 与 Libass 四类 native，并单独检查 merged Manifest：XrayService 必须 `exported=false` / `process=:xray`，同时拒绝 BootReceiver、`RECEIVE_BOOT_COMPLETED`、`REQUEST_INSTALL_PACKAGES` 与 VPN service permission 回流。普通 FongMi 权限不因为本 fork 的一般性安全偏好而额外改写；只有 Xray、TV 网络恢复或防止上游 APK 自更新覆盖 fork 所必需的 Manifest 差异可以长期保留。

current / publish workflow 按消费顺序清理构建临时文件：v7 native harness 验证通过后、准备 arm64 之前删除，arm64 验证后立即删除；Libass 开始前再回收已消费的黄金 APK、JADX 和 Xray bindings 重建目录。Libass 所需 player candidate、container、本项目正式 APK native 容器及已导入 AAR 保留到各自消费完成，剩余 Libass 临时文件在主 Gradle compile / assemble 前清理。不能把数 GiB 的两个 Android 原生测试环境一直保留到 Maven 测试之后。关键阶段记录 `du` / `df`，失败 artifact 包含实际 Surefire 报告。修改 compatibility 输入或 hash 时必须同步修改对应 verifier；不得重新加入任何高于公开源码的 Dolby/MPV/ISO Release-only restorer。

## 7. 构建

### GitHub Actions

仓库所有可执行 workflow 都必须保持**纯手动**。GitHub 官方 helper action 同时保持 Node 24 兼容 major（当前为 checkout v7、setup-java v6、setup-python v7、upload-artifact v7），避免 runner 强制兼容旧 Node 20 action 所产生的弃用告警：

```yaml
on:
  workflow_dispatch:
```

不保留 `push`、`pull_request`、`schedule`、`workflow_call` 等自动触发。当前三个手动入口分别为：`01-当前源码编译与APK验证.yml`（构建验证）、`02-正式APK构建与发布.yml`（正式发布）、`03-已验证APK发布续传.yml`（失败续发）。不再保留上游升级入口。

#### AI 协作执行准则

[AI_COLLABORATION.md](AI_COLLABORATION.md) 是当前 AI 协作规则的 canonical 文档；用户给出新的开发边界、Actions/AC、分支或交接要求时，应直接同步维护该文件。本文不重复维护其手动触发、轮询和交接细节。


当前工程主构建：

`.github/workflows/01-当前源码编译与APK验证.yml`

它负责：

1. 准备 JetBrains JDK 21 / Android SDK，并执行禁用自动下载的 `gradlew help`，实际启动上游要求的 Gradle daemon；预检在昂贵的 player/native 重建之前完成；
2. 先获取并验证本项目已发布 APK 内固定 Libass native，再从固定公开 FongMi/media commit 重建 18-AAR player candidate，并下载 / 校验其它 compatibility 与黄金 Xray 输入；
3. 直接导入固定公开 FongMi/media 重建出的 player candidate；黄金旧 APK只用于重建与 Go JNI 配套的 libXray Java bindings 与 Xray 动态 parity；
4. 重建并导入最小 Libass compatibility AAR；
5. 执行 current Java → 黄金 v7 / arm64 native 动态 Xray chain parity（统一以 v7 发布行为为黄金 oracle，包含 KCP golden cases 与发布版 `testXray` runtime validation）；
6. 只编译 Android TV / Leanback Java；
7. 只 assemble Android TV / Leanback 两个 ABI 的 Release APK；
8. 对最终 APK执行 Media3 DEX 类定义/引用闭合、MPEG-H class/native、Xray/FFmpeg/MPEG-H/Libass runtime PT_LOAD provenance 与 merged Manifest security contract；
9. 上传短期、固定签名的 TV release artifact（保留 2 天）供临时验证；上传成功后自动删除同名旧 release，只保留最新一份。失败报告只保留 1 天。历史 recovery 工作流入口已移除，底层取证脚本和 fixture 保留在 Git；长期可重建输入只保留源码 commit、脚本、fixture 与 hash，不再占用 Release。Gradle 命令继续使用 `--warning-mode all`；当前剩余会在 Gradle 10 失败的 deprecation 已确认全部来自固定上游同样使用的 Chaquopy Gradle plugin 17.0.0（multi-string dependency notation 与 execution-time `Task.project`），不是本仓库 Gradle 脚本。当前保持 FongMi/TV 5.6.3 的 17.0.0 pin，并让 `com.fongmi.chaquo.Platform` 继续跟随固定上游实现，不在本 fork 中为一般兼容或 warning 主动改写 Python ABI 选择逻辑。

正式发布器（文件名保留以兼容既有手动入口）：

`.github/workflows/02-正式APK构建与发布.yml`

Release 只保留 `v5.6.0-xray.5` 黄金参考和一个当前正式版，均只上传双 ABI APK。按用户最新要求，发布和续发都不再生成、上传或临时创建项目源码 ZIP、`source-backup-*` Release/tag；源码、签名及历史取证材料由私有 Git 仓库管理。

`test.7` 构建源码为 `439cea8d7a9d3cdb1a17b4ed962c6d68ed164508`，缺少后续 Hysteria2 备注查询边界修复；正式版替换旧测试发布。构建源码、资产 hash 与当前验收结果记录在对应 GitHub Release，历史 test.7 证据保留在本文维护记录，不能当作正式版的验证。

发布 workflow 以 `BUILD_SOURCE_SHA` 作为唯一构建与发布源码，重新准备固定依赖、执行源码 guard 与双 ABI 黄金 Xray chain parity，只编译/assemble Android TV / Leanback Release 两个 ABI，并核对最终 native provenance、Manifest、签名、应用版本、non-debuggable 与 16 KB alignment。正式发布标签不再写死为 5.6.3：工作流通过 `scripts/build/resolve-release-tag.py` 依据 checkout 后的 `app/build.gradle` 与 `scripts/build/source-baseline.json` 校验并生成 `RELEASE_TAG`。脚本**不自动递增版本**；同名替换仍必须由用户明确授权并显式选择 `replace_existing`。正常手动触发时 `BUILD_SOURCE_SHA = github.sha`，权限保持 `contents: write + actions: read`，同一发布流程使用 concurrency 排队而不取消正在进行的发布。

`scripts/build/publish-current-release.py` 只处理两份 APK 的草稿上传和正式切换，`tests/test-release-publication.py` 验证失败和清理顺序。先逐文件核对 name / digest / size 与来源 tag，验证通过后才进入切换。已有同名版本必须由用户明确要求并选中 `replace_existing`；旧 APK 暂存为 rollback 草稿，直到新正式 APK、Git ref 和 latest 全部核验后才清理。失败时保留可诊断/恢复的草稿，不把失败说成替换成功。显式选择 `prune_superseded` 时，验证成功后再删除黄金版与当前正式版之外的 Release/tag。

GitHub 的按 tag 获取已发布 Release 接口不会返回草稿；草稿创建和旧版转 rollback 后，必须使用已知 Release ID 校验状态、tag 和全部资产。存在性检查同时包含分页草稿列表；最终正式发布仍检查公开 tag、Git ref、资产摘要及 latest，不能因草稿查询 404 就放松校验。测试替身必须保留“draft 按 tag 查询为 404、按 ID 可读”的真实区别。

仅发布阶段失败时，可用纯手动 `03-已验证APK发布续传.yml` 或在具备对应仓库权限的环境执行同一续发工具，续发原 Actions 已验证 APK，避免重复编译。续发先验证原 run 的仓库、workflow、触发方式、源码及全部构建/验收步骤，再读取该 run 的失败报告，通过明确草稿 ID 下载原资产并重验摘要、签名、Media3 DEX 类链接、Manifest 和内嵌源码；发布来源继续记录原 APK 的构建 SHA。当前运行代码必须与原构建一致，不能将较新发布工具的提交冒称 APK 来源。原 run、报告或资产不满足条件就停止。

2026-10-26 的完整构建通过，但发布与首次续发因 Actions `GITHUB_TOKEN` 创建 rollback tag、移动正式 tag 返回 HTTP 403 而失败，已经上传的新 APK 无需因此重编译。遇到该权限错误，使用已授权且实际能操作目标仓库 Git ref 的凭据处理精确标签；发布器仅在目标 ref 已准确指向原验证源码时跳过冗余 PATCH。所有验证门槛继续保留。删除标签返回 403 时，结果记录 `pending_tag_cleanup` / `complete_pending_tag_cleanup`，必须完成对应清理并复核远端标签集合后才能声称全部完成；不得把 Release 已删除等同于 tag 已删除。

切换后期失败没有自动回滚，正式入口可能暂时缺失；此时先读取失败 artifact 内 `publication-before.json` / `publication-result.json`，核对正式 tag、rollback 草稿和新草稿，再恢复入口或继续切换，不能直接复用已占用的 rollback tag 盲目重跑。需要时可通过 `rollback_tag` 手动输入一个预先指向旧 APK 源码的 tag，避免 runner token 为旧提交创建 tag 的权限限制；成功后该临时 tag 自动清理。

### 固定签名与 Release 构建校验

版本命名、修订号递增、versionCode 公式和覆盖升级约定以 [PROJECT.md](PROJECT.md#版本命名与覆盖升级) 为准；后续 AI 的强制发布要求见 [AI_COLLABORATION.md](AI_COLLABORATION.md#11-ai-开发与发布的版本约束)。本节维护签名恢复、构建配置与产物验证方法。

- 新固定签名为 RSA-4096 / SHA256withRSA，有效期 100 年，自此用于本地与手动 workflow 的正常发布。PKCS12 文件 `signing/fingmi-xray-release.p12`、恢复配置 `signing/release-signing.properties` 和证书 fingerprint 文件按用户授权存入**私有仓库**；配置包含密钥密码，不能输出到日志或复制到公开项目。源码备份也包含它们，应同时保存到用户离线备份。
- `app/build.gradle` 直接读取此固定配置，Debug 也复用同一签名；缺少文件时构建失败，不回退到临时开发证书。两个 current-main workflow 不再生成签名，正式包使用 Release variant。历史 `recovery-*.yml` 工作流已删除，相关取证脚本与证据仍保留在仓库中，不属于当前正式发布入口。
- 当前 GitHub 连接无 Actions Secrets 管理权限，因此本轮采用用户授权的私有仓库恢复配置。签名证书 SHA-256：`3cd86f4fdf6044e7e60307624bf0d8c892dfd83b81ce21748504fcbba28763c2`，见 `signing/release-certificate.sha256`；每次发布用 `scripts/build/check-release-signing.py` 核对，不得重新生成或覆盖此 key。
- 旧签名遗失，无法用新 key 覆盖黄金版或过去临时签名测试包；首次需备份配置并卸载旧安装。同一包名 `com.fongmi.android.tv`、同签名、递增 versionCode 是后续覆盖升级的必要条件；本轮没有电视安装实测。armeabi-v7a 和 arm64-v8a 使用同一证书和 versionCode，选择设备匹配的 ABI。

本地构建与校验：

```bash
python3 scripts/build/check-release-signing.py
bash gradlew :xray:testDebugUnitTest :tv-recovery:testDebugUnitTest :app:assembleLeanbackRelease --no-daemon
python3 scripts/build/check-final-apk-native.py --apk-dir app/build/outputs/apk/leanback --build-type release
python3 scripts/build/check-release-signing.py --sdk "$ANDROID_HOME" --apk app/build/outputs/apk/leanback/release/leanback-armeabi_v7a.apk
python3 scripts/build/check-release-signing.py --sdk "$ANDROID_HOME" --apk app/build/outputs/apk/leanback/release/leanback-arm64_v8a.apk
```

Release 文件名沿用上游 finalizer 的 `leanback-armeabi_v7a.apk` / `leanback-arm64_v8a.apk`，对外资产命名为 `FongMi-Xray-TV-<Release tag>-<ABI>.apk`，其中 tag 必须与本次应用 `versionName` 一致。设备 ART/真实节点/电视待机仍属于真机验收，不因 GitHub 标记为正式版而自动视为通过。

当前 build 与 publish workflow 都必须先执行：

- `tests/test-xray-android-runtime-compat.py`：防止 Java 21 可编译、但旧 Android ART 运行时不存在的 API 再进入 `:xray`，并防止 `main` 构建重新退回“官方旧 Java bindings + 单独替换发布版 Go JNI”的不匹配组合；
- `tests/test-xray-core-parity.py`：守住配置生成、存储 / TOFU、Service 重试清理、Settings 核心语义、手机导入的 EventBus / operation 中断边界与发布版错误去敏链，并要求 current public destination guard 除已登记的 DNS 根点本地目标修复外，与发布 `qz3` readable mirror 保持逐行为等价；同时调用 `tests/test-xray-service-execution.py`，编译执行真实 Service、generation gate 与错误去敏类，验证启动/停止、准备期间替换/取消、回调失败后的清理、仍运行的 native Core 防护与取消后禁止信任写入。Android、native、配置构建及 pin 存储为确定性边界替身，实际 native 配置另由双 ABI chain 验证；
- `tests/test-xray-playback-parity.py`：守住 VOD / Live、播放器代理切换、媒体旁路、本地 scheme、artwork/logo 与资源释放语义，并调用 `tests/test-xray-side-request-lifecycle.py`，编译真实弹幕/字幕 API 与上游 `ApiCallback`，验证 HTTP / 下载完成后排队回调的 Xray 取消、owner 关闭、replacement 与 reentrant 边界；`tests/test-xray-danmaku-client-binding.py` 另执行真实页面初始化/选择方法，覆盖服务尚未绑定、直连、代理与断开后的 client 选择，避免只检查代理已经就绪的路径；
- `tests/test-xray-playback-address-parity.py`：把 public HTTP(S)/RTSP/RTSPT、私网/保留目标、Unicode whitespace，以及 Live pending `.strm` / YouTube indirection 边界与冻结发布证据做 differential parity；
- `tests/test-xray-playback-binding-handoff.py`：由 playback parity 调用，执行真实 Activity / Service 绑定方法与 `XrayPlaybackSession`，覆盖新旧播放页交接、相同媒体 key、旧页迟到关闭、重复认领、Live pending 及默认 Mobile/PiP 行为；平台、播放器与远端服务为明确替身；
- `tests/test-xray-artwork-lifecycle.py`：从 Gradle 当前应用 runtime 提取真实 Glide / AndroidX，执行两个宿主的实际清理与销毁方法；API 28/35 共 12 项验证 Activity-owned target 取消、重复清理、退出/销毁后的请求抑制与代理卸载。Android 使用 Robolectric，播放器和会话边界是交互计数替身，不代替完整电视播放验收；
- `tests/test-xray-session-races.py`：锁住发布版 STOP / timeout / callback 的竞态顺序；
- `tests/test-xray-service-client-lifecycle.py`：直接编译真实 Service client，锁住 bind timeout、cancel/unbind、Binder death 与 stale callback / connection generation；
- `tests/test-xray-normalizer-parity.py`：把当前 share-link normalizer 与 display helper 对发布版 readable reference 做纯 JVM differential parity；
- `tests/test-xray-transport-security-parity.py`：把 TLS / HY2 TOFU identity、首次信任、证书变化拒绝、已有 pin 与大小写/migration 边界对发布 reference 做 differential parity；
- `tests/test-upstream-update-disabled.py`：防止 FongMi 上游自更新入口、直接 release endpoint 调用或 APK 安装权限重新进入当前 fork；
- `scripts/build/check-elf-runtime.py --self-test`、`check-final-apk-native.py --self-test`、`check-final-apk-manifest.py --self-test`：先验证最终 ELF/Manifest gate 自身的判定逻辑；
- `tests/test-build-hygiene.py`：防止错误 XLIFF namespace、非 positional 多参数 string、FongMi/Chaquopy 上游边界再次被 fork-only 改写、Release-only media restore 回流，以及仍基于 Node 20 的旧 Actions major 再进入构建；
- `tests/test-tv-network-recovery.py`：锁住正式 `gn3` 的前后台 / SCREEN generation 来源，并用纯 JVM harness 验证 recovery 顺序、连续稳定检查、DoH resolver snapshot 与跨 generation 串行清理。

`tests/` 是 `main` 的统一回归入口，不再另维护目录 README。除上述 workflow guard 外：

- build/publish 的 Gradle 编译步骤必须同时执行 `:xray:testDebugUnitTest` 与 `:tv-recovery:testDebugUnitTest`；另有独立的 `:catvod:testDebugUnitTest` 步骤验证用户批准的主机名修复及既有代理规则。`test-build-hygiene.py` 检查三个入口不可被遗漏，发布续发工具也要求真实 Glide 和代理回归步骤成功。Python source/JVM guards 与 Gradle 模块 JUnit 是不同验证层，不能互相替代；workflow 仍只允许手动触发。

- `tests/test-current-native-share-chain.py` + `tests/xray-current-chain/`：执行 current Java normalize/security/config 链，并分别调用固定 v7 / arm64 发布 `libgojni.so`，对 26 组 conversion/runtime oracle 与发布版 `testXray` 做动态 parity；其中 6 组覆盖 KCP golden cases。
- `tests/test-xray-tls-fragment.py --workdir build/work/xray-tls-fragment`：执行真实 Java config/bridge，验证默认关闭保持原配置、TCP/TLS 适用范围、HTTP/3 跳过、mask 顺序/去重，以及测试副本与播放配置一致性；复用固定摘要的 org.json，native I/O 为替身，不能代替原生分片实测。两个手动 build/publish workflow 均运行此项。
- `tests/xray-session/`：Android / Binder / Handler 等 deterministic test doubles，只替代平台边界，真实编译 session / settings controller。
- recovery 专用 fixture 继续留在 `recovery/*-tests/`；只有 current workflow 显式调用的冻结 oracle 才进入 current 验收链。

### 应用内更新策略

FingMi-Xray 当前**不使用 FongMi/Release 的应用内自更新**。原因是上游 APK 会覆盖当前带 Xray 模块和兼容层的构建。

当前约束：

- Home 不做自动更新检查；
- 设置页版本号只用于显示，不触发更新；Leanback 版本行保持不可聚焦的纯信息状态；
- `Updater` 保留为 no-op 兼容壳，防止以后合并上游时旧调用点直接恢复下载逻辑；
- Manifest 不申请 `REQUEST_INSTALL_PACKAGES`；
- 测试包 / 正式包只通过本仓库明确发布并由用户主动安装。

现存四个入口为 `01-当前源码编译与APK验证.yml`（构建验证）、`02-正式APK构建与发布.yml`（正式发布）、`03-已验证APK发布续传.yml`（原产物复验续发）、`04-上游一键升级.yml`（上游升级），全部仅通过 `workflow_dispatch` 手动触发。五个历史 `recovery-*` 工作流已删除，其取证源码、脚本和 fixture 仍保留；详见 [RECOVERY.md](RECOVERY.md#9-归档-faithful-构建工具非-main-构建链)。

### 本地

编译、测试或 assemble 前，需要先准备 `app/libs` 与 `libxray/libs/libXray.aar` 所需的固定依赖。最完整的依赖准备顺序以 `01-当前源码编译与APK验证.yml` 为准。仅执行 `help` 的 daemon 预检不依赖这些生成 AAR。

完成依赖准备后，主要验证命令为：

```bash
bash gradlew --no-daemon :xray:testDebugUnitTest :tv-recovery:testDebugUnitTest :app:compileLeanbackDebugJavaWithJavac
bash gradlew --no-daemon :app:assembleLeanbackDebug
```

集中复查时，除上述源码/JVM入口和双 ABI native chain 外，应核对 Gradle XML 中实际执行的 tests/failures/errors/skipped。需要确认重新执行而非 `UP-TO-DATE` / `FROM-CACHE` 时，在对应 task 后加 `--rerun`；不要为普通文档调整重复构建。可用 `--offline` 复用已经校验的本地依赖。

云端受限文件系统中，Java 用户目录与 Maven/Gradle 缓存必须使用可写路径；Robolectric 会在 Java `user.home` 写下载锁，不能只设置 Maven local repository。当前云端以 `-Duser.home=/workspace` 和 `/workspace/.m2/repository` 完成测试；Gradle 自动下载的 JetBrains JDK 需通过 `-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts` 信任环境系统 CA。代理沿用环境提供的配置，不关闭 TLS 验证。播放器公开源码构建还会安装 NDK `29.0.14206865` 与 `28.2.13676358`。wrapper 未带执行位时可使用 `bash gradlew`。 `check-final-apk-manifest.py` 读取 apkanalyzer 的合并输出，因此检查时需将 Java 参数传给 `JAVA_OPTS` 并移除该子进程的 `JAVA_TOOL_OPTIONS`，避免 JVM 的 “Picked up” 提示混入 XML；参数不变、TLS 验证仍开启。

## 8. 固定 FongMi/TV 5.6.3 维护基线

本仓库只维护 `main`，采用固定 FongMi/TV 5.6.3 源码（`c616c0aa3613e87529791587a9f71b78c278c991`）与对应公开 FongMi/media 固定提交。普通业务、UI、播放器默认不主动跟随上游更新。

原有 `04-上游一键升级.yml` 和 `scripts/upstream/` 的升级生成、适配、实验测试均已退出日常维护。发布版本校验所需的不可变基线单独保留在 `scripts/build/source-baseline.json`。现行构建继续使用固定 18-AAR 播放器、Libass/native 校验、黄金 Xray 依赖恢复与三个手动工作流。

本次从旧实验分支只挑选 Xray 会话/网络边界、远程封面生命周期以及 TV 恢复协调的修复和对应测试；不合并新版 Media3、Libass 或 FFmpeg 实验。离线 JVM/源码回归与 Android 双 ABI APK 构建是不同证据等级，不能互相替代。

## 9. 验证清单

当前验收对象是**当前 `main` 架构 + `v5.6.0-xray.5` v7 的 Xray 外部行为语义**。正常发布不要求重建完整 5.6.0 faithful APK，但凡修改 Xray / 播放代理 / Service 生命周期，必须继续用冻结发布证据、source guards 或动态 native parity 证明没有偏离黄金参考。历史 recovery workflow 已从当前仓库删除；如需恢复历史二进制取证入口，先按 [RECOVERY.md 第 9 节](RECOVERY.md#9-归档-faithful-构建工具非-main-构建链) 核对脚本、输入和 Git 历史，不把旧工作流当作当前验证入口。

影响 Xray / 播放器 / 网络生命周期的修改，至少考虑以下场景：

### Xray 基础

- Android 12 / SDK 32 等旧 ART 上的节点保存、删除、测试；
- v7 / arm64 测试包的 Service bind、Java → libXray invoke 与错误返回；
- 手机导入；
- VOD 开启 / 关闭；
- Live 开启 / 关闭；
- Xray 启动失败后的直连恢复；
- Service disconnect / Binder death / stale callback。

### 播放身份

- 切集与自动下一集；
- 切频道；
- 换线路 / 换源；
- 同一播放身份内实际 URL / CDN / parser 结果变化时 **不** 重置 Xray；切换到新的逻辑播放身份时默认重置，连续命中电视直播自动规则时仅保留 transport 并推进 identity；
- 换播放器；
- Activity 退出 / 销毁。

### 媒体网络

- HTTP / HTTPS；
- DRM；
- RTSP / RTSPT；
- subtitle / danmaku；
- EPG / XML metadata；
- artwork / logo；
- preload / cache 边界。

### 播放器兼容

- Libass primary / secondary subtitle；
- Matroska ASS attachment；
- EGL / GLES 渲染生命周期；
- MPV secondary subtitle / font；
- Exo / MPV 切换。

### TV 生命周期

- 长后台恢复；
- SCREEN_OFF / SCREEN_ON；
- Fast Start / 待机恢复；
- DNS / DoH 重建；
- Spider 重建；
- DLNA renderer 生命周期。

静态比较、单元/JVM 测试、发布 native 动态 parity、Gradle 编译、APK assemble、模拟器与 Android TV 真机运行是不同层级的证据，提交说明和文档必须准确写明实际验证到了哪一层。AI 协作时的文档更新与记录边界见 [AI_COLLABORATION.md](AI_COLLABORATION.md)。

## 10. 精选维护记录（历史快照）

以下是按当时阶段记录的**已完成验证、真实根因与有意决策**，不是当前版本状态清单。旧 Release、构建候选、AC 成败与当时未完成事项均以原日期解释，不能替代第 1–9 节的现行事实；原始过程仍可从 Git 历史和对应 Actions 记录追溯。

### 10.1 长期有用的维护线索

| 关注点 | 关键历史节点 | 当前应查阅的位置 |
| --- | --- | --- |
| Xray Java/JNI 必须成套、黄金行为与安全边界 | 9/27、10/2–10/3 | 第 3、6、9 节；[RECOVERY.md](RECOVERY.md) |
| TV 恢复模块化、DoH 与 Spider/Glide generation | 10/2–10/11 | 第 4 节与对应 JVM 回归 |
| HY2 备注、IPv6 媒体 URL、媒体旁路排队回调 | 10/4–10/8 | 第 3、9 节与对应 source/JVM/native guard |
| Media3 decoder 缺失、Glide 生命周期、主机名崩溃 | 10/11 | 第 5、9 节与本节对应故障记录 |
| 固定签名、发布续发、一次性同名替换 | 10/5–10/26 | 第 7 节与 [PROJECT 版本规则](PROJECT.md#版本命名与覆盖升级) |
| 5.8.7 升级阻断与一键升级工具 | 11/2–11/3 | 第 11、12 节 |

### 10.2 按日期保存的维护记录



本节只保留会长期影响后续开发判断的迁移决策和故障结论；普通 commit、run、临时 trigger 与一次性排障过程由 Git / Actions 保存，不在文档重复记录。

#### 2026-09-27 — libXray Java/native ABI 必须成套

曾验证“官方 v26.7.28 Java bindings + 历史 API v2 `libgojni.so`”会在 JNI 初始化阶段因模型类不匹配导致 `:xray` 进程失败。因此当前构建从黄金发布 APK恢复与发布 JNI 配套的 `libXray/**` generated bindings 和双 ABI JNI，同时保留官方 AAR 的通用 `go/**` runtime。后续升级必须把 generated Java bindings 与 JNI 当成同一 ABI 单元处理。

#### 2026-09-28 — TV-only 与 v7 Xray 黄金参考

项目只交付 Android TV / Leanback，输出 armeabi-v7a 与 arm64-v8a；Mobile 不是本 fork 的 Xray 验收目标。当前模块化架构不要求恢复旧版混合源码结构，但 Xray 的 normalize / display、VALIDATE / TEST / START / STOP、Binder generation / timeout、播放代理、旁路请求、失败恢复和资源释放等外部行为以 `v5.6.0-xray.5` v7 为黄金参考。

#### 2026-09-29 — full-JADX 扩大外围审计边界

筛选后的 readable JADX 不是完整调用图。后续 Xray 审计必须从旧 PlayerManager / Service / security helper 反向枚举 caller，覆盖字幕、弹幕、EPG/XML、DRM、RTSP、artwork/logo、MediaSession、preload、外部播放器与手机导入等“类名本身不含 Xray”的路径。该原则已由 core/playback parity guards 固化。

同阶段 TV 网络恢复补齐普通 API client 与 playback client 隔离、Glide 动态取得新 API client、图片失败缓存复位、generation 串行恢复以及 stale task/callback 拒绝；Manifest 不再用 BootReceiver 形成第二条恢复入口。

#### 2026-09-30 — 媒体边界回到公开上游

播放器与普通业务重新明确只以公开 FongMi/TV + 固定公开 FongMi/media 为主体。任何只存在于高于公开源码的 Release / APK 中、但未公开的 Dolby、MPV bridge、remote ISO、native UDF / disc navigation 等都不属于本 fork 的恢复目标。保留的媒体差异只允许是当前公开源码可构建所需的最小 compatibility adapter；Libass native 的非源码来源另见下方“构建债”说明。

最终 APK 验收同时提升为硬门槛：Xray、FFmpeg、MPEG-H、Libass 的 runtime PT_LOAD provenance 与 merged Manifest security contract 必须在 assemble 后直接验证，不能只检查构建输入。

#### 2026-10-01 — 以上游完整树重新建立基线

为清除旧 `main` 中多轮维护留下的不可追溯差异，重新以 `FongMi/TV@c616c0aa3613e87529791587a9f71b78c278c991` 完整树为基线，再只应用 Xray、Android TV 网络恢复、禁用上游 APK 自更新、构建/测试基础设施及不可避免的 compatibility 差异。无法归类的普通业务差异一律恢复上游。

#### 2026-10-02 — DoH race 收口并统一回 `main`

TV 待机网络审计发现 `OkDns.lookup()` 在 reset/rebuild 并发时存在离锁后重复读取 volatile `doh` 的 TOCTOU 窗口。当前实现改为在同步边界内快照本次 lookup 使用的 `Dns resolver`，再在锁外执行实际 DNS 请求，并由 `tests/test-tv-network-recovery.py` 锁定该约束。

完成源码、Xray/TV 网络、上游差异与最终构建验证后，干净重建结果成为唯一 `main` 基线。该运行代码基线已通过自动源码/native/assemble/Manifest 门槛；此后 fresh 黄金网络恢复对比只新增了 Spider cleanup 异常隔离修正，当前 HEAD 尚未为这一小修重复跑完整构建。尚未发布新的测试 Release，Android TV 真机 Xray 与待机/长后台网络恢复仍是下一层验收。

随后以当前 `main` 代码反向核对长期文档，确认全部上游同路径差异仍只落在 Xray、TV 网络恢复、禁用上游自更新、构建/测试基础设施与最小 compatibility 范围；同时修正文档中对 Xray 本地 DataSource scheme 的错误描述，并补齐 Core DNS/私网保护、Exo-only proxy 注入、Home-owned 网络恢复与实际 CI guard 清单。

#### 2026-10-02 — 黄金 TV 网络恢复 fresh 对比与 Spider cleanup 修正

同一份 fresh v7 full-JADX 重新核对 `gn3`、Home 恢复逻辑、`l61`、`ha2`、`la2`、Glide 与 Spider clear。generation 来源、Home resume/focus 触发、普通 API client 与 player client 隔离、DNS/DoH 重建、异步 Spider clear、两次稳定 Internet 检查、约 500 ms 轮询与 DLNA 生命周期均与当前架构保持同一外部语义。

当前保留几项有证据支持的增强：Glide 不再永久固定旧 API client；网络恢复会清除瞬时图片失败集合；DoH lookup 在同步边界内快照 resolver；`recoveredGeneration` 使 Home 重建后只跳过真正完成过的 generation。fresh 对比同时发现 Jar/JS/Python loader 的 `forEach(Spider::destroy)` 不具备黄金版“单个 destroy 失败仍继续清理”的容错，已改为逐 Spider try/catch，并让 QuickJS module-cache clear 失败也不阻断状态清空。该修正不改变 recovery 顺序，只恢复黄金版清理失败隔离语义。

#### 2026-10-02 — fresh v7 full-JADX / DEX 独立 Xray 完整性复核

为避免把旧 recovery 结论当成前提再次自证，单独用固定 `v5.6.0-xray.5` APK 再跑一次完整 recovery analysis（run `36910320478`），取得 fresh v7 full-JADX 与双 ABI DEX/dexdump。审计从完整 APK 重新枚举 Xray direct classes、AIDL/Binder glue、Service/session/settings 状态机，并以旧 `PlayerManager(th2)` 的 current-client、Xray-active 与 proxy transition 方法反向穷举所有 caller，覆盖 DRM、RTSP、字幕、弹幕、EPG/XML、artwork/logo/MediaSession、preload、外部播放器和手机导入。

结果没有发现当前 `main` 尚未映射的 Xray runtime path；旧 AIDL 六个事务与当前 `validate/test/start/stop/resetSecurity/cancel` 一一对应，5s bind、1.5s cleanup、30s startup、45s settings timeout 也由 fresh JADX/DEX 重新确认。fresh v7 与仓库 selected reference 的 3 个差异仅是 TV 网络 helper 的格式整理，已恢复为 fresh 文本；此后 63 个 `shared/sources/` 文件与 fresh v7 blob 全部一致。运行代码没有因此修改。

该结论仍限定为**已取证行为/调用链完整映射**：旧 APK 的原始未混淆 Java 源码和 libXray 原始 Go 源码并未找回。native 继续使用正式 APK 固定 SHA 的 `libgojni.so` 与匹配 generated bindings，并由此前成功的双 ABI current-chain parity 验证；最终 Android TV 真机仍是更高层级验收。


#### 2026-10-03 — 第三轮只审 Xray / TV recovery 未发现新的确定 Bug

继续严格按长期维护边界只检查 Xray 与 Android TV 待机/长后台网络恢复，不扩查普通 FongMi 业务。第三轮刻意避开前两轮已反复覆盖的 START/STOP 主路径，重点复核 XrayPreferences / XrayCertificatePins 迁移、share-link normalizer、错误去敏、Binder client/Service cancel、SOCKS/RTSP socket、播放 identity、Live metadata client，以及 TvNetworkLifecycle、NetworkRecoveryCoordinator、API/DNS/DoH reset、proxy selector/auth、BaseLoader/Spider completion、Glide failure epoch 与 Home destroy/recreate。

本轮没有构造出新的确定 current-only Bug。证书 pin store 与 legacy mirror 的 prefs/字段/KeyStore alias/迁移逻辑一致；settings close/phone-import abandon 的“只 unbind、不 remote-cancel”也与冻结 legacy/DEX 行为一致，不擅自改动。VOD newIntent/换集/换源和 Live 切频道/切线路/catch-up 均确认经过 Xray identity reset；只有刚成功 START 后继续同一 pending Live channel 的恢复路径明确保留同 identity。BaseLoader.clear(after) 由 per-loader Throwable 隔离加外层 finally 保证 completion callback，不会因单个 Spider.destroy 失败永久卡住 recovery。

同时把纠偏前最终审计状态 `70b720bf...` 与 current 运行 blob 逐项反查：LiveActivity、VideoActivity、SettingActivity、ImgUtil、XrayProxySocketFactory、XrayShareLinkSecurity、XrayGenerationGate、XrayService、XrayPlaybackSession、XrayServiceClient、XraySessionController、XraySettingsController 均逐 blob 一致；唯一 XrayConfigFactory 差异就是已经由真实双 ABI `testXray` 证明不兼容、并从 current 淘汰的 `::ffff:0:0/96` runtime 增强。没有发现漏重放的其它有效 Xray/TV-recovery 修复。

仍保留两项只作为观察风险而不修改：黄金 TV recovery 的约 6 秒稳定性轮询上限，以及不主动退休 dedicated player client 的后台播放保留策略。二者都有黄金/现行边界依据，目前缺少真机或更强证据证明是 current Bug；不得仅凭理论推演再次扩张 recovery 状态机。

#### 2026-10-03 — 第二轮审计纠正 Xray close 误报

第二轮只读反查重新沿真实同步调用顺序核对 `XrayPlaybackSession.close()`，确认上一轮把 owner 销毁误判成资源泄漏。实际顺序是 `close() -> end() -> stop(false) -> XraySessionController.stopSession()`；`stopSession()` 在提交 Binder STOP 后会**立即同步** `notifyState(IDLE)`，而此时 `XrayPlaybackSession.closed` 尚未置位，所以既有 `onXrayStateChanged(IDLE)` 已经同步执行 `clearResources(false)` 并关闭 `XrayHttpClient`。如果 controller 原本已是 IDLE，`XrayPlaybackSession.stop(false)` 本身也会直接清理 resources。因此 published/test.6 的原实现没有这条泄漏。

为保持纯净基线，上一轮追加到 `XrayPlaybackSession.close()` 的重复 cleanup 与对应 parity guard 已全部撤回，运行代码重新回到已发布验证状态。该纠错再次确认：后续 Xray/TV-recovery 修复必须沿完整同步/异步调用链证明问题，不能只看最终 callback 分支推断资源泄漏。

同轮继续复查 TV recovery generation / DNS-DoH reset / Spider clear / Glide epoch / Home stability poll。黄金 `l61` 本身在约 6 秒稳定性轮询上限后会结束该 generation，即使 INTERNET capability 尚未连续稳定两次；这仍保留为黄金行为/真机风险观察项，没有凭静态推演扩张 recovery 状态机。

#### 2026-10-03 — 纯净基线发布验证通过并替换测试 Release

修正 native 未接受的 mapped-IPv6 runtime 增强后，重新触发 publish run `37100464365`，build source 为 `1b7976f7ddd742e65392819c4cd5013407e23545`。该 run 全部步骤通过：fork source guards、Android SDK 36/37、固定 player/native 输入重建、双 ABI 黄金 Xray native/runtime parity、reconstructed Libass candidate、Leanback compile、双 ABI assemble、MPEG-H/native provenance、最终 Manifest security contract 与 Release 发布均为 success。

发布结果为 `v5.6.3-xray.test.6` pre-release，tag target 精确指向上述 build source；资产仅有两个 Android TV APK：
- armeabi-v7a：`sha256:af4e725c59a9b92e49ce1c4391219c788c3c2d67f37e958881d70ae0cd121f39`
- arm64-v8a：`sha256:2d482e2d71de00ae7bd75186a80387acc6a2a5896a7db8a2e4453eb1a9c59168`

发布成功后已先恢复 publish workflow 为 `workflow_dispatch` only，再删除临时 marker，避免清理提交再次触发 Actions。随后只同步 README/DEVELOPMENT 文档，没有修改运行代码。当前 Release 集合只保留黄金 `v5.6.0-xray.5`、当前测试 `v5.6.3-xray.test.6` 与一份用户明确要求的最新 `source-backup-*` 源码备份；旧测试/临时发布不长期保留。自动构建已验证，但 Android TV 真机 Xray 与待机/长后台恢复仍需实际设备验收。

#### 2026-10-03 — 发布 native parity 淘汰未验证 mapped-IPv6 runtime 增强

发布 run `37097786995` 在 source guards、Android SDK 准备、player/native 输入重建和 libXray AAR 准备均通过后，首次在真实黄金 `libgojni.so -> testXray` runtime validation 阶段失败；第一条 `vless-kcp-srtp-seed` 即返回与冻结 v7 oracle 不同的 response。该 case 只是 26 条 runtime validation 的第一条，current 与黄金 runtime request 唯一被测试归一化允许的结构差异是此前静态审计加入的 `::ffff:0:0/96` reserved prefix，因此这次 native 证据证明该“IPv4-mapped IPv6 私网防护”并未满足实际 Core 配置合同。

按纯净基线原则，current 已删除这条未经过 native 验证的 runtime 增强，同时移除 parity 中为它设置的特例，恢复对黄金 runtime JSON 的**完全一致比较**。黄金已有的 `::ffff:0:0:0/96` 保持不变；如未来仍要补 mapped-IPv6 安全缺口，必须先证明候选配置能被固定双 ABI `testXray` 接受，不能再仅凭静态 CIDR 推理提交。

#### 2026-10-03 — 全量文档与冻结发布说明反查

重新检查仓库 7 份 Markdown（6 份项目文档 + `LICENSE.md`），并完整读取冻结的 `ORIGINAL_README.md` 后，以其用户级产品合同反查 current 源码与长期文档。确认 no-VPN、当前播放会话手动启用、VOD/Live identity 边界、节点测试/手机导入、独立 `:xray` 进程、资源释放与 TV 长后台网络恢复仍有 current 实现；v2rayN 标准单节点重新明确为主要分享链接兼容/测试目标。

同时修正文档自身漂移：只有 `ORIGINAL_README.md` 冻结，`AI_COLLABORATION.md` 必须随用户开发限制更新；**该次审计当时** Releases 尚无 `v5.6.3-xray.test.6`，只有黄金版与用户要求的 source-backup；README 的 CI SDK 列表同步为 workflow 实际安装的 Android 36 + 37.0 / Build Tools 36.0.0 + 37.0.0。RECOVERY 另修正黄金 STOP/callback 竞态的前后矛盾，并明确冻结 README 的“换地址/后台状态”是用户级概括，DEX/JADX 证据对 logical identity / resolved URL / 后台保留播放给出更精确语义。

#### 2026-10-03 — 纠正 5.6.8 文档与构建边界

再次检查全部长期 docs 后确认，公开上游仍严格是 FongMi/TV 5.6.3（`c616c0aa...`）；Release/APK 的更高版本号不得被写成 current 上游或功能目标。README、PROJECT、RECOVERY 当前没有 5.6.8 基线表述；AI 协作规则与 DEVELOPMENT 已把一般性的高版本 Release 叙述改成“高于公开源码的 Release-only”。

同时确认这不是纯文档问题：current/publish workflow 仍下载 FongMi Release 5.6.8 Leanback APK，只为 Libass compatibility 提取 `libmedia3ass.so`。该路径现明确登记为**待移除构建技术债**，不是允许继续维护的第三项能力，也不能用来恢复 5.6.8 的 Dolby/MPV/ISO 等行为。当前业务源码仍只维护 Xray 与 TV recovery，但在这项 Libass 二进制输入清理完成前，不再把仓库描述成“所有构建输入也严格只来自公开 5.6.3”。

#### 2026-10-03 — 回到 source-backup 后只重放 Xray / TV recovery 已确认修复

按用户要求，`main` 先强制恢复到源码备份 tag `source-backup-2026-10-02-main-6a4117c8` 对应的 exact commit `6a4117c8d52a37af117daf6c716969293400bb87`，再重新审计该点之后 274 个提交及其最终净差异。此前由静态竞态推演扩散出的 Config replay/task owner、BaseLoader barrier/Spider lease、deferred Cast/BOOT/navigation、Setting/Live recovery UI 等实验链没有重新带回；普通 FongMi Config/UI/业务源码继续以 source-backup/固定公开上游为准。

重新提交的运行代码只保留两类：

- **Xray**：VOD new-intent identity/ready-state 边界；Live XML/EPG 在 proxy install、手动关闭与 ERROR rollback 时的播放网络身份重新接管；native cleanup、Binder bind/asInterface/link/unlink/unbind/cancel/callback 的 Runtime/Linkage failure 收口；本地 proxy 安装/卸载失败后的资源与 Core 回滚；replacement START / bind-pending / failure callback 的 reentrant owner 竞态；Settings result/timeout/delete/reset 的 owner、partial-delete 与 listener 隔离；首次 TOFU pin 只在拥有该 operation/session 的成功路径提交；RTSP SOCKS connect/bind 失败时关闭新建 socket。
- **Android TV 网络恢复**：保持 source-backup 的 generation → 普通 API/DNS/DoH reset → async Spider clear → stable network → Home refresh 小边界，仅补 `ImgUtil.networkFailureEpoch`，使退休网络代际晚到的 Glide `onLoadFailed()` 不再重新污染新 generation 的图片失败集合或覆盖恢复后的图片状态。

与上述修复直接对应的 current-native/share、core/playback、ServiceClient、session/settings、transport-security 与 TV recovery source/JVM guards 一并重放。TV recovery guard 额外锁定普通 `KeepActivity/SiteApi/BaseConfig/VodConfig/LiveConfig/WallConfig/LiveParser/ConfigEvent/Notify` 必须保持固定上游 Git blob，防止后续再把恢复状态机扩散进普通业务层。

这次重放完成时尚未触发 GitHub Actions/AC，也没有把旧 run 冒充为新 HEAD 验证。source-backup 之前已有的构建/native/Manifest 证据仍只证明当时对应代码；该状态随后由 2026-10-03 的 publish run `37100464365` 完成自动验证，见后续记录。

#### 2026-10-04 — 用户分享链接核验与 Xray 旁路排队回调修正

重新对照公开 `FongMi/TV@c616c0aa3613e87529791587a9f71b78c278c991`（5.6.3）完整树核查差异，恢复两处不需要改变普通上游行为的细节：`ViewModelTaskRunner.cancelAll()` 回到上游仅取消并清空 futures 的实现，保留 Xray/TV recovery 所需的定向 `cancel(type)`；`ChannelAdapter.onViewRecycled()` 回到上游实现，Xray logo 抑制继续只由专用状态及绑定路径负责。没有用高于公开源码的 APK 恢复上游功能；既有 5.6.8 Libass native 输入债仍按前述边界保留，尚未移除。

用户提供的六条单节点链接（HY2 IPv6 + mport、域名 Reality XHTTP packet-up、IPv4 Reality gRPC gun、VMess KCP、VLESS / Trojan WS TLS）与五组 IPv6/域名端点变体，均用当前真实 Java normalize/security/config 链和冻结 legacy reference 完成完全一致比较，再用 SHA 固定的黄金 v7 `libgojni.so` 执行真实转换及 `testXray` 配置校验。额外逐字段核对 server address/port、SNI、Reality 参数、Host/path、gRPC authority/serviceName、KCP seed 与 HY2 跳跃端口；没有把域名替换成导入时解析的 IP。既有 26 条 native/runtime oracle（含 6 条 KCP）也全部通过。原始用户凭据只用于工作区外临时测试，不写入源码、fixture 或文档。

固定公开 Xray Core 的 `recovery/node-dns-tests` 在本地合成 DNS/TCP/UDP 环境通过 9 个子场景：AAAA-only、双栈、IPv6 字面地址与 nil/AsIs dial 设置。该证据验证节点域名引导使用系统解析器、IPv6 字面地址不发起 DNS，且节点地址与 TLS SNI 分离；它不代表实际 Android 网络或用户节点一定可达。HY2 `insecure=1` 继续遵循黄金 TOFU 证书 pin 语义，本次配置测试使用合成证书探测结果，没有执行真实节点握手。

本轮复现一个 current Xray 集成缺陷：弹幕/字幕 HTTP 或下载完成后先清空 request owner，而 `ApiCallback.post()` 的 UI 结果尚未执行；此时开启 Xray，取消逻辑误判没有请求，旧网络结果仍会送达，搜索对话框的取消 completion 也被遗失。当前只把 owner/completion 的退休延后到 UI 结果实际执行完毕，HTTP/下载句柄仍及时清空；按 request id 收口，避免旧结果清理回调中创建的新请求。字幕 ZIP 解包后的排队交付同样受该 owner 保护，上游 `ApiCallback` 保持原样。

新增 `tests/test-xray-side-request-lifecycle.py` 用确定性 HTTP / Download / 主线程队列边界编译执行真实 API：修复前复现 stale callback，修复后 16 个场景通过，并已接入现有 playback parity guard，build/publish 无需新增 workflow 步骤即可运行。本轮本地 14 个标准验证入口均通过；证据限于源码/JVM、v7 native 配置校验与本地 Core DNS，不包含当前改动的 APK assemble、Android ART、真实播放或 TV 待机验收。未触发 GitHub Actions 或发布。

再次复核公开上游 HEAD 与当前声明版本，仍为上述 5.6.3 基线；普通 Config、Keep、SiteApi、LiveParser、Event/Notify 等源码保持上游 blob。沿弹幕/字幕调用方、Xray playback identity / START-STOP / proxy cleanup，以及 TV SCREEN/background generation → Home 串行恢复 → API/DNS/DoH reset → Spider cleanup → Glide epoch 重新检查，没有复现新的确定问题。约 6 秒网络稳定性轮询上限与后台保留 dedicated player client 继续作为已登记的真机观察项，不据静态推测扩张上游业务状态机。

#### 2026-10-04 — 公开上游完整差异与两项维护模块独立复核

独立对照固定 FongMi/TV 5.6.3 源码树：上游 1,120 个跟踪路径中有 1,061 个逐字节一致、57 个修改、2 个网站文件删除（不包括本 fork 新增文件）。逐项核对修改仅服务 Xray、TV 恢复、禁用上游自更新、构建基础设施及公开 Media3 兼容；固定公开 `MpvPlayer` 的缺失选轨/字幕接口说明最小兼容适配仍有必要。Libass 固定 native 构建债未消失。

复查 Xray 的 Service/绑定/设置/代理/媒体旁路及 TV 的 Home/DoH/Spider/Glide generation，纠正局部代码易产生的误报：显式 SOCKS 代理不会被 `ProxyRedirectInterceptor` 重选路覆盖；`close()` 先经同步 IDLE 卸载代理。四个针对性源码/JVM 回归入口通过，**没有确认新的确定性运行缺陷或修改运行代码**；没有新 AC、APK assemble 或真机验收。

#### 2026-10-04 — 独立恢复模块与集中 FongMi 接线

按用户要求进一步独立维护两项自有能力，新增 `:tv-recovery` Android library，将 `NetworkRecoveryCoordinator` 与 `TvNetworkLifecycle` 移入 `com.fingmi.tvrecovery`。恢复协调算法保持原样；lifecycle 中的 DLNA 服务调用替换为宿主提供的 `Renderer` 接口。模块只依赖 Android/annotation，不引用 FongMi、catvod、Xray 或应用适配类。既有 coordinator 单元测试随核心移入模块。

新增应用自有 `com.fingmi.integration.recovery.FongMiNetworkRecovery` 适配器，集中普通 API/DNS/Glide reset、Spider clear、系统网络能力判断、主线程调度、已恢复 generation 标记及 flavor DLNA 接线。Home 只提供页面取消、进度、存活判断、刷新回调，并保留原有 resume/focus/check/destroy 调用；普通 FongMi Config、SiteApi、播放器业务等没有随拆分重写。Xray 核心继续独立维护在既有 `:xray`，应用封面适配 `XrayArtworkBitmapLoader` 仅移动到 `com.fingmi.integration.xray`，行为未改。Xray 核心版本、JNI/bindings、转换/security/runtime 配置、固定 native 来源及 workflow 均未调整。

新增模块边界与实际适配器 JVM 验证，分别编译执行 Leanback/Mobile 接线；既有 14 个本地验证入口全部通过。实际执行 `:tv-recovery:assembleDebug :tv-recovery:testDebugUnitTest` 成功，独立 AAR 生成、Android Java 编译与两个迁移的 JUnit 测试通过。云端 Gradle 使用当前 session proxy 和系统 CA 信任，不为此修改上游 Gradle/toolchain 设置。本次没有构建完整应用 APK、触发 Actions、更新核心版本或发布 Release，Android 真机验收仍未完成。

后续上游同步应保留两个核心模块，先采用公开 FongMi 树，再核对应用自有适配层及页面/播放器所需接入点。核心独立不意味着零上游接线：网络资源、播放器与 UI 属于宿主，接口变化仍需适配与回归验证；不得因此接管普通上游业务或把网络恢复并入 Xray。

#### 2026-10-04 — 云端完整 TV APK 构建与模块拆分接线修正

用户明确要求本地编译并上传 Release。本次完整 Leanback javac 发现拆分恢复模块时误删了 HomeActivity 的 `ImgUtil` import，而上游 `ImgUtil.logo()` 调用仍保留；仅恢复该 import，不改变上游 logo 或恢复流程。此前核心/适配器 JVM 验证没有编译完整 HomeActivity，不能代替应用编译。固定 Media3 container AAR 加入构建产物忽略规则，二进制不提交 Git。发布 workflow 仍为纯手动，当前测试目标推进为 `v5.6.3-xray.test.7`。

固定公开 FongMi/media 17-AAR candidate 已在云端重建成功；Libass 的 10 个真实 Robolectric 测试通过，extractor SHA-256 `feb8be30e3d431391ce4b3b165a6cbfb18313969d7ba7da2d6ccfeb96d25ee68` 与 candidate SHA-256 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861` 均符合仓库固定值。最初 Robolectric 因只读用户目录失败，改用可写 Java user.home 后通过，没有为此更改上游源代码。既有 14 个 source guards 及 ARMv7/ARM64 各 26 个真实黄金 JNI 转换/runtime 用例均通过。Xray v26.7.28 与两 ABI 黄金原生库保持原样，FongMi 公开源码基线仍为 5.6.3。完整 Leanback javac 重编译与 APK assemble 均成功，APK build source 为 `631cbcf0948370bdbf8c4a337d44fbd979c68485`。

两个完整 APK 的最终 Xray / FFmpeg / MPEG-H / Libass ELF 运行段均匹配验证过的 AAR；双 ABI 单独打包，DEX 包含 Xray service、独立 recovery core 及 app adapter；Manifest、apksigner 与 16 KB page zipalign 校验通过。该源码重新跑完 14 个标准验证入口。本轮没有 Android ART 启动、真实节点握手、播放或 TV 待机验收。

| 本地完整测试 APK | SHA-256 |
| --- | --- |
| armeabi-v7a | `44385f3a3a7b62d0b894efa7020eb253de310d08b5eaa751523272764c20ffdd` |
| arm64-v8a | `5915528ac25ac4ee6f09391275868c119fd1d6123253970a01862b86292ae05e` |

两 APK 使用同一云端 Debug 测试证书 SHA-256 `0d71ccd96f6c91f8e3d1e9c9e7f37d5e1c3ce4b4bb407a0a7d85ade1475a6c2b`，与黄金版及 test.6 证书不同，不能覆盖安装；测试前需备份配置。该证书不等同历史正式发布签名。完整 APK 保存在本地 `app/build/outputs/apk/leanback/debug/`。

云端向 GitHub uploads endpoint 的直接发布失败：GitHub CLI、urllib 与 curl（HTTP/1.1、HTTP/2）均返回 HTTP 400 `Bad Content-Length`；1 KB 和更小的临时未发布探测也同样失败，未留下任何远端资产，不能归因于 APK 内容或文件大小。保持原测试 Release，清理本轮空草稿后，仅尝试一次已有纯手动 publisher 作为必要发布替代；该路径会重新构建，必须以它实际产出的 source / digest 为准，不能把上述本地 APK hash 当作 Actions 发布资产 hash。

#### 2026-10-04 — 再次逐项上游审查与 Hysteria2 备注边界修复

重新读取公开 FongMi/TV 默认分支 HEAD，仍为 `c616c0aa3613e87529791587a9f71b78c278c991`；其 `versionCode=563`、`versionName=5.6.3` 与当前应用一致。本次按 Git tracked tree/blob 对照审查起点 `439cea8d7a9d3cdb1a17b4ed962c6d68ed164508`，得到 1061 个同路径完全相同文件、57 个修改文件（其中 42 个 Java）、2 个删除文件和 376 个新增文件。删除项仍只有 Pages 自动部署 workflow 与网站目录 README。逐项读取现有差异，而非仅凭类名或上次记录认定它们属于接线。

本次没有发现需要进一步恢复的无关上游业务修复。播放器差异限定于 Xray client/DRM/RTSP 注入、身份变化时卸载代理、预加载与媒体旁路清理；普通 ViewModel 通用取消、频道回收、配置解析和数据库仍保持公开上游。字幕/MPV 差异另与固定公开 media 的真实 API 对照：该版本没有应用所需的 secondary-track selection/reset/suppression、独立副字幕样式及字体设置接口，保留现有最小兼容实现。禁用上游 APK 自更新属于防止 fork 被覆盖的既有基础设施。Libass 的 5.6.8 APK 固定原生库输入仍是未移除的构建债，**不是上游源码、不是第三项维护业务，也不代表完全满足“所有二进制输入仅来自公开 5.6.3”**。本次没有反编译较新 APK、引入其功能或修改媒体依赖。

Xray 审查覆盖分享链接、security/pin/config、Service 串行执行与代际门控、Binder 死亡/超时、settings 保存/删除/取消、VOD/Live 身份及 Exo/DRM/RTSP、弹幕/字幕/EPG/XML、artwork/logo/preload 的实际调用方。网络恢复审查覆盖 SCREEN/Activity 前后台代际、DLNA 生命周期、Home adapter、API client 与 DNS/DoH 重建、Spider 串行清理和 Glide 失败代际；未复现新的确定恢复缺陷。`tv-recovery` 不反向依赖 `app`、`catvod` 或 `xray`，网络资源重建通过应用自有适配器接入；两个核心模块独立维护仍需要宿主页面/播放器接线。

复现了一个 Xray 分享链接缺陷：Hysteria2 备注允许出现未转义的 `?`，但 `rawQuery()` 从任意位置寻找问号，把 `#node?mport=invalid&insecure=1` 中的备注当成连接参数，导致合法节点报端口错误；合法形状的备注参数也可能被错误移到真实查询部分。先加入失败回归，确认修改前抛出 `Xray link port is invalid`，再仅调整 `:xray` 查询边界，忽略 `#` 之后的问号。冻结 legacy normalizer 同样保留旧边界，这是已登记的 current 有意修复；黄金参考源码和 native oracle 不修改。Xray v26.7.28 与双 ABI JNI/bindings 均未更新，上游业务代码未修改。

验证结果：14 个标准本地入口全部通过；新增 6 个 Hysteria2 备注回归涵盖域名、IPv4、IPv6、authority 跳跃端口、真实查询与备注共存、百分号编码及形似有效参数的备注；双 ABI 各 26 个真实黄金 JNI 转换/runtime 用例仍与冻结 oracle 一致。另以现有 CurrentNativeChain 编译真实当前 Java，在两 ABI 各执行 5 个新备注场景，经 security、固定黄金 native 转换、当前 runtime 构建及 native `testXray` 均成功；证书探测与 pin 存储仍为确定性测试边界。完整 `:app:compileLeanbackReleaseJavaWithJavac --offline --no-daemon` 成功，未为上游 resource/deprecation warning 修改源码。本次未重新 assemble/publish APK、触发 Actions、测试 ART/真实节点或 TV 息屏恢复；约 6 秒恢复等待上限等既有真机观察项继续保留，不据静态推测改写上游状态机。

同时确认此前唯一手动发布 run [`37195530886`](https://github.com/rileyaaa/FingMi-Xray/actions/runs/37195530886) 已成功。`v5.6.3-xray.test.7` 的 tag/build source 均为 `439cea8d7a9d3cdb1a17b4ed962c6d68ed164508`，两个实际 Release 资产如下；发布集合现为黄金版、test.7 和历史源码备份，test.6 已由发布器验证后清理。**test.7 包含独立 recovery 模块，但不包含本节随后修复的 Hysteria2 备注问题；本节测试对应后续 main 源码，不是该已发布 APK 的新增证明。** README 与当前发布说明同步纠正，保留历史构建记录。

| test.7 实际发布资产 | GitHub 资产 SHA-256 |
| --- | --- |
| armeabi-v7a | `fbf6d6beab7c18f0cf4366a8586814667f6d825bf06fca1a7f566357e3077c1e` |
| arm64-v8a | `19ee000e08e62f8019f0d7e4afd7c1005fd775027840bf07f4abcdd6d37caad3` |

#### 2026-10-05 — 模块取消、资源关闭与网络边界复查

固定上游差异与核心运行文件未见新的漂移。补跑 Gradle JUnit 发现 `livePendingResolverRetainsCurrentIdentity()` 断言过期：`resolved()` 现报告 URL 是否变化，但同一播放 identity/generation 保持不变；**仅修测试预期，不修改运行代码**。14 个源码/JVM入口、实际 Gradle Xray 3 项和 recovery 2 项通过。

额外验证 1,188 组 HY2 备注/参数隔离变体、8 次真实 JVM/环回 SOCKS5 握手与 6 组冻结 JNI 边界，确认域名交由 SOCKS 代理解析；这些均不代表 Android ART、真实节点或电视待机已验收。

#### 2026-10-05 — 集中复查与验证入口补齐

在重复完整上游差异审查没有发现新运行故障的基础上，补齐**不同层级的实际验证**：14 项源码/JVM入口、Gradle JUnit（Xray 3 项、TV recovery 2 项）、Leanback Release Java 编译、双 ABI 各 26 组黄金 JNI/native runtime 及各 5 组备注场景均通过。新增 `test-xray-service-execution.py` 编译真实 Service/gate/sanitizer 执行 9 组故障与取消场景，平台和 native 为边界替身。

此前只运行源码 guard、漏掉实际 Gradle JUnit 是验收流程缺口，因此 build/publish workflow 现明确要求执行两个模块的单测。没有新 AC 或实际设备验证，不能把这些通过结果扩大成 APK 或电视运行结论。

#### 2026-10-05 — 复查测试有效性与上游边界

本次不修改运行代码。为证明回归不是“无论如何都绿色”，在仓库外的独立副本中分别移除五处保护：运行中禁止 TEST、START 回调派发失败清理、cancel owner、恢复 owner 关闭后迟到回调、失效 Home 刷新与完成标记；真实编译可以通过，但测试均在预期断言处失败。正向 14 个验证入口、Gradle JUnit（3+2 项）、Leanback Release Java 编译和双 ABI 黄金 native 链再次通过。**人为注入的失败不是产品 Bug，JVM/native 证据不等于真机验证**；未触发 Actions。

#### 2026-10-05 — 正式发布命名与持久签名

按用户要求，将显示版本和 Release tag 统一为 `v5.6.3-xray.1`，Android versionCode 设为 `563001`，新增固定 RSA-4096 发布签名并按授权连同恢复配置保存到私有项目。软件设置直接显示既有 `BuildConfig.VERSION_NAME`，无需修改上游 UI。Xray-core、公开 FongMi 源码基线及两个模块业务行为不变；此次差异限于版本/签名、构建与发布验证、对应文档。

旧 `test.7` 对应 `439cea8`，源码备份对应 `41896214`，均早于本次来源；正式 APK 包含后续 Hysteria2 备注解析修复。手动 current-main/build 与 publish 入口改用 Release variant 和持久签名，保持纯 `workflow_dispatch`；原生库验证器支持上游 Release finalizer 的实际文件名，新增签名/版本/non-debuggable/16 KB alignment/内嵌 Git revision 校验。签名验证器同时支持 Build Tools 37 的 `V2 Signer:` 格式，并用旧临时签名 APK 验证拒绝路径。

完整本地 Release 混淆、资源压缩、Lint 与 assemble 已通过。首次离线运行缺少 Lint 传递依赖 `stax-api` / `xpp3`，联网补齐后成功，没有禁用检查或修改上游业务。14 个 source/JVM/验证器入口通过；实际 JUnit 强制重跑 Xray 3 项、recovery 2 项通过。双 ABI APK 的版本与同签名、Manifest 安全接线、四类原生库 PT_LOAD、单 ABI 打包、MPEG-H class/native 及 16 KB 对齐通过。提交后再次打包，以保证 APK 内嵌 Git revision 与发布 tag 的构建源码完全一致；最终 digest 以 Release 资产为准。正式状态是发布渠道选择，Android ART、真实节点、电视覆盖安装与待机/长后台恢复仍未实测。

旧发布及旧备份仅在新 APK / 新 tracked-tree ZIP 的远端 digest 与 tag 核对后清理。新源码备份包含签名文件和恢复配置，不包含临时产物；签名不可重建，后续维护必须复用并由用户保留离线副本。

#### 2026-10-08 — 独立复核上游边界与七条用户分享链接

本轮重新读取项目文档并读取远端源码基线；公开 FongMi/TV HEAD 仍为 `c616c0aa3613e87529791587a9f71b78c278c991` / 5.6.3，审查起点为 `3fab84a`。重新生成完整 tracked-tree 差异：1061 个同路径文件完全一致、57 个修改、2 个删除、381 个新增。审查分别沿上游差异、Xray 生命周期与安全配置、TV 恢复及分享链接转换链展开，不将旧测试记录当作本轮通过证据。

57 个修改文件逐项检查后，未发现本轮需要再恢复的无关上游业务修改。另读取固定公开 media 的实际 MPV API，确认现有兼容映射对应公开源码缺失接口。9 个普通 Config/API/UI 文件及先前恢复的通用取消/频道回收方法仍保持上游；两个核心模块没有反向依赖宿主。既有 Libass 高版本 APK 原生库构建债仍存在，本轮不反编译更高版本 APK、不引入其业务行为。

七条用户链接加 30 个 IPv4/IPv6/域名、跳跃端口与编码变体，在双 ABI 各完成 37 例 current Java → 固定黄金 JNI → current runtime → native `testXray`；744 项字段断言通过，归一化、安全转换与 runtime 配置均与冻结恢复 Java 一致。特别确认 Argo 的连接域名与 TLS SNI / WS Host 分离，`/?ed=2560` 保留正确；HY2 IPv6 / 跳跃端口、Reality XHTTP / gRPC、VMess KCP seed 及 VLESS / Trojan WS 参数同样通过。双 ABI 各 26 项冻结 native oracle 通过，当前 AAR 中 JNI 与黄金文件逐字节相同。固定公开 core 的本地 DNS / IPv6 TCP / UDP 9 个子场景另通过；这是源码与环回环境证据，不能替代 Android 上的实际节点解析。真实用户凭据只作仓库外私有测试输入，未连接用户服务器；证书探测及 pin 存储为确定性边界。

本轮确认并修复一个独立于节点导入的 Xray 问题：公网 IPv6 **媒体 URL** 的 `URI.getHost()` 包含 `[]`，真实 destination guard 只接受裸 IPv6，VOD / Live 因而拒绝启用 Xray。旧测试共用简化 guard，掩盖了这处真实组合缺陷。本轮先替换为真实 current / legacy guard 并得到预期失败，再只修 `XrayPlaybackAddress` 的 URI 边界；135 个回归场景随后通过，私网/保留/zone/mapped 地址继续拒绝。黄金 APK 原始 DEX 也直接传递带括号主机，这是已登记的有意修复，证据与历史差异见 [RECOVERY.md](RECOVERY.md#公网-ipv6-播放地址current-有意修复)。不改 FongMi 业务文件、核心配置或冻结 oracle。

修复后重新执行 14 个标准 source/JVM/验证器入口，全部通过；Gradle JUnit 强制重跑 Xray 3 项、recovery 2 项，失败/错误/跳过均为 0，Leanback Release Java 编译强制重跑成功。另以真实 Service 和替身平台/native 执行 3 个销毁故障场景，覆盖正常停止、stop 连续异常、prepare 阻塞后的中断及禁止启动/信任写入；恢复核心另验证 8192 种网络稳定性序列、27 个代际/关闭场景及 5000 轮前后台/息屏/配置重建组合，均通过。没有复现其它确定的 Xray 资源释放或待机恢复缺陷，不据理论竞态扩张上游状态机。

本次只更新源码修复、对应测试及证据文档；RECOVERY 中遗留的拆分前归属说明也已纠正。Xray 核心、应用版本与固定签名保持不变，未触发 Actions 或重发 APK；已发布 `v5.6.3-xray.1` **尚不包含本轮公网 IPv6 媒体地址修复**。测试不包含 Android ART/Binder、真实节点握手/播放、设备 RSS 或电视待机/长后台验收；约 6 秒恢复兜底与后台 player 保留仍是既有设备观察项。

#### 2026-10-08 — 发布前全新复查与同名替换流程

按用户明确要求，以 `6e7ac98` 再次独立读取当前源码与公开上游，重新验证模块边界、135 个真实地址检查场景、7 条链接及 30 个变体的双 ABI 配置链；未确认新的生产缺陷。额外使用真实 OkHttp 5.5.0 与环回 SOCKS 验证运行/排队请求取消、keep-alive 连接回收、基础 client 隔离和公网 IPv6 请求路径，两场景通过。恢复部分新增多 Home owner 的 6 种回调交错及网络/DLNA 异常测试，真实 OkDns / Doh / OkHttp 完成 100 轮重建；确认派生 DoH client 与被清理的 transport 共享池和 Dispatcher。固定公开 core 的 3 个 WS Build 场景确认 `ed` 提取为 early-data 大小并从握手 path 移除。Android 平台/调度仍为明确替身，不等同真机验收。

本次用户明确授权 GitHub Actions 编译，并作为单次例外同名替换 `v5.6.3-xray.1`、更新旧 `source-backup-2026-10-05-main-357402dc`。版本名称、`563001` 与正式签名保持不变；发布器补齐同源码备份、草稿逐资产校验、旧包 rollback 保留及验证后清理，避免构建/上传失败先丢失现有版本。源码备份名称按实际构建 SHA 和 UTC 日期生成；最终是否发布成功及产物摘要以完成后的 Actions / Release 核验为准，准备流程不代表发布已完成。

#### 2026-10-08 — Actions 工具链故障与 Xray 内存复核

实际 Actions 失败发生在 Gradle daemon 启动阶段，尚未进入应用编译：workflow 安装 Temurin 21，而公开上游 `gradle-daemon-jvm.properties` 要求 JetBrains 21，备用 Foojay 下载地址返回 HTTP 400。两个 current-main build/publish 入口改为通过 `setup-java` 预装 JetBrains 21，并在 player/native 重建前用禁止自动下载的 `gradlew help` 实际启动 daemon；保留上游工具链条件，不更换 Xray core、版本或签名。官方 JBR 21.0.11 下载已按官方 SHA-512 校验；全新独立缓存下正向 daemon 启动通过，普通 OpenJDK 21 的负向控制按预期拒绝 vendor 不匹配；没有生成 player/Libass/libXray AAR 的干净 tracked tree 同样通过 `help`。失败 run 尚未执行发布步骤，旧正式包及旧备份保留。

同一官方 JBR 下强制重跑模块 JUnit 与 Leanback Release Java 编译通过，XML 确认 Xray 3 项、TV recovery 2 项，失败、错误、跳过均为 0；build hygiene 与 9 个发布事务测试通过，两个 workflow 的 YAML 和纯手动触发结构通过检查。本地编译通过不等同于新 Actions 已完成 assemble / 发布。

内存专项重新组合真实 `XraySessionController` 与 `XrayServiceClient` 执行 9 类共 9000 次启停、绑定失败、超时、重入与迟到回调序列，终止后 binding、DeathRecipient、pending 引用及 Handler 任务均清空。真实 OkHttp 5.5.0 与本地 SOCKS/HTTP 完成 102 次资源生命周期，FD 数 `13→13`，204 个弱引用跟踪对象全部可回收；另一个独立宿主验证完成 10 次活动/空闲连接关闭和 250 次 client 创建销毁，连接池与请求计数归零，普通 player client 不受影响。真实 Service 的 4 类销毁故障验证包含停止异常、准备阻塞及忽略 Java 中断的边界，均到达最终私有进程终止请求。这些没有复现持续泄漏；Android/Binder/native 使用明确替身的部分只能证明清理路径，不能冒充电视 ART、真实进程退出或 PSS/RSS 实测。

沿实际宿主顺序复现并修复两处 Xray 接线缺陷。首次页面初始化先配置弹幕 view、后请求绑定播放服务，原 fork 的 client 选择无条件调用 `player()`，导致服务为空时 NPE；改为未绑定时沿用上游 `OkHttp.player()`，绑定后继续选择当前播放 client。另一处是新播放页改变共享播放器 key 后，旧页 `onStop` 的 owner 检查不再成立，可能关闭 HTTP 资源却未卸载共享播放器的旧代理。实际编译的 PlayerManager / PlaySpec / XrayHttpClient 组合复现了对已 shutdown client 的保留；新 binding 交接钩子在新页播放任务前同步结束旧 Xray。新增回归分别在修前以 NPE、移除交接钩子时以旧资源未释放断言失败，修后通过。改动只落在三个宿主文件的 Xray 必要接线，不改上游 `PlaybackService`、`PlayerManager` 通用逻辑，也不为上游自身问题追加修补。

两处宿主修复完成后，重新执行 14 个标准验证入口（包含新增初始化/交接回归）全部通过；官方 JBR 下 Leanback Release Java 再次强制编译通过，发布事务 9 项通过。Xray 模块源码、核心 AAR、TV recovery、版本和签名均未变化；完整 APK assemble 和远端替换仍由授权的手动 Actions 流程执行，以实际 run 及资产核验为准。

#### 2026-10-11 — Actions 磁盘峰值修复

继续处理前次发布失败。真实 runner 的 JetBrains 安装、daemon 预检、源码 guard 和双 ABI Xray native chain 已通过，随后 Robolectric 下载 Android 测试运行库时返回 `java.io.IOException: No space left on device`；这是磁盘耗尽，不是十条 Libass 用例分别出现行为错误。既有清理位于 Libass 测试之后，两个完整 native harness 同时占用空间；本地相同目录的实占约为 v7 2.7 GiB、arm64 3.5 GiB（用于说明规模，不冒充 runner 的实测剩余容量）。

两个 current-main workflow 将清理提前到各自消费者完成后，避免两个测试运行环境同时长期保留；仅删除本次工作目录下已使用完的输入，不清系统工具链、依赖缓存、当前 AAR 或签名。build hygiene 在隔离临时目录执行真实 cleanup shell，验证已消费 Xray 文件删除、后续 Libass 输入及 AAR 字节完整，并检查清理位于验证之后、Maven 之前。所有测试、固定 hash 与发布校验保持开启，workflow 仍只手动触发。

官方 JBR 21.0.11 下以新外部目录重新完成 Libass 构建，Robolectric 10 项通过，失败、错误、跳过为 0；extractor SHA-256 仍为 `feb8be30e3d431391ce4b3b165a6cbfb18313969d7ba7da2d6ccfeb96d25ee68`，candidate 仍为 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861`，双 ABI native / Java contract 通过。本轮不修改运行源码、公开上游基线、Xray 核心、版本或固定签名。

另完成包含前轮两处宿主修复的本地双 ABI Release assemble，实际执行 R8/L8、打包及签名，原生库运行段、Manifest、固定证书、`v5.6.3-xray.1` / `563001`、non-debuggable、16 KB 对齐和内嵌源码核对均通过。此本地 APK 来源为 `950d8a6`，只作为完整构建证据；远端最终包由提交构建流程修复后的 Actions 重新产出，不能复用本地摘要冒充其结果。清理回归、9 项发布事务测试、YAML 与 Bash 语法检查通过；设备安装及电视运行仍未实测。

#### 2026-10-11 — 下载输入失效与冷入口恢复修复

后续 Actions 已通过工具链预检和公开 media 的 17-AAR 构建，失败点是既有 5.6.8 APK 下载 HTTP 404；这次不是 artifact 配额或 runner 磁盘错误。已保存必要失败证据并按用户授权清空 Actions artifacts，核对 artifacts/caches 均为 0。一次性提取后清理的长期授权写入 AI_COLLABORATION；10 日新增的非 canonical 临时审查文档早已删除，没有新增验证结果或运行源码变化，不重新创建。

本项目现有正式双 ABI APK 内的 Libass SO 与原固定输入逐字节一致；正常构建改为一次选定当前正式 Release、按资产 ID 下载并校验两份 SO。容器摘要与来源如实记录，原始上游整包校验模式仍保留，固定 native/candidate 摘要不变。先校验可用输入再执行昂贵 player 构建，禁止用新版本 APK、修改 hash 或放松最终校验来绕过故障；来源债和历史重建限制见第 6 节。

新鲜公开 TV tree 对照仍为 5.6.3，逐项复查现存宿主差异，没有确认需要恢复的无关业务修改。恢复模块则复现了可达的冷 Live → 首次 Home 晚注册问题：旧 Live 的 STOP 误扣可见 Home，错误进入后台且漏掉 SCREEN 恢复代际。只改独立核心的 Activity 身份配对及销毁引用清理；旧核心负向回归明确失败，新核心双 flavor 回归、8192 种稳定性序列、27 个迟到回调场景、5000 轮生命周期组合和 Recovery JUnit 2 项通过。普通上游 App/Home 不变。

Xray 当前源码重新验证 9000 次 Controller/Client 清理序列、102 次真实 OkHttp/SOCKS 开关（FD `13→13`、204 个弱引用可回收）及四类 Service 终止边界，未确认新泄漏。七条分享链接与 30 个变体在 arm64 完整 native/runtime 链通过，372 项字段断言、26 项冻结 oracle、本地 DNS/IPv6 TCP/UDP 9 项和 WS early-data 3 项通过。当前云主机高 PID 触发 API24 ARM32 Bionic 旧 mutex 的 16 位 owner TID 限制，v7 harness 在进入链接转换前阻塞；本轮本地不能声称双 ABI 均通过，Actions 仍保留原双 ABI 验证门槛。没有连接用户节点，也没有修改 Xray 核心或签名。

修改后的 Xray JUnit 3 项与完整 Leanback Release Java 强制重编译通过，14 个标准验证入口、发布事务 9 项及 native 输入边界 13 项通过。新的资产 ID 下载入口已实际下载双 ABI 并验证；官方 JBR 下分别用保留正式包和原上游容器完整重建 Libass AAR，两份产物逐字节相同，SHA-256 仍为 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861`，49 个类及双 ABI JNI 合约通过。JVM/环回与边界替身证据不代替电视 ART、真实进程 PSS/RSS、握手播放、息屏或 Fast Start 验收；新 APK 与源码备份的最终替换以实际 Actions 成功和远端资产核验为准。

#### 2026-10-11 — 编译通过后的草稿发布 API 修复

包含前述修复的 `943357e2` 已在 Actions 完成公开 media、Libass、双 ABI Xray native、模块测试、TV 编译与 Release assemble；最终 native、Manifest、固定签名、版本、源码标识和对齐检查全部通过。双 ABI 各 26 个黄金 native/runtime oracle 也通过，补足本地 v7 高 PID 环境无法启动 harness 的验证限制。失败发生在最后发布阶段，两个正确的新 APK 已上传至草稿，旧正式版未切换。

根因是发布器用 `GET releases/tags/<tag>` 读取草稿，真实 API 返回 404；`GET releases/<id>` 则能读取正确草稿。原测试替身错误地允许按 tag 读取 draft，漏掉了此边界。修复新草稿和旧版 rollback 草稿的 ID 校验，保留全部状态、资产和 Git ref 检查，测试替身按真实 API 行为调整。16 项发布事务测试通过；修前代码在新回归中明确复现原错误。

补充仅续发原已验收资产的手动入口，避免为发布工具修复重复编译应用。11 项来源与失败注入测试、build hygiene 和 workflow 语法检查通过；真实只读演练已走完原 run/jobs、artifact ZIP、草稿资产 ID 下载、APK 摘要/源码/固定签名/Manifest 核验。Actions artifact ZIP 下载使用 JSON API 的默认 Accept，Release 资产下载才使用 octet-stream；两类 API 区分已由实际请求及回归约束。本次没有修改应用、Xray、恢复模块、公开上游版本或签名，续发 APK 和配套源码备份仍准确对应原构建 `943357e2`，不冒称来自后续发布工具提交。

续发 Actions 已成功完成：`v5.6.3-xray.1` 为非预览且 latest，两个资产 ID/摘要与原 Actions 构建报告一致；配套 `source-backup-2026-10-11-main-943357e2` 已发布，下载后的 ZIP 摘要及全部 1507 个 tracked blob（包括固定签名恢复文件）逐项核对通过。旧正式包、指定旧备份、stage/rollback 临时 Release 和 tag 均在最终验证之后清理。保存失败排错证据后删除已消费的 Actions 报告，artifacts/caches 再次核对为 0。发布工具修复和后续记录留在 main，APK/备份的构建源码身份保持原样；真机验收边界仍不变。


#### 2026-10-11 — 直播初始化缺少基础解码模块

用户真机报告 `NoClassDefFoundError: androidx.media3.decoder.DecoderInputBuffer`。复核正式版双 ABI APK，确认最终 DEX 引用了但未定义 12 个基础 decoder 类型；播放器重建脚本只导出 17 个 AAR，漏掉公开固定 Media3 源码已有的 `lib-decoder`。AAR 的 `classes.jar` 不内嵌 Gradle 的项目传递依赖，复制依赖方 AAR 并不能自动包含 decoder。Android 默认 ProGuard 配置中的 `-dontwarn androidx.**` 使该缺失没有阻止 R8 出包，已有 `-keep DecoderInputBuffer` 也不能创建未输入的类。这是本 fork 构建集成遗漏，不是应在上游播放器业务中修补的问题。

本轮修复补齐同一固定公开源码的基础 decoder 产物，并补充依赖集合与最终 DEX 定义/引用的校验。验收必须先证明旧正式 APK 会被新检查拒绝，再验证修复包；原来的 assemble、签名、原生库和 Manifest 通过结果不能替代 Java 运行时链接完整性。设备直播/点播与实际解码验收仍需与云端证据区分。修复前后运行对照中，原 24 个 AAR 摘要完全不变，仅增加固定公开源码编译的 decoder：修复前 Java 编译通过但 4 项运行用例均失败；修复后 API 28/35 的真实普通音视频/文本、FFmpeg 音视频、MPEG-H renderer 构造及 ExoPlayer 重复创建/释放共 4 项通过，失败、错误、跳过均为 0。最终 DEX 检查器在两个实际故障 APK 上均明确拒绝 12 个缺失类型；检查器 12 项回归及候选依赖 9 项回归通过。完整固定公开源码的 18 个 AAR 已重建并通过符号依赖校验。此次修补按正常版本规则推进为 `v5.6.3-xray.2` / `563002`，不沿用此前 `.1` 同名替换的一次性例外。随后本地完整 Leanback Release assemble（R8 混淆与资源压缩开启）通过，双 ABI 最终 DEX 中被引用的 46 个 Media3 类型均有定义，三个显式保留 buffer 均存在。双 ABI native PT_LOAD、14 项 Manifest 权限/服务接线、固定正式证书、`563002`、non-debuggable、16 KB 对齐校验全部通过。该本地包用于提交前验证；正式发布必须由 Actions 从修复提交重新构建，不把本地工作树包冒称提交后的 CI 产物。随后 Actions 已从该修复提交完成双 ABI 全量构建并发布正式 `.2` 与配套源码备份；本轮下载的 arm64 正式资产摘要与发布记录一致，DEX 的 R8 map ID 与用户后续播放崩溃日志一致。编译、链接与发布成功不等同所有页面生命周期已通过设备验收。


#### 2026-10-11 — 退出播放页与请求主机名崩溃

用户在 `.2` 报告退出直播时 `You cannot start a load for a destroyed activity`。根因是本 fork 的 artwork 清理在 `onDestroy()` 里调用 `Glide.with(activity)`；Android 此时已标记 Activity destroyed，异常中断后续会话/时钟释放。Live 与 Video 的同类接线一起修复，通过 Application manager 清理原 owner 的 target；退出/销毁时仍先卸载代理，再跳过 UI、logo、artwork 和 EPG 恢复。真实 Glide 5.0.9、当前 Gradle runtime、Robolectric API 28/35 共 12 项通过；相同回归运行修前宿主产生 4 个失败和 4 个错误，包含用户报告的原异常。调用方初始化、旁路取消、跨页面交接及 TV recovery 回归也通过。

另一个 `nc2.<init>:20 → tn2.intercept:128` 与实际发布 APK 的 R8 map ID 精确匹配，定位为 `OkProxySelector.Policy` 对 `URI.getHost()` 的空值调用。该类及拦截器整份源码与公开上游基线相同；部分 OkHttp 接受的域名（如下划线域名）转换为 Java URI 后 host / port 无法识别。用户明确允许仅修复此项上游崩溃，例外登记在 AI_COLLABORATION 第 9 节。最小修复从规范化 `HttpUrl` 读取 origin 的 scheme、host 和有效端口；不把所有空 host 合并成空字符串，不改代理选择、规则匹配或重定向实现。真实 OkHttp HTTP 链与本地服务器验证四类域名、无 Content-Type 响应及不同 host / port 的 origin 隔离；14 项原有代理/重定向/认证回归加 2 项新回归共 16 项通过，同一测试对独立编译的公开上游恰好新增 2 项 NPE 失败。OkHttp 自身对这类 URI 空 host 选择 DIRECT 的既有规则保持原样，不声称新增自定义代理支持。

首页点播无响应找到一条可执行的相关路径：上游 `CrashActivity` 在历史含 Home 时设置 crash 标志；下一次 `SiteApi.homeContent()` 跳过一次 Spider 首页加载并返回空分类，`VodActivity.start()` 在空分类时直接返回。执行这三个实际方法能复现首次不跳转、再次刷新分类后可跳转；三个整份文件保持公开上游原样。尚不能将该路径认定为用户现场唯一原因，不能因此修改上游通用导航。

项目实际 `:catvod:testDebugUnitTest` 也执行 16 项且失败、错误、跳过均为 0；该工程没有 Release unit-test task，CI 使用实际存在的 Debug JUnit 入口，APK 仍编译 Release variant。修复集中完成后，本地 Leanback Release assemble 在 4 分 38 秒完成，执行了重新编译、R8 和打包签名；双 ABI 最终 Media3 46 项引用均有定义，原生库、Manifest、固定签名、`.3` / `563003` 与 16 KB 对齐通过。构建使用提交前工作树并单独记录来源，正式 Actions 必须从提交后的源码重新构建。

以上 JVM / Robolectric 与构建证据不代表电视 ART、真实源搜索播放、硬件解码、PSS/RSS 或连续遥控操作已经验收。正式 APK 和配套源码备份仍以 Actions 发布及远端资产核验为准。


#### 2026-10-11 — 发布标记与固定构建输入分离

新的 Actions 在输入预检阶段停止：已有 `.1` / `.2` 资产未变化，但远端 Release 已被改为预览版，`releases/latest` 因此返回被脚本明确排除的 5.6.0 黄金参考。问题发生在公开 player/native 重建之前，不是新的应用编译错误。保留远端预览状态，将容器选择改为分页读取已发布版本、按数字版本选取最新符合命名的非草稿；只将指定 APK 作为两份固定 Libass SO 的容器。最高版本资产不完整或摘要不符仍必须失败，native pin、历史上游整包验证模式和最终 APK 校验不变。这使重新标记已发布版本不会切断固定构建输入，也避免错误地把有问题的旧包重新设为正式版。

容器选择与完整性回归 18 项通过；实际分页查询后选中仍为预览状态的 `.2`，按原资产 ID 下载双 ABI，APK size / digest 和两份固定 `libmedia3ass.so` SHA-256 全部通过。报告区分 `tag_source_commit`（tag 快照观察值）与 APK 摘要，不将其冒称重新验证的 APK 编译源码；下载和提取不读取 Java/DEX。此次仅修构建取源，应用修复、`.3` 版本、固定签名和核心不再变化。

#### 2026-10-13 — 可选 TLS 分片与验证边界

用户反馈在自己的网络使用 `tlshello / 80-120 / 5-10` 后连接改善，明确要求在 UDP 下增加轻量开关。当前仅在 Xray 设置及模块内部接入默认关闭的选项，具体配置、适用范围与 DNS 边界见前述 Settings / Binder；不据此将此前连接失败认定为 DNS 污染，也不把 Xray 测试结束后的进程清理当作根因。没有修改 FongMi 普通业务、TV recovery、固定核心、版本或签名，未触发 Actions 或发布新 APK。

固定发布 ARM64 JNI（SHA-256 `40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece`）实际 `testXray` 接受关闭、finalmask 分片及旧 freedom 分片三组配置。Go TLS / Chrome uTLS 各自开关两态共四个本地 VLESS+TLS+WS 测试全部完成证书 pin 校验、TLS 握手、WS 升级、`/?ed=2560` early-data 和隧道内 HEAD 204。环回链路的 TLS record 捕获中，关闭为一个 ClientHello record；开启分别为 19 / 18 个，非末段 payload 均为 80–120 字节，到达间隔约 5.3–9.9 毫秒，重组得到完整 ClientHello。目标、证书及 HTTP 响应均为本地测试，未连接用户节点；这证明固定核心的分片配置实际生效，不证明用户网络已恢复或普遍提速。其它 TCP transport / REALITY 的覆盖来自固定核心源码与配置回归，未声称各自完成端到端握手。

新增配置回归 36 项通过，并覆盖默认关闭、既有 mask 保留与顺序、重复应用、H3 跳过、REALITY 不受无关 TLS ALPN 影响，以及 ping 副本保留选项且不污染播放配置。真实 controller/client/service 配合 Android/Binder/native 替身验证保存、删除、未保存测试、不可变请求及 validate/test/start 传递；既有 normalizer、transport-security、playback、ART API 与构建 guard 通过。独立复核同时修正旧源码 parity guard 对注释的过度转义匹配，确保 Java 字符串中的斜杠不会遮蔽真实配置差异；黄金恢复文件保持冻结。

官方 JBR 21 下 Xray JUnit 3 项（失败、错误、跳过均为 0）及 Leanback Release 的 Java、AIDL、资源编译通过。本地 ARMv7 native harness 再次遇到既有 QEMU 超时，因此不声称本轮 v7 原生验证通过，也不据此认定设备核心故障；没有重复等待。以上没有覆盖电视 ART/遥控实测、真实节点及设备内存曲线，也没有完成新 APK assemble/发布。

#### 2026-10-13 — 分片参数评估与 `.4` 发布准备

用户补充该预设来自手机 IG 图片/视频的低延迟使用经验，并要求评估后发布电视版本。保留已实测有效的 `80-120 / 5-10`，不开启全局默认，不增加调参或 DNS 面板。本地两组捕获的首末 ClientHello 分片跨度约 125 / 139 毫秒；这是每条新 TLS 连接的握手开销，不是后续媒体数据持续分片。在受干扰线路上避免重试可能抵消该开销，但缺少用户线路的受控 A/B 证据，不能据本地环回宣称其它参数更快。自动跳过按 transport/security 判断，VLESS/VMess 等协议名本身不决定适用性；XHTTP 独立 `downloadSettings` 子连接不继承顶层 mask，不将其计入分片覆盖范围。

按用户要求仅用 Leanback 默认/简中/繁中资源覆盖将应用显示名称改为 `FongMi-Xray`。公开上游资源、包名 `com.fongmi.android.tv`、固定签名与 Xray 核心保持不变。远端 `.3` 已发布，本次正常递增到 `v5.6.3-xray.4` / `563004`；发布器同步生成匹配源码备份，并在验证完成后替换指定的 `source-backup-2026-10-11-main-b01e193a`。构建与上传结果以 Actions / Releases 实际验证为准，准备状态不等于已发布。

提交前本地 Leanback Release Java 编译、资源链接和 Manifest 合并通过；用 AAPT2 读取本次双 ABI linked resource table，默认/简中/繁中 `app_name` 均为 `FongMi-Xray`，版本与包名一致。Gradle 两模块单测入口通过并复用未变更结果（Xray 3 项、recovery 2 项，失败/错误/跳过为 0）；build hygiene、16 项发布事务、12 项续发来源回归、固定签名与两个 workflow 纯手动 YAML 检查通过。完整 APK assemble、最终 DEX/native/签名验收与远端发布交给本次用户授权的 Actions 从提交源码执行，不将本地编译检查冒称正式 APK 已发布。

#### 2026-10-13 — `.4` 发布后复核与上游补丁登记

重新读取 Actions 和 Releases，确认 `.4` 已从 `93a69dc7` 完成正式构建、发布及最终校验；两份 APK 的远端 digest 与该构建日志一致，配套备份为 `source-backup-2026-10-13-main-93a69dc7`。本轮未重新下载 APK 或将这些 CI 结果写成新的本地构建。按用户要求把唯一的 `OkProxySelector.Policy` 上游业务补丁、回归入口与未来跟随上游的处置规则放到本文前部；AI 协作限制同步明确，只有有证据且明显影响实际使用的上游故障才允许最小例外。

独立读取 Xray 配置、安全、Settings/Binder/Service、HTTP/Socket 资源所有权及播放页接线，重新执行 session 18 项、settings 18 项、Service 10 项和 client 生命周期回归；36 项分片配置、normalizer/display/HY2、安全转换、媒体旁路及页面交接、135 项播放地址回归均通过。恢复侧重新编译当前源码执行双 flavor/冷入口回归、8192 种稳定序列、27 项迟到/关闭场景、5000 轮生命周期和 6 项多 Home 交错；真实 OkHttp/DoH 100 次重建以及各 5 条运行中/空闲环回连接清理通过，专用 player client 保持独立。

未确认新的可达运行缺陷，本轮只更新文档，不改变生产代码、核心、签名或版本，也不重复触发 Actions。上述 JVM/环回证据不替代电视 ART/Binder、OEM 待机/广播时序、真实节点网络或设备 PSS/RSS；既有证书预探测分片限制、独立 XHTTP 下载子连接和恢复约 6 秒兜底仍按已登记边界处理，不据推测追加功能或重构。

#### 2026-10-20 — 独立复审与公开上游核对

重新读取公开 FongMi/TV 默认分支 `fongmi`，HEAD 为 `0af3b31a1783b8fa4f0ce12e52ac9fad78ddfb1e`。相对固定基线 `c616c0aa…` 的 10 个新提交仅修改 `website/` 中 17 个文件，Android 源码、构建配置和 5.6.3 版本均未变化；本轮不因网站更新迁移应用基线。当前应用、两模块及兼容层源码与已发布 `.4` 的构建提交一致。

相对固定上游，1059 个已有路径完全相同；59 个修改路径已逐项阅读差异，主归类为 Xray 接线 36、恢复及混合接线 12、构建/签名/文档/自更新隔离 7、固定公开媒体 API 兼容 2、已批准主机名修复及回归 2。删除项仍只有 Pages workflow 和网站 README，没有删除 Android 运行源码，也未发现需撤回的无关业务修补。普通业务例外仍只有本文前部登记的 `OkProxySelector.Policy`；核心模块独立不等于宿主零差异，既有 Libass native 来源债也没有因本次审查消失。

重新独立阅读配置/安全/分片、Settings/Binder/Service、播放资源所有权和待机恢复；本轮执行 normalizer（33 个边界、8 个显示边界及发布样例/HY2 回归）、分片配置 36 项、传输安全、session 18 项及 settings 生命周期、client 生命周期、Service 10 项、播放接线/旁路、135 项播放地址、TV recovery 双 flavor/冷入口/代际竞态，以及 core parity、ART API、自更新禁用和构建 hygiene 检查，均通过。未确认新的可复现运行缺陷，没有修改生产代码、Xray 核心、签名或版本，没有触发 Actions 或重新发布 APK。

本轮证据为静态审查与实际 Java 源码的宿主 JVM 回归；Android、Binder 和 native 边界使用确定性替身，没有重新运行历史 native/FD/弱引用压力测试，也没有电视 PSS/RSS、节点握手或分片性能实测。恢复后的云环境不含历史外置压力 harness，历史结果继续作为历史证据，不能冒充本轮验证。后续优先把有长期价值的最小、无敏感信息的压力 fixture 纳入现有 `tests/`，并固定真机启停、播放切换、待机唤醒及网络切换的验收步骤；在出现失败证据前维持当前实现和可选分片参数，不增加强制 GC 或新的恢复状态机。


#### 2026-10-26 — 完成 `.1` 发布续传与双版本清理

原 Actions `40252299406` 已从 `4bea3a54ece68fbb439374e7d7944ec94fe28683` 完成双 ABI 的完整编译、native/DEX/Manifest/签名验收及草稿上传；失败原因是后续 tag 操作权限，不是编译失败。当前 main 的应用、两模块与兼容层同该构建逐文件一致，后续提交仅调整发布工具与文档。本轮使用环境已有的仓库授权成功创建 `.1` ref，执行同一续发工具，重新下载草稿资产并核对摘要、内嵌来源、固定证书、版本、DEX、Manifest 和 16 KB 对齐，未重复完整编译或触发新的 Actions，也不将当前 main 冒称 APK 构建来源。发布事务 21 项、续发来源 14 项、DEX 检查器 12 项回归通过。

新正式 `.1` / `563001` 为非草稿、非预览且 latest；arm64 SHA-256 为 `004cd5e003a644a7e421a859cd7a7187e98e729bea94af157127dd3d20609bd5`，v7 为 `64fdc38928f96185e924444e9c4ca33c582021e732df4b7e041daa4321615424`，与原 Actions 报告一致。完整源码归档先验证通过再按本次用户要求删除；远端 Release 与 tag 最终只保留 `v5.6.0-xray.5` 和 `v5.6.3-xray.1`，黄金资产不变。临时草稿、stage/backup 标签与旧 `.4` 已清理，失败证据提取后清理 Actions artifacts。

本次版本重置是用户指定的一次性例外，`.2`～`.4` 的安装 versionCode 高于 `563001`，通常不能直接降级覆盖；Release 和 README 已说明先备份配置。固定包名、签名、公开上游和 Xray 核心未变，后续正常发布继续按版本规则递增。本轮证据不包含电视安装、实际节点和设备内存测试。


#### 2026-10-26 — 简化手动入口与取消 Release 项目备份

按用户要求从发布器、续发工具和工作流中移除源码归档生成/上传及旧备份参数；APK 的草稿验收、显式替换授权、rollback、来源与 latest 校验继续保留。五个历史 recovery 工作流和现行构建中的临时 push-marker 逻辑已移除，三个保留入口分别承担构建检查、编译发布、失败续发，全部限定 `workflow_dispatch`。历史脚本与 fixture 保留在仓库；GitHub 已登记的过时入口同时禁用，不删除 run 历史。AI 规则与构建 guard 禁止自动触发和源码备份回流。此次只调整维护基础设施，不涉及应用、上游业务、两模块运行源码、核心或固定签名；不编译或重发 APK。

本轮发布事务 22 项、续发来源 13 项、DEX 检查器 12 项及 build hygiene 通过；独立 YAML 解析确认三个入口仅允许手动触发，45 个 shell 步骤通过 `bash -n`。没有消耗 Actions 编译额度。

## 11. 当前稳定版本与维护边界

当前源码基线：FongMi/TV 5.6.3、FongMi/media 固定提交 `3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`。正式已发布版本为 `v5.6.3-xray.1`，本轮代码清理不更改发布版本号、不重新签名、不发布 APK。

已登记的 `OkProxySelector.Policy` 空 host 最小补丁仍需保留；仅当未来用户明确批准单项维护或升级工作时才独立审查其适用性。历史 5.8.x 升级实验不属于当前主分支的构建及发布条件。



## 12. 2026-11-25 — 独立公开 TV 5.9.0 适配（仅本开发分支）

**未合并或替换 main。** 此节仅记录 `dev/fongmi-upstream-adaptation` 的实际候选工作。冻结来源为 `4a52de1daa465d81df7ac06e886a1f184053253c`，验证提交为 `8819ccf8e3e97bb739f986b04c5cc5e2fad98cf7`，[Actions 45545472828](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45545472828)。Core 仍是冻结的 v26.7.28 定制成套 JNI/bindings，未将独立 Core 候选试验移入此分支。

### 12.1 公开来源与实际候选移植

`scripts/upstream-adaptation/lock.json` 固定实际 TV / Media3 源码 commit/tree、104 个 fork delta 的旧/新/冻结 blob 与策略。AC 真实浅检出公开输入，核对 commit、tree 和许可证 SHA-256，在临时独立 5.9.0 工作树执行移植。57 个文件搬迁或干净三方合并，41 个冲突保持新版上游原状，5 个旧播放器兼容文件暂不移植，其他新版上游文件逐字节保持不变。候选树仅生成在 runner 临时目录，未作为已完成的可构建源码提交，未执行完整 Leanback assemble。独立 AAR 构建使用 5.9.0 公开 SDK/Gradle，不签名、不运行媒体或真实节点。两个正式工作流在本分支保留原定义并禁用 production job；验证入口只给只读权限，源码快照不含历史正式签名目录，不上传产物。

公开来源与许可证实际日志（SHA-256 为许可证文件摘要）：

```text
SOURCE old_tv FongMi/TV c616c0aa3613e87529791587a9f71b78c278c991 8aa6eebcf6bdf320841ef1158f0434faabc7a61f GPL-3.0 license_sha256=3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986
SOURCE tv FongMi/TV d3a0b84b24cf6628d72a4dbc2be453875b005536 82953e314d3009f039bb220db05ca537e0eadc92 GPL-3.0 license_sha256=3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986
SOURCE media FongMi/media 3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d b7a4d78a2168bd5065034d37a242b7e51785ea4e Apache-2.0 license_sha256=cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30
SOURCE media_default FongMi/media 2bc207851df311340767e913931ca7b28cab1794 246fb170134edf5a7b5f8a2ca6f4f8bc81903383 Apache-2.0 license_sha256=cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30
```

### 12.2 已实际解决的独立构建输入

- REBUILT_WRAPPER hook official_sha256 50cb2376064781c79ec3708fe2c29d1c1efcec56cfb471b25172b433172cb9b7 rebuilt_sha256 fb38e8cda7436908b3b1bc10a7a543f4814dd74eb4d9b69c462f088ab8c98422 public_api_equal True
- REBUILT_WRAPPER tvbus official_sha256 b759805bf99d6b9fd0ed4882d12614fc4431fc613ef7e3dcb963d8a35d2160b4 rebuilt_sha256 b759805bf99d6b9fd0ed4882d12614fc4431fc613ef7e3dcb963d8a35d2160b4 public_api_equal True

实际运行 `:hook:assembleRelease`、`:tvbus:assembleRelease`、`:tv-recovery:assembleDebug`、`:tv-recovery:testDebugUnitTest`，Gradle 报 BUILD SUCCESSFUL。Hook 公开 JVM API 相同，输出字节摘要不同，不声称 bit-for-bit；TVBus Java wrapper AAR 字节一致，但其外部 native engine（TVCore 动态 System.load）没有重建，也未测试播放。构建脚本 `scripts/upstream-adaptation/rebuild_public_wrappers.py` 可复现此步骤；不提交 AAR 或把产物混同正式 APK。5.9.0 toolchain 已用于独立 library build，不等于整个 app 编译通过。

### 12.3 仍缺失的构建依赖与来源边界

- Media3/Exo/MPV Java：当前公开 FongMi/media 两个分支均不具备完整 5.9.0 调用契约。对 158 个 Leanback/shared import 的存在性扫描得到 50/66 个缺口，嵌套 import 计数不等于独立类数。方法符号初查也报告 setDecoderManager、setBackendPlayer、getSubtitleOffsets 等缺口。需取得完整合法可用的配套源码与 JNI/AAR 构建合同，再进行真正 javac/assemble；不能靠兼容空壳。
- `app/libs/lib-mpvplayer-release.aar`、`app/libs/lib-decoder-ffmpeg-release.aar`：5.9.0 官方树未跟踪，AbiApkPackaging 明确依赖其统一 libffmpeg.so、libplayer.so、libmpv.so、libc++_shared.so 以及 ABI/DT_NEEDED 校验。FongMi/FFmpeg 的公开 9.1.git (`1a6411b`) 和 9.0.2 (`bdf1719`) 是源码候选（FFmpeg 具体 LGPL/GPL 依赖编译选项）；FongMi/mpv `78fcc83`（仓库许可证标识 GPL-2.0）是核心源码候选，均未证实与 5.9.0 Android JNI 桥及构建配置匹配。未将其二进制投入构建。
- Libass、ISO/BD-J、字幕、音视频效果等定制媒体功能：需要匹配的公开 Media3 实现、JNI 与 native 依赖，不能使用旧版 Libass 补丁或较高 APK 中反编译的实现替代；未证明完整重建。旧 5.6.3 的固定 Libass 原生来源债仍保留在 main。
- QuickJS：官方 FongMi/quickjs `764294b`（MIT）是引擎源码候选；5.9.0 TV 树内 runtime-release.aar / wrapper-java.jar 已核对文件摘要，但精确 Android wrapper 构建输入及版本未建立。不能以引擎源码存在证明已重建插件。
- Node.js：官方 TV 树含两 ABI libnode.so 和公开 C++ bridge；确切 Node 版本、NDK/构建选项与相应源 pin 未确认。两 ABI 摘要见下，未重建或执行。
- Thunder：官方树中四份 Xunlei SDK SO 的 bytes 和来源可核，但未查得对应 SDK 完整公开源码、许可证/再分发条款，未重建或使用这些库。
- TVBus：Java wrapper 已解决；外部 native engine 的版本、合法来源及可重建性未证实。Python/Chaquopy 17.2.0 来自公开版本目录，独立 runtime 插件/wheels 及其原生构建、BD-J runtime ZIP 仍需分别核实，不将模块化 runtime APK 误作 host 所缺媒体 AAR。
- Gradle wrapper、Hook 和 TVBus wrapper 及现有官方 TV 跟踪二进制的完整输入摘要如下。树内官方来源不等于每项 native 的许可证或可复现性已确认；无来源二进制不使用。

```text
UPSTREAM_BINARY_INPUT app/libs/hook-release.aar bytes 5816 sha256 50cb2376064781c79ec3708fe2c29d1c1efcec56cfb471b25172b433172cb9b7
UPSTREAM_BINARY_INPUT app/libs/tvbus-release.aar bytes 3184 sha256 b759805bf99d6b9fd0ed4882d12614fc4431fc613ef7e3dcb963d8a35d2160b4
UPSTREAM_BINARY_INPUT gradle/wrapper/gradle-wrapper.jar bytes 59203 sha256 e996d452d2645e70c01c11143ca2d3742734a28da2bf61f25c82bdc288c9e637
UPSTREAM_BINARY_INPUT nodejs/src/main/jniLibs/arm64-v8a/libnode.so bytes 48803656 sha256 2c591838e691f3d0f18f4c5e4232a75f467a08cea33d8637aa6ea5a8d47bc416
UPSTREAM_BINARY_INPUT nodejs/src/main/jniLibs/armeabi-v7a/libnode.so bytes 42630016 sha256 e9a2f2e6489398fb8968134f75ed385e27563ff2c56ec614b224d354e298511b
UPSTREAM_BINARY_INPUT other/tools/bfg.jar bytes 14483456 sha256 1a75e9390541f4b55d9c01256b361b815c1e0a263e2fb3d072b55c2911ead0b7
UPSTREAM_BINARY_INPUT quickjs/libs/runtime-release.aar bytes 1286144 sha256 95fe344fc77debc9c3b38d1bff0bf9cc7c151422dc6f7809b0595e2820f60567
UPSTREAM_BINARY_INPUT quickjs/libs/wrapper-java.jar bytes 823366 sha256 a8ed7aaec3de6f62da4b2c1dbe12626012117bfed4306656df00c267de19913c
UPSTREAM_BINARY_INPUT thunder/src/main/jniLibs/arm64-v8a/libxl_stat.so bytes 837976 sha256 16d89692e499316519e1da9d6431e31fd4692626c03a2f1509950582cea8521f
UPSTREAM_BINARY_INPUT thunder/src/main/jniLibs/arm64-v8a/libxl_thunder_sdk.so bytes 5607344 sha256 a2aa4e17470c355da6172333859a1a38445ee77b0fa5cf263e934ae00bce4030
UPSTREAM_BINARY_INPUT thunder/src/main/jniLibs/armeabi-v7a/libxl_stat.so bytes 501528 sha256 52093068e0ed5651d8565fb2f560de35d72cf73071319cf0d411be55b6983eba
UPSTREAM_BINARY_INPUT thunder/src/main/jniLibs/armeabi-v7a/libxl_thunder_sdk.so bytes 3680664 sha256 2c202ae36003c2ceaba85bba6560d98f6a56c1559c50cc72d6e3499f9495294a
```

### 12.4 每个缺失 import 和冲突的证据

下表为存在性筛查，实际调用者路径保存在上述 Actions 的 source-stage job 138973922845 的 MISSING_MEDIA_SOURCE 日志；下列“缺”表示对应公开分支中未找到匹配或外层类型源码。

| Media3 import | release-1.11.0-fongmi | release |
| --- | --- | --- |
| `androidx.media3.common.DecoderMode` | 缺 | 缺 |
| `androidx.media3.common.DiscMenuController` | 缺 | 缺 |
| `androidx.media3.common.DiscMenuState` | 缺 | 缺 |
| `androidx.media3.common.DolbyVisionOutputPolicy` | 有候选 | 缺 |
| `androidx.media3.common.MediaChapter` | 有候选 | 缺 |
| `androidx.media3.common.MediaEdition` | 有候选 | 缺 |
| `androidx.media3.common.VideoTransform` | 缺 | 缺 |
| `androidx.media3.common.audio.AudioChannelMix` | 缺 | 缺 |
| `androidx.media3.common.audio.AudioChannelMode` | 缺 | 缺 |
| `androidx.media3.common.audio.AudioEffectParameters` | 缺 | 缺 |
| `androidx.media3.common.audio.AudioEffectProcessor` | 缺 | 缺 |
| `androidx.media3.common.text.SubtitleContent` | 缺 | 缺 |
| `androidx.media3.common.text.SubtitleFontFile` | 缺 | 缺 |
| `androidx.media3.common.text.SubtitleOffsets` | 缺 | 缺 |
| `androidx.media3.common.text.SubtitleSelectionState` | 缺 | 缺 |
| `androidx.media3.common.util.LocalClearKeyLicense` | 缺 | 缺 |
| `androidx.media3.common.util.TrackSelectionUtil` | 缺 | 缺 |
| `androidx.media3.datasource.IsoUri` | 缺 | 缺 |
| `androidx.media3.datasource.ProgressiveIsoCache` | 缺 | 缺 |
| `androidx.media3.decoder.ffmpeg.FfmpegMotionInterpolationController` | 缺 | 缺 |
| `androidx.media3.decoder.ffmpeg.FfmpegMotionInterpolationController.FormatSupport` | 缺 | 缺 |
| `androidx.media3.decoder.ffmpeg.FfmpegMotionInterpolationController.OutputState` | 缺 | 缺 |
| `androidx.media3.decoder.ffmpeg.FfmpegMotionRenderersFactory` | 缺 | 缺 |
| `androidx.media3.effect.ColorToneAdjustEffect` | 缺 | 缺 |
| `androidx.media3.effect.DetailAdjustEffect` | 缺 | 缺 |
| `androidx.media3.effect.VideoAdjustment` | 缺 | 缺 |
| `androidx.media3.exoplayer.DecoderManager` | 缺 | 缺 |
| `androidx.media3.exoplayer.DecoderMode` | 缺 | 缺 |
| `androidx.media3.exoplayer.audio.AudioEqualizerController` | 缺 | 缺 |
| `androidx.media3.exoplayer.hls.CmgConfiguration` | 缺 | 缺 |
| `androidx.media3.exoplayer.iso.BdjRuntime` | 缺 | 缺 |
| `androidx.media3.exoplayer.iso.IsoDiscPreparation` | 缺 | 缺 |
| `androidx.media3.exoplayer.iso.IsoNavigationPlayerController` | 缺 | 缺 |
| `androidx.media3.exoplayer.libass.LibassConfiguration` | 缺 | 缺 |
| `androidx.media3.exoplayer.libass.LibassFontConfig` | 缺 | 缺 |
| `androidx.media3.exoplayer.libass.LibassFontFile` | 缺 | 缺 |
| `androidx.media3.exoplayer.libass.LibassPlaybackSession` | 缺 | 缺 |
| `androidx.media3.exoplayer.libass.LibassSubtitleController` | 缺 | 缺 |
| `androidx.media3.exoplayer.source.ContentTypeResolvingMediaSource` | 缺 | 缺 |
| `androidx.media3.exoplayer.source.DefaultPositionMediaSource` | 缺 | 缺 |
| `androidx.media3.exoplayer.source.EndTrimMediaSource` | 缺 | 缺 |
| `androidx.media3.exoplayer.source.preload.DiskPreloadManager` | 有候选 | 缺 |
| `androidx.media3.exoplayer.text.DefaultSubtitleContentLoader` | 缺 | 缺 |
| `androidx.media3.exoplayer.text.SecondaryTextOutput` | 缺 | 缺 |
| `androidx.media3.exoplayer.text.SubtitleTranscript` | 缺 | 缺 |
| `androidx.media3.exoplayer.text.SubtitleTranscriptParserFactory` | 缺 | 缺 |
| `androidx.media3.exoplayer.text.SubtitleTranscriptSession` | 缺 | 缺 |
| `androidx.media3.exoplayer.trackselection.DecodeTrackSelector` | 有候选 | 缺 |
| `androidx.media3.exoplayer.trackselection.SecondaryTextTrackSelector` | 缺 | 缺 |
| `androidx.media3.mpvplayer.MpvAndroidOptions` | 有候选 | 缺 |
| `androidx.media3.mpvplayer.MpvConfigFileInspector` | 缺 | 缺 |
| `androidx.media3.mpvplayer.MpvDecoderMode` | 缺 | 缺 |
| `androidx.media3.mpvplayer.MpvLibrary` | 有候选 | 缺 |
| `androidx.media3.mpvplayer.MpvPlayer` | 有候选 | 缺 |
| `androidx.media3.mpvplayer.MpvPlayer.VideoOutputOption` | 有候选 | 缺 |
| `androidx.media3.mpvplayer.MpvPlayerConfig` | 有候选 | 缺 |
| `androidx.media3.mpvplayer.MpvSubtitleContentLoader` | 缺 | 缺 |
| `androidx.media3.mpvplayer.MpvSubtitleOptions` | 有候选 | 缺 |
| `androidx.media3.mpvplayer.audio.MpvAudioFilter` | 有候选 | 缺 |
| `androidx.media3.mpvplayer.media.MpvDrmSupport` | 缺 | 缺 |
| `androidx.media3.mpvplayer.video.MpvVideoEqualizer` | 有候选 | 缺 |
| `androidx.media3.ui.PlayerSeekView` | 有候选 | 缺 |
| `androidx.media3.ui.danmaku.Danmaku` | 有候选 | 缺 |
| `androidx.media3.ui.danmaku.DanmakuConfig` | 有候选 | 缺 |
| `androidx.media3.ui.danmaku.DanmakuPlayerViewController` | 缺 | 缺 |
| `androidx.media3.ui.libass.LibassPlayerViewController` | 缺 | 缺 |

未解决的候选接线（不采用 ours/theirs 整体覆盖，保持上游待人工移植）：

```text
CONFLICT_THREE_WAY app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java
CONFLICT_THREE_WAY app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java
CONFLICT_REMOVED_PATH app/src/leanback/java/com/fongmi/android/tv/ui/activity/PushActivity.java
CONFLICT_THREE_WAY app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java
CONFLICT_THREE_WAY app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java
CONFLICT_THREE_WAY app/src/leanback/java/com/fongmi/android/tv/ui/adapter/ChannelAdapter.java
CONFLICT_THREE_WAY app/src/leanback/res/layout/activity_setting.xml
CONFLICT_THREE_WAY app/src/leanback/res/layout/view_control_live_action.xml
CONFLICT_THREE_WAY app/src/leanback/res/values-zh-rCN/strings.xml
CONFLICT_THREE_WAY app/src/leanback/res/values-zh-rTW/strings.xml
CONFLICT_THREE_WAY app/src/leanback/res/values/strings.xml
CONFLICT_THREE_WAY app/src/main/AndroidManifest.xml
CONFLICT_THREE_WAY app/src/main/assets/index.html
CONFLICT_THREE_WAY app/src/main/assets/js/script.js
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/Updater.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/api/LiveApi.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/api/loader/JarLoader.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/api/loader/JsLoader.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/api/loader/PyLoader.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/api/parser/EpgParser.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/model/VideoViewModel.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/playback/live/LivePlaybackController.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/playback/live/LivePlaybackHost.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/playback/vod/VodPlaybackController.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/playback/vod/VodPlaybackMedia.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerEngine.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerSession.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/player/mpv/MpvPlayerEngine.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/server/process/Action.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/ui/dialog/DanmakuSearchDialog.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/ui/dialog/PlayerEngineDialog.java
CONFLICT_THREE_WAY app/src/main/java/com/fongmi/android/tv/ui/dialog/SubtitleSearchDialog.java
CONFLICT_REMOVED_PATH app/src/main/java/com/fongmi/android/tv/utils/Download.java
CONFLICT_THREE_WAY catvod/src/main/java/com/github/catvod/net/OkProxySelector.java
CONFLICT_REMOVED_PATH catvod/src/test/java/com/github/catvod/net/OkProxySelectorTest.java
REVIEW_OLD_MEDIA app/src/main/java/androidx/media3/exoplayer/libass/LibassFontFile.java
REVIEW_OLD_MEDIA app/src/main/java/androidx/media3/exoplayer/text/SecondaryTextOutput.java
REVIEW_OLD_MEDIA app/src/main/java/androidx/media3/exoplayer/trackselection/SecondaryTextTrackSelector.java
REVIEW_OLD_MEDIA app/src/main/java/androidx/media3/ui/danmaku/DanmakuPlayerViewController.java
REVIEW_OLD_MEDIA app/src/main/java/com/fongmi/android/tv/player/mpv/MpvUtil.java
```

**结论**：依赖与宿主边界仍阻断完整 5.9.0 Leanback 双 ABI APK，未完成 Android ART、真实网络、直播切换或待机真机回归。继续的必要前提是合法、可追溯且匹配上述缺口的媒体源码/依赖；不把本次独立 library build 说成整套软件通过。main 不改、不合并、不发行。

### 12.5 5.9.0 的独立依赖来源与 TV 恢复接线推进

本轮只变更候选生成器、固定来源清单和局部回归，不改冻结 5.6.3 运行源码、Core、播放器、签名或正式工作流。12.1–12.4 的数字是 `8819ccf8` / AC 45545472828 的历史实际结果，不冒充新的整包构建结果。

**依赖定位**：TV `d3a0b84b` 的 app/build.gradle 第 102 行以 `implementation fileTree(dir: "libs", include: ["*.aar"])` 载入播放器，不通过 TV 的版本目录声明 Media3 Maven 坐标；定制源仓库 `3c2cbe8` 的 `build-logic-settings/src/main/kotlin/androidx/media3/buildlogic/Media3Modules.kt` 才列出模块 artifactId。以下坐标中的 group 为 androidx.media3；1.11.0 只表示可核对的标准基线，不代表已取得与 5.9.0 匹配的定制 AAR。

| 模块 artifactId / 输入 | 真实缺口与 TV 调用点 | 来源状态 |
| --- | --- | --- |
| media3-common | DecoderMode / DiscMenuController / SubtitleOffsets / AudioEffectParameters；PlayerManager、PlayerEngine、音效控制器 | 两个固定 media 树均缺定制接口 |
| media3-exoplayer | DecoderManager、LibassPlaybackSession、ISO / 字幕；ExoPlayerSession、ExoMediaSourceFactory | 公开标准模块不能替代定制 API |
| media3-exoplayer-hls | CmgConfiguration；PlayerEngineFactory | 缺定制 HLS 合同 |
| media3-datasource | IsoUri、ProgressiveIsoCache；MediaItemFactory、MpvUtil | 缺定制 ISO 支持 |
| media3-effect | ColorToneAdjustEffect、DetailAdjustEffect、VideoAdjustment；ExoVideoEffectController | 缺定制效果实现 |
| media3-ui / media3-ui-danmaku | PlayerView.setBackendPlayer、LibassPlayerViewController、DanmakuPlayerViewController；PlaybackActivity、ExoSubtitleController | 缺宿主适配接口 |
| media3-decoder-ffmpeg / lib-decoder-ffmpeg-release.aar | FfmpegMotionInterpolationController / FfmpegMotionRenderersFactory；ExoUtil、ExoPlayerSession | Java/JNI 和对应 native 制品未获；不能仅因 Gradle 有 module 定义就声称可用 |
| media3-mpvplayer / lib-mpvplayer-release.aar | MpvConfigFileInspector、MpvSubtitleContentLoader、MpvPlayer.getSubtitleOffsets；MpvConfigFile、SubtitleFileContent、MpvPlayerEngine | 缺配套实现、native ABI |
| media3-database | lib-exoplayer、lib-datasource 传递依赖；自身 api(lib-common) | 已确定完整官方同树源码，待实际编译/链接 |

**已确定一项独立来源**：FongMi/media `3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d` 的 libraries/database 与 AndroidX 官方 [1.11.0 tag](https://github.com/androidx/media/tree/1.11.0/libraries/database)（实际 commit `2bc207851df311340767e913931ca7b28cab1794`，亦为原 media_default pin）整模块 tree 均为 `4b17bde909283355be9b2258dae8faf3ffe425e8`。清单新增 `shared_media_source` 并在下次候选 staging 检查两个 tree。标准坐标 `androidx.media3:media3-database:1.11.0` 有官方源码对应；本轮未下载验证 Google Maven AAR/POM（直接读取未成功），不引入制品、不宣称完整编译或跨定制 common ABI 已通过。其余 50 个历史 import 缺口及 native 缺件没有凭空减少。

**已实际移植的独立接线**：5.6.3 的 FongMiNetworkRecovery.clearSpiders 调用 BaseLoader.get().clear(after)，而 5.9.0 BaseLoader 仅有无参 clear 与 destroy，原三方合并冲突。新版按代际换 Node/Jar/JS/Python loader，异步清理 previous，并仅在退出时 destroy retired；保留该机制及原异常聚合，不恢复旧 loader 类。仅在锁定的新版 BaseLoader blob `a4129fc79a16c2920907d184c8e264dd49435cb3` 上增加 clear(Runnable)、普通 worker 上专用 FIFO、同一换代锁内提交清理任务、finally App.post 完成回调。保持普通 clear 无回调、destroy 不变更退出语义；不改任何 Config/UI/播放器或 runtime loader。候选结果 blob `9c2f598f91431cccf7de200c05f8473b8fc7e58f`，原冻结文件仍用原 blob 校验。该路径从历史 three-way conflict 改为显式锁定移植；下一次 staging 才能报告新冲突计数。

**实际轻量验收**：JDK 21.0.12.1，javac --release 17；使用逐字节匹配 GitHub blob 的 5.9.0 BaseLoader 和未改的 NetworkRecoveryCoordinator（`6d335d87264379b037ee682d38fc1c4d85825af7`）执行 `tests/test-upstream-recovery-loader.py`。通过普通 worker FIFO、旧 Home 退出、新 Home 接手、两次稳定样本后刷新、异常时逐 loader 尝试和 finally 回调、退出 destroy/retired 清理；未移植源缺少 clear(Runnable) 而编译拒绝，去掉 FIFO 与提前回调两个变体被测试拒绝。Android/Task/Guava 与具体 loader 是确定性替身，不冒称真实 Spider runtime、线程压力、Android ART 或真机通过。可单独运行，不需重跑旧候选：
```sh
python3 tests/test-upstream-recovery-loader.py --base-loader /path/to/pinned-tv/app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java
```

**Xray 接线尚未改动**：5.9.0 PlayerEngineFactory.create 已去掉旧 decode 入参；PlayerManager 的 replaceEngine/ensureEngine 及 ExoMediaSourceFactory 新增 Auth.Context、独立 SubtitleTranscriptSession、LibassPlaybackSession，默认 OkHttp.player(auth) 与共享缓存。旧 fork 的 playbackProxy、切换时保留播放状态/清理 side requests、RTSP socket factory、DRM 同代理和禁止复用普通直连缓存必须重新按新宿主合同接线，不能以旧 5.6.3 factory/engine 整体覆盖。继续优先审 Home 的生命周期与普通 API/DNS reset 的新入口；播放器适配等待对应公开 media 接口。无新的全量 Android AC：完整 native/media gate 仍阻塞，且本轮局部证据不需要再跑已失败的候选。

### 12.6 TV 恢复宿主整组移植与独立 Media3 构建验收

基于 `837d8f4` 的 BaseLoader 恢复回调移植，新增 `reviewed_recovery_host.json` 和严格输入/输出 blob 门禁。只对固定 5.9.0 Home、SiteViewModel 及自有恢复生命周期、Leanback 渲染桥和适配器实施逐锚点移植；当前 5.6.3 原文件不变。Home 在 adapter 初始化后、权限请求前注册恢复，等待初始配置 ready 且 Home resumed 才检查网络代际；恢复只刷新内容，不重放新版 pending 外部 Intent，保留新版 `releaseResources()` 的 Home/PlaybackService/NodeRuntime 所有权。SiteViewModel 只取消 RESULT lane、清 loadingHome；新版 TaskRunner 已包含 cancel 和更完整的主线程结果门禁，直接保留，不套回旧实现。API37+ 的 DLNA start 服从 ACCESS_LOCAL_NETWORK，统一由恢复生命周期按已有启动状态重试，权限拒绝、普通页面切换或后台 SCREEN_ON 不额外启动；不修改 DLNA 播放实现。

实际本地 JDK21 验收：四份真实候选 Java blob `97a04e5c`、`6d335d87`、`ae204d77`、`a0bc77a9` 与已核对的固定输出完全一致，`test-upstream-host-recovery.py` 19 项断言及 4 个负向变体通过。覆盖权限拒绝/授权、API36 行为、冷外部入口、内部导航、配置重建、重复 SCREEN_OFF/ON、两次稳定采样、旧 Home 退出/新 Home 接管。Android、HTTP/DNS/Glide 与 Spider 清理是确定性替身，不声称实际 Activity、网络或 TV 播放通过。

新增独立验收 `verify_recovery_batch.py`：只生成实际候选并检查已移植路径与真实上游 Intent、普通 player/auth/redirect、图片请求边界；运行新旧两组恢复测试和已移植 Xray Java normalizer/session 回归，并可单独构建实际候选 tv-recovery Android library。其余候选冲突仍保持上游，不运行已知缺件的全 APK 门禁。新增 `public_media_build` 固定四个可独立从公开 FongMi/media 构建的模块 tree（common、database、datasource-okhttp、exoplayer-rtsp），`rebuild_public_media.py` 只构建对应 AAR，记录实际 SHA-256，database 对照 Google Maven 1.11.0 POM/AAR API，两个网络模块检查 Call.Factory / SocketFactory 接口。不复制到 app/libs；构建结果待新验收日志，不能冒称已通过。上游 APK 自更新与 runtime module 安装属于不同路径，5.9.0 Updater/Manifest/Setting 仍待分拆，不发布当前候选。保持现有定制 Core 和旧分享/导入契约，未重新验收新版 Core。

### 12.7 Live 请求身份与 Xray 宿主接口移植

固定 5.9.0 LivePlaybackController/LivePlaybackHost 输入 blob f2c114f8/27324f62，使用 reviewed_live_host.json 逐锚点移植，输出 c7f79c6e/b8774f56。普通宿主保留上游 pending 对象身份门禁、preparePlaybackForRefresh 无条件替代旧播放前的准备而非强制 stop、回看 TIME_UNSET 回退及 push 路由。仅显式启用 TV Xray 宿主门禁时清理旧播放身份；手动 START 重新解析使用新请求但不再次换代，等待代理 START 的已解析请求不会被重连或重复选择重发，退役时清空请求并取消解析，同步回调已换代则不提交旧任务，push 路由先退役 Xray。LivePlaybackState、LivePlayRequest 和 LiveDataSource 保留固定上游实现。

JDK21 --release 17 实际编译六份固定候选 Java 文件（包含 PlaybackResult），tests/test-upstream-live-host.py 16 项断言和 4 个负向变体全部通过；测试 blob bb5803ae、移植规则 c82dc07b。Android、Media3、解析和 Xray owner 为确定性边界替身，不等于真实 LiveActivity、Web 播放、PlaybackService、PlayerManager 或 native 已通过。实际 TV Activity 的代理绑定、自动规则、元数据和 Web 路由仍须逐项移植，旧 Activity 不整块覆盖。

AC [45588016507](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45588016507) 固定 18e099f 的恢复 job 139114518780 成功：58 项移植/干净合并、39 项宿主冲突和 5 项旧媒体待审；19 项生命周期及 4 个变体、BaseLoader FIFO/交接/失败/销毁及两项变体通过，33 normalizer + 8 display 边界、6 Hysteria2 URI 片段回归、真实 Xray Java session lifecycle 与 11 项播放会话同步重入通过，5.9.0 Android tv-recovery assembleDebug / testDebugUnitTest BUILD SUCCESSFUL。该 AC 不包含本节较晚提交的 Live 移植；后者只获 JDK 证据，下一批统一验收已接入测试脚本。现有 Core 不变，旧分享 native 兼容仍须双 ABI 实测。

### 12.8 公开 Media3 实际构建证据

AC [45588016507](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45588016507) 两项 job 均 success，固定 workflow commit 18e099f25416635c4120522089cb48c554167d3d。公开 Media3 job 139114518166 在 3m59s Gradle 构建成功，来源 FongMi/media 3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d / tree b7a4d78a2168bd5065034d37a242b7e51785ea4e（Apache-2.0，许可证 SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30）。实际产物如下，已记入 lock.json 的 verified_build：

| 模块 | bytes | SHA-256 |
| --- | ---: | --- |
| lib-common | 665440 | f835fd9dca0dd562e56430dc0861b468888dbb85301cff314753f1dcdd1fc186 |
| lib-database | 7197 | 520e6f814e42a7d428db187ac073b453c0fcba0f4f5f4edd1cf33fafd2cfb740 |
| lib-datasource-okhttp | 9879 | 67875d86e6339b75baf39c359b22da12ce1fce24f9d15b2144583c568bef742c |
| lib-exoplayer-rtsp | 165543 | 4d9c19231d4a629c01ac601da1fbc452fea86fab87d0c709008cd307076d1952 |

Google Maven 正式 media3-database:1.11.0 POM 1723 字节、SHA-256 951d795778085be496046b11743865f8c4f9e7c385ed163c38bcacb185177e5e；AAR 7197 字节与本次源码构建完整 SHA-256 一致，public API 对比通过。datasource-okhttp 的 Call.Factory 与 RTSP 的 setSocketFactory(javax.net.SocketFactory) 在真实重建 classes.jar 上通过 javap 检查。以上是一次已完成构建的实际摘要、不是第二次重建的一致性证明；未来验证必须对照固定来源、依赖及记录的 digest，发现不同则先调查，不静默换件。没有保留或上传 AAR、没有部署到 app/libs、没有完成完整播放器/JNI/native 或双 ABI APK。临时 workflow 已结束，移除本次一次性 push 文件，不删除 run；复现入口为固定 18e099f 的 workflow 内容和当前脚本，Live 新移植需下次独立批量验收，不冒称在该 AC 内已测试。

### 12.9 Xray 播放 transport 与 5.9.0 Exo 宿主候选

固定 5.9.0 的 OkHttp、ExoMediaSourceFactory、ExoPlayerSession、ExoPlayerEngine、PlayerEngineFactory 与新版 SubtitleFileContent 输入 blob，逐锚点生成候选（reviewed_media_host.json）。保留现有 TV 普通 API/DNS 资源换代，以及新版 Auth.Context / redirect 语义；新增显式 client 的 Auth.Context 绑定，不能退回全局 player client。代理媒体 HTTP 使用同一 session client（包括 DRM、ISO 导航传入的 data source 和字幕转录入口），复用既有 scheme guard 和 RTSP TCP socket factory，不使用直连磁盘缓存、不在代理 engine 中跨媒体预加载。普通路径仍调用原有 factory、cache、metadata、decoder、navigation 和 preload 行为。新版字幕读取仅对传入代理资源的 session 使用代理，不修改 MPV 普通字幕读取。所有输出 blob 已记录；仍须验证真实候选与可用媒体制品。由于新版定制 ContentTypeResolvingMediaSource/ISO/CMG 内部取流、播放器服务与 PlayerManager 所有权未完成验收，本批仅提供未启用的代理 engine 构造及匹配接线，不将其提前接入 PlayerManager，不宣称真实播放已可用。Core、主线及发版文件不变。

### 12.10 独立 transport 验收与第二组公开 Media3

新增 verify_transport_batch.py，严格生成并核对本轮六份 media host 与上一轮 Live host 的实际候选输出，编译真实 PlayerEngineFactory 及从候选抽取的既有 scheme guard（确定性 Android/Media3/engine 替身）；可另行使用 5.9.0 原 Gradle/SDK 编译实际 catvod，复制候选中未修改的三份 Xray 网络源码作为测试输入，用 Robolectric/真实 OkHttp Auth、redirect 和 XrayHttpClient 回归（HTTP 终端交换为确定性替身）。不执行正式 APK、签名或整个旧候选门禁。新增第二组十个公开 Media3 Java 模块 source tree 锁；支持独立 staging 目录及 provenance 清单，已验摘要的重建必须匹配锁，Google Maven database 要求完整 AAR 字节一致。新组第一次构建摘要待日志，禁止当作完整定制播放器或覆盖 app/libs。

### 12.11 5.9.0 字幕侧请求与新 Download 路由候选

在上一批 AC 45596644795 已运行时继续独立代码。5.9.0 Download 移至 catvod，旧 app Download 的 client/tag 写法不能直接迁移。保留新版下载器的文件大小、Range/续传/分段、取消、校验和回调实现，仅新增每实例非空 Call.Factory 绑定，download() 首次请求及 request(client) 保存的 continuation factory 一致，不选显式 factory 时仍使用原 OkHttp.client()。SubtitleApi 保留新版搜索/详情解析、归档和 Task/Download 包路径，移植既有 request id、Call/Download 所有权、异步 UI 投递/ZIP 解压、旧 owner 取消及 Xray transition completion；旧 request id 不能取消新任务。固定输入输出 Download c01a7f3a -> 0ef776e8、SubtitleApi d16c1d82 -> 290690f3。新增 test-upstream-side-requests.py 复用原 16 项回归和一项下载 client/旧 owner 验证，实际 Download 只做源码 transport handoff 门禁，IO/真实服务接管仍需验证；本提交未进入正在跑的 AC，不宣称已通过。

### 12.12 transport 与第二组公开媒体实际验收

AC [45596644795](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45596644795) 的两个 job 均 success，固定 workflow commit `1d03287908435db37a4387a295b5a1e64641e319`。首次触发 45596534600 未生成 job，原因是临时 workflow 的未加引号 if 标量含提交消息中的冒号及空格；修正 YAML 后才执行本批构建，不是重跑已成功任务。

transport job 139144342781：候选实际输出 65 项移植/干净合并，33 项未解决宿主冲突，5 项旧媒体待审；6 份 media host 及 2 份 Live host 输出 blob 一致。Live 16 断言、4 个负向变体；实际 PlayerEngineFactory 15 断言，候选抽取 scheme guard 42 断言，4 个负向变体均被拒绝。Android catvod assembleDebug 与实际 OkHttp/Auth/Xray 3 项 Robolectric 测试通过，构建 1m39s；HTTP 终端交换、engine 与 Android/Media3 相关 JDK 边界是确定性替身，不是实机播放或实际代理网络验证。普通 API reset 不销毁 player 与 Xray client，Auth.Context 同源/跨源重定向边界通过。仍不启用 PlayerManager 代理接管。

公开 Media3 job 139144342951 在 3m25s 构建成功。固定 FongMi/media 3c2cbe8 / tree b7a4d78a，Apache-2.0 许可证摘要与上轮一致。新增十个 AAR 的实际摘要如下，并记录于 lock.json 的 public_media_next_build.verified_build：

| 模块 | bytes | SHA-256 |
| --- | ---: | --- |
| lib-container | 67910 | 980e5bbb08359fa8103aa2c082b71ef739e161c8d6e018ead6fc78b703f61d23 |
| lib-decoder | 19842 | 3aba35e2bb7cbb930fbdaa22bc1c8d42b45ce5002d7a6a0901af9bfacbd44a6c |
| lib-datasource | 182361 | 01ca3ee28ec995eb143c740f3672413b5b3ec429be71565388bf7e265420c15b |
| lib-extractor | 1099488 | 9f5d306cabf3118ae26417c02870200dd245da853f980cdc8d51b27db34accd9 |
| lib-exoplayer | 1792164 | 6527da13a137bb02beda0b06fd913d44a2ec48faea69e301ebf2edef5183e388 |
| lib-exoplayer-hls | 272832 | b15159474508fff57d26426e0c86bf33f0ddafe42a32b2706d9154884956996e |
| lib-exoplayer-dash | 150318 | 107a799baf20951ae85144b3857d03cfd2cea47477df7e759b7289ba797f5464 |
| lib-exoplayer-smoothstreaming | 53726 | c3f9d0375a08bfe0ba6491d958f96a572cb6a4a10bb8113449cd8ee78ff75883 |
| lib-session | 956900 | 5cc3711f21bfd98ebb9bc498d20e221bbb15edeaa9ac0b161334f0a337d17536 |
| lib-ui | 369310 | da5b513a10aa6400703cb2d692ddb8b1c5a970aa31a47278fe8a38b6497dfae9 |

第二组完整 staging 与来源清单生成成功，累计 14 个公开 Media3 AAR 有实际构建证据。每个新增摘要是首次构建记录，不声称已经二次重建字节一致；后续按锁校验。未上传 AAR、未覆盖 app/libs、未补足定制媒体/JNI/native 全部合同、无 5.9 APK 或双 ABI 运行验收。0ccae97 的 Download/SubtitleApi 是该 run 启动后新增候选，侧请求回归尚未执行，本次只接入下一批 transport 验收入口，不将先前结果归给它。保持现有定制 Core 与旧导入合同。已结束的本批一次性 workflow 93 删除，其他会话的发版文件、签名、main 及历史 run 不动。

### 12.13 5.9.0 PlayerManager、Timeshift 与 PlaybackService 宿主接线

固定公开 5.9.0 PlayerManager f7cb9dbb -> 6d7d4ef2、TimeshiftPlayback 23d6cd38 -> d027dbda、PlaybackService 3a8504da -> f996af63。逐锚点移植，不修改当前 5.6.3 app 文件。Xray engine 以资源对象身份匹配；MPV DRM fallback 只在无代理时走上游直连分支；保留新版 ISO edition/字幕偏移/音量/速度/回看及 MediaSession SessionPlayer 结构。切换时先取消旧 side requests、回看解析、预加载和 timeout，退役旧 engine；ERROR 记录当前 PlaySpec/快照而不直连重启，后续 START 可恢复。通过宿主 transition + PlaySpec 身份检查拒绝同步回调期间已换代的旧操作。新媒体 start/parse 清除旧恢复快照，但不无条件清除已获授权的 pending Live proxy。

5.9.0 新增 TimeshiftPlayback 原构造长期捕获 OkHttp.client()，普通 API 待机恢复后会持有已退役 client；改为每次请求按当前播放 owner 选择 client，Xray error 挂起时拒绝回看解析，切换取消旧 pending Future/Call，不清除原有回看时间轴。PlaybackService 保留新版 browse、进度和 SessionPlayer 逻辑，只补 side request/封面取消、URL 通知和旧代理 owner 在远程 browse 新媒体准备前退役；普通 browse 不改变原顺序。保留新版 public 播放器行为，不冒称定制媒体内部取流和 Activity/真实设备已验；当前先待本批独立测试。

### 12.14 播放宿主局部验收与公开 MPEG-H native 独立验证

新增 verify_player_host_batch.py，只执行本轮真实宿主方法（固定 PlayerManager/TimeshiftPlayback/PlaybackService blob，engine/Media3/服务为确定性边界替身）、上一轮未跑的实际 SubtitleApi/DanmakuApi side-request lifecycle，以及新 catvod Download 的 Android 编译与真实文件/Range worker 测试（HTTP 终端交换为合成响应）；不重复上轮 transport auth 或 14 个公开 AAR 构建。失败按首个实际断言/编译错误修正，不为通过而减弱门禁。

Media3 固定 3c2cbe8 的 decoder_mpegh tree 522078ee，README 明确 Fraunhofer-IIS/mpeghdec r3.0.2；已解析 tag 到 commit 335a2587/tree 7c17bcf3，LICENSE.txt blob 2948ac66。保留完整 decoder 与 UI manager，demo 依赖 ilo r2.0.0/mmtisobmff r1.0.2 已解析固定 commit，消费模块默认不构建 demos，离线 FetchContent。verify_public_mpegh_native.py 使用 Android SDK CMake 3.22.1、NDK 29.0.14206865、API24，分别编译真实 armv7/arm64 JNI，验证 ELF machine、PT_LOAD 16KB、Java native 导出全集与依赖，不上传或部署任何 native 制品。Fraunhofer 版权许可附带条件、不授予专利许可；本轮仅 compile/link，不能据此宣称已获分发/专利授权或真实解码验收。

FFmpeg 公开 consumer manifest ec9f8c76 锁定历史 producer FongMi/mpv-android 99a60ad2/tree 7d76eff8/run 31346106984，FFmpeg 04482c8d、dav1d 54706fc6、libplacebo 04b3a091，NDK 29.0.14206865 和两个 ABI 的各 .so/renderer SDK SHA-256。GitHub producer commit 可读取，run 与 artifacts API 均 404；不是可用制品，不将其他 FFmpeg 版本混入。该 manifest 只证明公开 media 分支的历史合同，不证明 TV 5.9.0 私有定制接口（FfmpegMotionInterpolationController/MPV/ISO/CMG 等）已经齐备。本轮结果待实际 AC。

### 12. 本批宿主与 MPEG-H 首轮实测（2026-11-25）

- Actions `45608824619` / job `139186671589` (`9db760c`)：69 transferred/clean merge、31 unresolved、5 old-media-review；23 个真实候选宿主方法断言、5 个负向控制、17 个侧请求生命周期场景通过；Android catvod assembleDebug 与 3 个 Download/真实文件/Range 测试通过（合成 HTTP 回应）。不是完整 App/播放器链接或真机播放证据。
- job `139186672005`：ARMv7 解码库与 JNI 真正完成 CMake 编译/链接，ELF 首个 LOAD 对齐只有 `0x1000`，16 KB 门禁失败，ARM64 未执行。保持所有验收断言，构建显式加入 max/common-page-size 16384 链接参数；只重验 MPEG-H，不重跑通过的宿主及先前 14 个公开 AAR。专利/分发许可和播放器实际解码仍是独立门禁。

### 12. 字幕/弹幕搜索窗口 owner 接管

在 5.9.0 原 `PlaybackDialog.observe`、保存状态与搜索分页基础上移植两个搜索窗口的 Xray client 路由、请求 ID 与取消回调代次。窗口替换/关闭/返回仅取消自己的 requestId；旧取消回调不能重置新请求界面；持当前 PlayerManager 锁核验 owner 与 suspended 后才发起请求，沿用 fork 字幕 API client / 弹幕 player client 的非代理回退选择。此处为源锚点移植，仍需独立窗口边界测试与完整 Android UI 链接，不能记为上一轮已经通过的宿主测试。

### 12. MPEG-H 双 ABI 复验通过

Actions `45609274767` / job `139188254192` (`1feed2d`) 仅执行 native 重验；ARMv7 4,847,928 bytes SHA-256 `e9fcbbb89307ba99bbccd56e28d353ebf02f34ca9d66689e5dd18b1c8fd33b5a`，ARM64 6,152,872 bytes SHA-256 `581451b75ce718d4aae0239fbca21379bb47e1384cd29474f0cc88ef50f5c23d`。两个 ABI 都通过 16 个 JNI 方法、JNI_OnLoad、3 个 PT_LOAD 段与 16 KB 对齐、动态依赖及无 RPATH/RUNPATH/TEXTREL 检查。结果写入来源锁；没有归档或发布二进制，没有宣称完整 AAR 或 5.9.0 播放器/应用可用。

### 12. 本批最终验收记录

- Actions `45609610298` / job `139189413876` (`0651c07`) success：两个搜索窗口实际候选源方法 16 断言与 generation 负向控制通过（确定性 UI/API 边界，非 Android UI 链接）。候选统计 71 transferred/clean merge、29 unresolved、5 old-media-review；上游未触碰范围校验通过。
- 本批仅新增宿主、侧请求、MPEG-H 双 ABI 源码编译/ELF/JNI 证据；未原样重复 45596644795 或此前 14 个公开 AAR 构建。FFmpeg 消费端来源锁已取得精确 producer/commit/ABI 摘要，但旧 run/artifacts API 404，没有拿到匹配的制品。完整 MPV、FFmpeg、Libass、ISO/CMG 等定制合同、Activity 与播放器全量链接、真机待机/解码/回放仍待完成。稳定 Xray Core 仍保留已验证的现有版本，未绕过旧分享导入与配置兼容门禁。
- 本批三次验收均已结束，删除自己的 94 临时 workflow；不修改冻结版发版、签名、主线或其他会话的工作流。不把局部通过标记为 5.9.0 双 ABI APK 可交付。

### 12. 5.9.0 Live EPG 与 VOD 播放身份接线候选

固定公开 5.9.0 的 LiveApi、EpgParser、LiveViewModel、VodPlaybackHost、VodPlaybackController、VodPlaybackMedia，以输入/输出 blob 锁定的最小移植。EPG 保留新版 XMLTV 时间/别名/排序、临时下载/校验/缓存、三日查询与回看 Auth；只有显式播放 client 才改走当前 client 和 metadata tag，普通调用仍使用原下载及 OkHttp.string。LiveViewModel 保留新版 Notify 错误和 TaskRunner，TV owner 对 URL、XML、EPG 在主线程再次核验代际并在取消时退役，普通宿主保留 postValue；cancelUrl 与既有 cancelPlaybackUrl 共用取消入口。VOD 手动切集/线路/源/质量、显式重载与 push 退役旧代理，保留新版解析展开、预载及普通回看逻辑；新增既有 clearPreloadForXray 接口与保留新版 isCurrent 的显式 Danmaku client/请求 ID overload。自动预载过渡及 Activity 实际绑定仍需与 PlayerManager 的代理预载禁止一同验证，不把局部接口当作完整接管。当前仅源锚点与输出摘要验证，待专项目标回归与完整 Android 链接；不改变冻结源码、签名、发布、Core 或旧 ABI 产物。公开 Media3 两分支在本次复核仍为原固定 commit；历史 FFmpeg producer 的 depinfo/download-deps 明确另有移动的 libass/MPV 和其他依赖，现有 consumer manifest 并未固定全部历史输入，不能称历史二进制可重现或补齐定制 TV 5.9 合同。

## 13. 冻结 5.6.3-xray.2 无正式密钥构建与离线签名交接

本节只适用于用户明确授权的单一开发测试分支 `dev/fongmi-upstream-adaptation`。默认 `main` 固定为 `4a52de1daa465d81df7ac06e886a1f184053253c`，仓库实际为 public；正式版本基线、两项业务维护边界及历史黄金证据不变。5.9.0 适配和候选 Core 均未通过完整兼容门禁，不得将其输入用于本次冻结版。三条线的固定 Git 归档引用分别为 `archive/frozen-public-validation-97a23d8`、`archive/fongmi-upstream-adaptation-e3fec17`、`archive/xray-core-stable-eb03202`。归档 tag 不是正式 Release。正式签名及发布必须独立验收。

### 手动验证入口与可复现性

在已有的 01 workflow 入口选择开发分支与 `task=frozen-signing-handoff`；它独立调用 `.github/workflows/04-frozen-signing-handoff.yml`（仅 `workflow_call`，无 push、marker 或定时触发），默认 task=none 不构建。上游验证仅在显式选择 `upstream-adaptation` 时运行。02/03 的开发分支 job 强制禁用。可使用 GitHub Actions 的 Run workflow，或在已授权的本地 GitHub CLI 中执行：

```sh
gh workflow run '01-当前源码编译与APK验证.yml' \
  --repo rileyaaa/FingMi-Xray --ref dev/fongmi-upstream-adaptation \
  -f task=frozen-signing-handoff
```

只有交接产物已失效或确有新的验收需求才启动，不为确认旧证据重复运行。入口只检出固定源码 `97a23d8fc2163c2c2b277e6c0e86a595a4638fa2`、tree `9a166475155cb5a897627fef6838f965e74afd5f`，回读归档 tag，检查 1522 个锁定 blob；不依赖冻结分支名存在。既有测试签名构建 [45547887003](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45547887003) 和无签名交接构建 [45570721364](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45570721364) 均通过；后者实际 workflow commit 为 `4b3fa6fc481c8bf84b02026276abeb9f627813ff`。手动分发入口的调整不等于重新构建或验证新的 APK。

### 已验交接产物（2026-11-25）

Artifact [15001953802](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45570721364/artifacts/15001953802) 名称 `unsigned-frozen-563002-45570721364`，126799059 字节，外层 ZIP SHA-256 `35fbda2824f2770a5b63bba6134be62f7a95e15ded2e868c5e504c728a5a41d0`，有效期截至 2026-12-09 07:57:23 UTC。它是待原签名验收的短期交接区，不是 Release 或长期备份；签名前下载并核对，不因清理临时分支而删除。

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| unsigned/leanback-arm64_v8a.apk | 133296011 | b9078a2c0a1f3d8f2660134c0e5d1dc4005d3dd640dcf0be20e71792cf3bffb4 |
| unsigned/leanback-armeabi_v7a.apk | 117813443 | 5ba80da9a2482590370f2f4d0ab94f1f0b93b72fe23ef6b879895210b9f4eae9 |
| PAYLOAD_SHA256.json | — | 1a8922b7058dc400456a1c7ff6771498cfce93585955194aadb9736b33b68986 |
| verify_handoff.py | — | b4ea23f224a0321337b987bdbb96a49db8a8d491116a7782979d43a4358ddaee |
| BUILD_RESULT.txt | — | c8b9ae74856d1e8ca24e0eb9b0d2ee383ab215d0de9bc3d7769b271ec137bd38 |
| media3-linkage.json | — | c59bb357e1e0b9ced36af91df15693f3928bcecd2d04873765db0353df264f29 |
| README.md | — | 0908d2c58fd03f7cdf88079ad62387beb41e66a5cc2797787ff4922b65e51420 |

上述摘要来自真实构建日志的 SHA256SUMS 清单，外层 ZIP digest 来自 GitHub Artifact 元数据；下载后还需核验实际字节。包内共八个文件（含 SHA256SUMS）。双 ABI 包名、v5.6.3-xray.2/563002、内嵌 revision、单 ABI、16 KB 对齐、非签名 ZIP 条目内容和压缩方式、无 v1/Signing Block、Xray/FFmpeg/MPEG-H/Libass PT_LOAD、三份 DEX 中 46 个 Media3 类型、XrayService exported=false/process=:xray 和 14 项 Manifest 权限检查全部通过。测试签名 APK 与一次性测试 key 已在 runner 清理；无签名候选不可安装。未完成真实正式签名、真机覆盖安装与实际播放/TV 待机恢复验收。冻结版本的历史输入不等于全源码、逐字节可重复构建。

### 正式签名与 Release 门禁

旧 .1 双 ABI 实际公开证书 SHA-256：`3cd86f4fdf6044e7e60307624bf0d8c892dfd83b81ce21748504fcbba28763c2`，包名 com.fongmi.android.tv，versionCode 563001。用户指定使用原签名而非新证书。2026-11-25 用户最新明确授权同仓既有开发分支使用冻结 main 原签名文件与配置对这批已验候选执行一次性签名，不要求用户另行离线签名。签名材料仅在同仓临时 runner 通过原路径使用，不能输出、重新提交、导出或进入日志、聊天、Artifact、Release；不扩大权限。无正式密钥构建流程继续独立，不接触原签名。实际仓库为 public，不能宣称签名材料未公开或已恢复保密。原 `publish-current-release.py` 的 `private is True` 安全门禁不变；公开仓库正式发布被阻止时保留已验候选，禁止绕过。

正式签名环境解压交接 ZIP，使用 Android SDK build-tools 37.0.0、cmdline-tools/latest、Python 3。只签已固定摘要的两个无签名候选，先检查原 keystore 的 DER 公开证书 SHA-256，严格匹配 .1。一次性同仓签名复用原 `check-release-signing.py`、配置字段和交接验证脚本；由子进程环境传递密码而非输出。以下为非秘密验证入口（离线使用时亦适用）：

```sh
sha256sum -c SHA256SUMS
python3 verify_handoff.py --handoff . --sdk "$ANDROID_HOME"
# 使用原签名，产物置于 signed/，不修改签名后的 APK。
python3 verify_handoff.py --handoff . --signed-dir signed --sdk "$ANDROID_HOME"
```

验收只需正式签名 APK、最终文件 SHA-256、公开签名与校验记录；禁止返回签名凭证。用对应 ABI 真机在保留 .1 数据的条件下 `adb install -r`，不卸载旧版冒充覆盖；实际测试范围必须如实记录。正式 .2 仅在通过验收后按用户授权发布 GitHub Releases 一次（非 draft、非 prerelease），tag 与版本名一致、仅 APK，原 .1 不同名覆盖，旧资产按用户最新保留要求处理；不自动清理旧 Release，不发布试签或无签名包，不改 main。待签名交接仍需保留远端 Artifact，但原冻结分支可通过归档 tag 与固定 commit 完整复现，不是继续保留第三分支的理由。

### 5.9.0 基础播放宿主与 TV 资源独立验收

- AC 45641018729 / job 139299361569（fc7f9553）：19 项实际候选 Java 方法断言及三个负向对照；75 个移植/干净合并、25 个未解冲突、5 个旧媒体待审。临时 95 已由 10db6b8b 删除，测试保留。
- 11346fe3 固定八个原冲突路径的输入/输出 blob。PlaybackActivity 保留新版 binding 替换、Web/PiP/DiscMenu、输出绑定及 LiveDanmaku 分发；补旧 TV Xray owner 退役钩子、当前 native owner URL 通知、播放 client 选择和主动挂起时静态/直播弹幕源拒绝。VideoViewModel 只恢复 DETAIL/PLAYBACK/PRELOAD 三 lane 的 Xray 过渡取消，不调用 stopSearch，不覆盖新版 resolve/quality/builtin。Action 只恢复旧手机输入两入口，保留新版 sync/refresh/文件及控制响应。三语字符串及 Live 控制列只追加原 Xray 元素，Leanback Manifest 恢复 SettingXrayActivity，继续排除 BootReceiver/RECEIVE_BOOT_COMPLETED。
- AC 45647615337 / job 139322767826（11346fe3）真实候选 82 个移植/干净合并、18 个未解冲突、5 个旧媒体待审；18 项方法断言、四项负向对照、XML 结构保留通过。Android/Media3 用确定性 JVM 边界，不宣称 Android aapt/ART 或完整 APK。保留 test-upstream-owner-resources.py，删除临时 96。实际 Leanback Live/Video、Setting、手机前端、主 Manifest 的自更新/模块安装分离与 MPV 宿主仍待移植。

### 稳定 Core 与可重建依赖边界复核

- 2026-11-25 核对正式 XTLS/libXray、Xray-core 最新均 v26.11.9，仍为原候选。独立历史 AC 45544415939 job 138970443908（v7）与 138970444230（arm64）实际相同：v2 导入 0/26，v3 23/26，exact golden 0/26，旧 runtime config 校验 26/26、本地生命周期成功。缺 TLS/Hysteria2 TOFU probe；旧可用 vmess-kcp-wireguard-seed、vmess-qr-ws、vmess-qr-grpc 被拒绝。
- 新的源码定位：XTLS/libXray@5a0f7d8d1c28b34afb5727b04b26a10f6dbac7e3 的 invoke.go blob 50e83024088f6ff30ff87d8a643631de814b80bc 只接受 API 3，dispatcher 无两个旧 probe；share/parse_share.go blob 0ef5bf6f3f2638ea1efcf89ff99de0c392fc90ac 用 url.Parse 后按 scheme 分派，vmessOutbound 取 hostname/port，没有旧 VMess QR JSON 专门分支；share/convert_share.go b14546d057f3bad164fe25d5e472c2700218ae65 对投影 outbound 做 buildable filter，share/transport_build.go 00d06c4d01277ff51faba8a43145d5607b2b5c59 的 KCP 传输字段只有 mtu/tti 并另用 fm 表达 FinalMask。当前 LibXrayBridge 固定 API 2 并校验两个 64 hex 指纹。不得仅替换版本号、跳过 TOFU 或丢旧 KCP seed 字段；当前 Core 保留 v26.7.28。没有重复已失败候选，也没有建立新 Core 可替换证据。
- 14 个已验公开 AAR 与上一轮 MPEG-H 独立双 ABI JNI 不是完整播放器。此次单独新门禁 rebuild_public_mpegh_aar.py 以固定公开 FongMi/media + Fraunhofer r3.0.2 实际 Gradle lib-decoder-mpegh:assembleRelease，按 TV API 24、NDK 29、CMake 3.22.1、双 ABI 与原有 16 KB 约束生成临时完整 AAR；仅改变 runner 本地 Gradle 构建约束，未改 native 源。检查编译后的 Java class/native 方法、AAR 内准确两个 ABI JNI、动态依赖与 ELF 对齐，不部署、不上传、不声称专利许可或完整定制 TV 兼容。实际结果等待新 AC。
- 定制 MPV/FFmpeg/Libass/ISO/CMG 等缺件未被替换，历史 FFmpeg consumer 依赖 manifest 不是可取得 producer artifact。主线、正式 workflow、签名及 Release 不改。

### 5.9.0 实际播放器宿主与原生依赖边界

- 2026-11-25：b2076728 AC 45653208817 job 139342903885，MPEG-H source-only AAR 791681 bytes / SHA-256 80883a31661ec8c84a09e7a85a0a4fcf6441b95aba6c82d5fc2f306d8f3da995；两 ABI PT_LOAD 等于新 CMake 产物，7 Java 类/16 JNI 方法；job 139342904259 设置/手机/Logo 9 断言及三个负向对照通过，90 合并/12 冲突/5 旧媒体待审。不重复构建；98 临时入口已删除。
- b82777f9 AC 45665092625 job 139384988605：21 VOD/引擎断言及四个负向对照通过，92 合并/10 冲突/5 旧媒体待审。真实 5.9 VideoActivity 保持 Web、DiscMenu 和 external result；代理请求要求当前 owner、有效 client，普通初次弹幕请求仍在新 key 生效之前发起；引擎变更通知旧 owner；99 临时入口删除。
- 本次新 LiveActivity 规则沿用旧自动匹配与 pending START 状态机，保留上游 LiveInput、Web 分流/导航、seek/end 及 binding 重领。独立测试待 AC；不能以方法级测试代替 Android/ART 和真实电视待机验证。

#### 公开播放器源树与可重建性复核（不是 APK 工件回填）

- 5.9 TV 固定 d3a0b84b24cf6628d72a4dbc2be453875b005536，app/libs 只有 hook-release.aar（179856a41a3e03ce569f00a66b8a82ca1071830c）与 tvbus-release.aar（2fda22082087a1702436717c72efe05b65efe5ca）。两公开 FongMi/media 分支仍为 3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d 与 2bc207851df311340767e913931ca7b28cab1794；完整递归树均没有 MpvDecoderMode、SubtitleOffsets、SubtitleSelectionState、SubtitleContent、DecoderMode、DecoderManager、FfmpegMotionInterpolationController、DiscMenuController 类型，不能仅用 Maven/公开 AAR 混合替代。既有全量源门禁分别缺 50/66 个导入，保留该结果。
- TV MpvPlayerEngine blob cdd833c714e878850c2a192d1fe426c3f0b5a532 需要 MpvPlayer.VideoOutputOption、getSubtitleOffsets/setSubtitleOffsets、getSubtitleSelectionState、setSubtitleContentEnabled、setVideoDecoderMode、setDiscDataSourceFactory；TV MpvUtil blob 23a5812369a20c978b4cd7015af31c0cbb6a16f1 需要 builder.setVideoDecoderMode、setDataSourceFactory、setDefaultFontDirectories 等。公开 fork MpvPlayer.java blob 773b1560def27c628974a498dab3de6e8cc1e58f 仍有旧 setDecode(@C.DecodeMode int)，MpvPlayerConfig.java blob 3cb8359f28475fb098305ab58b7121000627f59e 不提供所需新 builder 契约。不能用删除双字幕/光盘/输出功能来编译。
- 公开 Media3 MPV module 有 Java wrapper（is/xyz/mpv/MPVLib.java blob 36da8033843061ffbcbf560ed77566ffdca4dd98），src/main/jni 无 native producer，src/main/jniLibs 有两 ABI 的 libmpv/libplayer/libc++_shared。公开 FongMi/mpv-android@99a60ad2141d5ace94453590903c2c6b9a0a2443 的 app/src/main/jni/Android.mk blob 4625e17cf396942b93571b2c4cfe42f2d6d4d4f3 实际编译 libplayer（main/render/request/log/jni_utils/property/event/thumbnail），关联 MPVLib.kt blob b8aa805de2c3df58c7ba8c11cefba0d5cda78eaa，因此存在低层 glue 源码候选，但不证明当前 5.9 定制 Java/Native 接口。历史 producer AC 31346106984 已不可获取；depinfo.sh blob ffe432a904fc1f765068fa29a3ffb1a666c5d291 仍包含 moving libass/dav1d 等依赖，完整历史产物无损重建尚未证成。当前 fongmi 分支 c92728c62336070c191032f22ba7473d95f276d2 不是历史 manifest producer。
- 公开 Media3 FFmpeg 并非没有 JNI 源：CMakeLists.txt blob 086fe3a78b1c6f7dcb70faf133e8fa22e4b83479 编译 ffmain/ffcommon/ffaudio/ffvideo/ffvideo_frame/ffvideo_gles/ffvideo_libav/ffvideo_placebo，依赖固定 headers、两 ABI avutil/swresample/avcodec/avformat.so 与 libplacebo.a。native-dependencies.properties blob ec9f8c76c66cdf5b50bdf4bf031cfab51f336551 记录 FFmpeg 04482c8d13ac27b2a9fe93f5d388929eef8af5f4、dav1d 54706fc6bc0cdecab7e9593974a4039cc038fca7、libplacebo 04b3a0918fb32b8f374193aaead8b509274aae97、NDK 29.0.14206865，且 14 个 .so 与 renderer SDK 有 SHA-256。旧 build_ffmpeg.sh blob e0a9aa4f8441fbaf67d7a0d7c20043ae96261c30 使用 static/disable-avformat/disable-avfilter，不等价于当前 CMake 共享库和视频 renderer 合同。可进一步独立核验并重编公开 JNI，但不能声称已重建所有 producer 依赖或匹配 5.9 私有/未公开定制接口。
- 不从 Release APK 反提取，不使用未知来源二进制，不替换 v26.7.28 Core；新 Core 仍须旧 API/导入、分享和播放安全契约通过。完整双 ABI APK 尚不可交付。

### 5.9.0 公开 FFmpeg JNI 与 Android 恢复集成

- Live AC 45665943884 / job 139387994121（8874b467）成功：21 断言、四个负向对照、93 已移植/9 冲突/5 旧媒体待审。100 临时入口移除，不重跑。
- FFmpeg 门禁固定公开 consumer tree 67a7cc5cee292c022b7837d3b78d4dd500b3c6e0、manifest ec9f8c76c66cdf5b50bdf4bf031cfab51f336551、NDK 29.0.14206865/CMake 3.22.1/API24；逐 ABI 审计七共享库、libplacebo.a、headers 清单和 license，实际编译原始 CMake ffmpegJNI（audio/video/renderer 均保留）并审核 22 JNI 导出、ELF、16KB、动态依赖闭包。仅 JNI 新编译，公开 consumer 中的 native 依赖并非本次 producer 重建；不部署、不上传、不宣称完整 AAR/运行解码或许可证已清除。
- 5.9 OkProxySelector 已以 HttpUrl 保存 scheme/host/port，覆盖旧 fork 的 URI host null 修复；保留实际 loopback 测试，仅适配新签名。Jar/Js/Py loader 新版统一 SpiderLoader 代际：clear 取消 pending、关闭 Spider 网络/JS/dialog、清理 subclass 引用；destroy 在最终退出执行。沿用新版，不恢复旧强制 early-destroy 迴圈；第三方 Spider 自定义 destroy-only 行为仍无真机/真实插件覆盖证据。
- 新集成门禁使用实际 staged catvod/tv-recovery Android Gradle 编译、Robolectric Application 生命周期与实际 OkHttp/独立 Xray client、完整上游 SpiderLoader/真实 Spider 及 loopback HTTP 回归。Hook/Renderer 有测试边界，完整 Home/Activity、真实电视网络/播放/runtime 插件仍须匹配定制 Media3 后验收。5.9 runtime 安装需要 REQUEST_INSTALL_PACKAGES，与冻结版 manifest 禁止权限策略冲突；本批不自行放宽。

- 4581baf2 AC 45672262184：job 139410395263 在 renderer LICENSE 的 SHA-256 前置检查停止，没有编译；consumer/producer（FongMi/libplacebo@04b3a0918）同一 LGPL-2.1 Git blob 20fb9c7da21cb5a29e10f614a03661a935181652，LF checkout b3aa400aca6d2ba1f0bd03bd98d03d1fe7489a3bbb26969d72016360af8a5c9d，规范 CRLF 后恰为 manifest 575888be9ac31801886babca6456e1beb346fa4fb3dd76f52111f8048e38d58a。仅固定文本 LF/CRLF 等价可核验；所有二进制必须逐字节匹配 SHA-256。job 139410394790 在 SDK 安装停止，未编译；恢复已成功 #45608824619 使用的 SDK 精确入口 --channel=3 platforms;android-37.0，未降低 compileSdk。
- 新候选保留完整 FongMiNetworkRecovery 与 Leanback TvDlnaLifecycle 的 Android 编译和 Robolectric 回归；App 主线程调度、DLNA service、Glide failure-reset、BaseLoader completion 为明确测试边界，真实 catvod/OkHttp 与 Xray client、生命周期/协调器及上游 SpiderLoader 另外完整执行。不能代替完整 Home/真实 TV/插件/播放器。
- Updater 候选仅保留 5.9 runtime module 通知和 transferText 原方法，应用 APK 检查/下载/安装回调 no-op，版本行非更新入口；RuntimeInstaller 不改。主 Manifest 仍是明确冲突：旧 fork 明文禁用 REQUEST_INSTALL_PACKAGES，5.9 独立 runtime 安装要求该权限；不自行放宽权限，也不删除正常 runtime 功能，不把当前候选当可交付 APK。旧 app/utils/Download 已被实际 catvod 下载器替代（#45608824619），不恢复旧类，检查候选无引用。101 临时触发移除。

#### FFmpeg JNI 独立重建实际结果与 Android 恢复测试编译边界

AC [45672857780](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45672857780)，固定 commit `cd36649801e306b8f9bb98d7ebf1ff31c8732232`。FFmpeg job 139412494231 success：实际 CMake 编译并链接 `ffmpegJNI`，每 ABI 7 个锁定公开共享库、34 个 renderer headers 与 libplacebo archive 通过输入审计；文本 LF/CRLF 等价需匹配 manifest 摘要，二进制摘要无例外。

| ABI | libffmpegJNI.so bytes | SHA-256 | JNI | PT_LOAD |
| --- | ---: | --- | ---: | ---: |
| armeabi-v7a | 1962072 | `7bc0b2d12c127d5d29f8636d6028cee2b31b9853bb156a83af38d1d126a6004e` | 22 | 3 |
| arm64-v8a | 2138256 | `735d5dbdf3acb744df1d6613fe964c69035d2765a0e08692b64954b7d85a0f32` | 22 | 3 |

两个 ABI 的新 JNI 与固定输入 ELF 均通过 16KB 最低对齐、SONAME 和动态依赖闭包检查；JNI_OnLoad 存在。历史 producer 依赖未重建，临时 JNI 输出非发布制品，不声称完整 AAR、APK、运行时解码或分发权已验收。

settings-boundary job 139412494163 success：实际 staged 应用更新空壳、runtime 模块通知、删除旧 Download 接线验证通过；2 unresolved / 5 old-media-review。主 Manifest 安装权限策略与 MPV 定制接口仍阻塞。

recovery-integration job 139412493675 failure：SDK 37.0 安装成功；`:tv-recovery:assembleDebug` 与 `:catvod:assembleDebug` 完成；`:catvod:compileDebugUnitTestJavaWithJavac` 在 UpstreamRecoveryAdapterTest.java:51 的 `Shadows.shadowOf(Looper.getMainLooper())` 多载解析报告 `android.hardware.fingerprint.FingerprintManager` 不存在。测试尚未运行，不能标记恢复集成成功。后续仅将两份新增恢复测试改为显式 `ShadowLooper` + `Shadow.extract`，不改断言、compileSdk、实际宿主源或边界；只重新执行恢复集成，不重新执行 FFmpeg、设置、Live、VOD 或 MPEG-H。

#### 5.9.0 适配停止门禁与恢复集成隔离（2026-11-26）

- [45673349061](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45673349061)（90dcb786，job 139414225176）：两个实际 Android debug library assemble 及 Java 测试编译成功；19 项运行，18 通过、1 失败。首个失败是 `UpstreamRecoveryIntegrationTest.standbyGenerationReplacesApiButNotPlayerOrBoundTransport` 第 36 行首次 renderer start 次数；尚未执行该测试后续待机代际与绑定 transport 断言。
- 现有产品生命周期是进程级 singleton；Robolectric 同 SDK/配置可复用 sandbox，独立测试 Application 可能继承上一测试的 singleton。ac426940 仅修改专项临时 Gradle 测试工程（每个测试类独立 JVM）和两份测试的只读初始状态断言；不重置产品 singleton、不改产品代码、不减少原断言。XML 门禁固定 16+1+1+1 项，零失败、零错误、零跳过。103 一次性入口已移除。后续独立 JVM 的原断言全部通过，支持测试 Application 与进程 singleton 隔离不足的判断；未改变产品逻辑。
- [45689744405](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45689744405) attempt 1（ac426940，job 139471731398）：两 Android library assemble 和 Java 测试编译成功，`:catvod:debugUnitTestRuntimeClasspath` 从官方 Maven Central 下载 `org.robolectric:nativeruntime-dist-compat:1.0.18` JAR 遇 HTTP 429，未运行任何断言。冷却约 29 分钟后仅重试该失败 job 一次；固定来源、版本、校验规则和原断言均不变。
- [45689744405 attempt 2](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45689744405/attempts/2)（同一 ac426940，job [139488892555](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45689744405/job/139488892555)）completed/success：2026-11-25 20:26:38 UTC `BUILD SUCCESSFUL in 1m 30s`。四类 XML 门禁实际通过：`OkProxySelectorTest` 16/16、`UpstreamRecoveryIntegrationTest` 1/1、`UpstreamSpiderLifecycleTest` 1/1、`UpstreamRecoveryAdapterTest` 1/1，共 19/19，零失败、零错误、零跳过。`:catvod:assembleDebug`、`:tv-recovery:assembleDebug`、`:catvod:compileDebugUnitTestJavaWithJavac`、`:catvod:testDebugUnitTest` 均成功；实际 debug AAR 大小分别为 catvod 254606 bytes、tv-recovery 6920 bytes。`REMAINING_SCOPE 2 unresolved 5 old-media-review`：主 Manifest 和 MpvPlayerEngine 冲突、五个旧媒体待审项仍在。此验收覆盖实际 Android library、Robolectric 恢复生命周期、上游 SpiderLoader 与真实 loopback HTTP，不代表完整 TV 宿主、APK 或真机验收。104 一次性入口在本收尾提交移除，历史 run/job 保留；不再触发 AC。复现入口仍为 `scripts/upstream-adaptation/verify_android_recovery_integration.py --old-tv <fixed-5.6.3-checkout> --tv <fixed-5.9.0-checkout>`，使用锁定浅 checkout、Java 21、SDK 37.0。

**5.9.0 当前不可发布，依赖恢复条件：** 2026-11-26 再读完整未截断的公开 Media3 树（release-1.11.0-fongmi：3c2cbe8a / 9123 entries；release：2bc20785 / 8613 entries），上述 50/66 import 缺口依然有效；两树均无 MpvDecoderMode、SubtitleOffsets、SubtitleSelectionState、SubtitleContent、DecoderMode、DecoderManager、FfmpegMotionInterpolationController、FfmpegMotionRenderersFactory、DiscMenuController、IsoNavigationPlayerController、LibassSubtitleController 的 Java/Kotlin 类型文件。TV 仍为 d3a0b84b，app/libs 仅 hook/tvbus 两 AAR；MPV Java 宿主实际调用 setVideoDecoderMode、setDiscDataSourceFactory、getSubtitleOffsets、setSubtitleContentEnabled 等，新版 MPV builder 亦要求 setDataSourceFactory、setDefaultFontDirectories。FFmpeg 公开 JNI 独立重建和 MPEG-H 双 ABI 已通过，不能代替 5.9.0 定制 FFmpeg/MPV 完整 AAR、特定 native 接口与 producer 链路。公开 FFmpeg 9.1/9.0 和 mpv-android 分支未更新，暂无新的完整匹配来源；本次不再重复上述已验门禁。

恢复适配须同时满足：取得可追溯、合法、版本配套的定制 Media3/MPV/FFmpeg Java/JNI、native 依赖和构建/分发合同（含 libass、ISO/光盘、字幕与正常上游音视频能力，以及 12.3 所列 runtime 依赖）；解决主 Manifest 的 REQUEST_INSTALL_PACKAGES 与 fork 禁止上游自更新的权限边界且保全正常模块安装，不自行扩大权限；解决 MpvPlayerEngine 接线及五个旧媒体待审项；实际编译完整 Leanback ARMv7/ARM64 APK，检查 ABI、ELF/动态依赖、16 KB、Manifest、全部宿主链接，再在真实电视验证普通播放、直播/VOD 当前 owner、字幕/旁路、待机和网络恢复。Robolectric/边界 fixture 仅覆盖所列测试，不等于上述 APK 与真机门禁。禁止从旧/新 APK 回填未公开实现、空壳接口或删减正常功能。

XTLS/libXray 与 Xray-core 当前正式 latest 仍是 v26.11.9，无新的 API 2/旧导入与分享、TOFU 及单一播放等价证据（旧 23/26 不是通过）；保留 v26.7.28。5.6.3-xray.2 仍是当前正式版，main f03faa5d 冻结；本次仅在 dev/fongmi-upstream-adaptation 留存测试与证据，不发布、不改签名或 Actions 历史。

#### 5.9.0 扩大公开来源核验（2026-11-26，再开启）

本节更新前述“暂无新的完整匹配来源”的具体证据；不是宣布 5.9.0 依赖已恢复。仍锁定 TV d3a0b84b、现有 fork 适配候选与原发布门禁。

**定制 Java/consumer 搜索及排除：**

- [Diaojiangjun/media](https://github.com/Diaojiangjun/media/tree/e9b5847ce6c16ec40536e0ec70cf7011391a4a9c) 与 [suxlsbz/media](https://github.com/suxlsbz/media/tree/e9b5847ce6c16ec40536e0ec70cf7011391a4a9c) 为相同 commit e9b5847ce6c16ec40536e0ec70cf7011391a4a9c，完整 tree 4369f8c21fc8c818096ef9b676194af40517890b / 9202 entries。65/66 个历史缺口 import 行可找到外层类型文件，仍无 androidx.media3.common.text.SubtitleFontFile；这不是 javac 或行为通过。11-19 的新增 commit 8d6bd33442c92d3d3bcff2dabe30a792c9fb91b3 引入大量 TV API 及 native prebuilts。实际 FfmpegMotionInterpolationController（blob 0f839574dd021320ef1d9d6eac081e517ce923f6）固定返回 unsupported/INACTIVE，IsoNavigationPlayerController（da7e1853ce88a6af1b55ab6c8ef35e8f15dc68a7）不建立 ISO 导航源、回报 RUNTIME_MISSING，LibassSubtitleController（6ec1618d3af0ef7fe77dfed80155252cd9243024）保留状态不足以证明实际副字幕输出。拒绝以这些空壳替代上游功能。Yuhaitao-920/fongmi-tv-589 的 from-source workflow 使用同一来源并有额外宿主/签名校验改动，不能作为本项目 5.9.0 等价证据。
- [dlgt7/media](https://github.com/dlgt7/media/tree/3382803f11e129af8676a0a775f98293b079797f) 完整 tree 4cc0071aa7b7b30e7dd73a476c10d2b72a94b7f8 / 9201 entries，较官方基线 63 commits。60/66 历史 import 行找到外层类型文件；缺 SubtitleFontFile、TrackSelectionUtil、FfmpegMotionInterpolationController（含两个 nested imports）、FfmpegMotionRenderersFactory。ISO controller（96592e430334446991e883eb456d975eaa8d881f）确有 session/open/menu 流程，IsoNavigationSession（25aec0adb0ba060391d8630dfead44b5987ad9b6）要求 isoJNI；LibassSubtitleController（a4ada8bb791992e88c283659f2506203b82af858）调用选择器和副字幕格式，LibassLibrary（6ec82056ee170094557d4a31d606ef424be56159）加载 media3ass。完整树查无对应 isoJNI/libmedia3ass SO 或相关 C/C++ JNI producer。FFmpeg/MPV 原生输入仍属旧基线；新增源码大量经上传提交，根 Apache LICENSE 与文件头不独立证明全部新增实现来源、完整 native 授权或 5.9.0 合同。两个 fork 的 MPVLib.java blob 同为 36da8033843061ffbcbf560ed77566ffdca4dd98，native 声明不能替代新版 MPV Kotlin bridge 的完整 stream/回调及 Java consumer 联合检查。
- 其他公开树交叉筛查：yangxw8820/fongmi_media、okcaptain/FongMi-Media、NextPlayerCloud/media-fm、webhtv/webhtv、chengxue2020/Fongmi-ExoPlayer 未发现上述 11 个关键新增类型的文件；其他同 tree 镜像不重复计为新实现。FongMi/FongMi、FongMi/Release 未提供缺失 consumer。kukuqi666/TVboxOSC 有其他产品的媒体 AAR 与 MPV 模块，但没有核实匹配源/授权/5.9.0 ABI 合同，未采用；15840213978a/fongmi-android6-main 的 scripts/recover_official_mpv.py（724e6967e13f5c5796e336bab8d2807f63a8bbd2）明确从 APK 读取 libmpv.so，排除该方式。旧 July fork 的媒体 AAR 和 xixu-me/fongmi-tv-actions-builder 亦不补足当前接口。
- 已扩展到历史公开 refs、作者其他项目、公开 Maven/AAR 来源。公开 Maven NextLib (1.11.1-0.18.0 / 1.11.0-0.15.0) 与 io.put:media3-ffmpeg-decoder (1.11.1+1) 为独立 Media3 扩展/音频 decoder，并非已证明 FongMi 定制接口替代；未下载或执行它们。WebHTV 公开 README 及锁定构建说明为旧的 1.11.0-alpha01-fongmi + nextlib 1.10.0-0.12.1 定制体系，独立 native 命名/链接合同，不是新版统一 libffmpeg.so consumer。未确认其他可验证的匹配 AAR；搜索可见范围有限，不宣称互联网不存在相关源码。
- FongMi/bdj-runtime@6b4bed40fc8c65480f4e1bedffbfa3be63dd99c0 README 记录独立 OpenJDK Zero 双 ABI、来源与许可证，但当前连接读取 zero-jdk8u482-r1 与 sources-v1 release tag 均 404、公开 run 列表空，不能据 README 宣称已取得运行时。此 producer 不等同 isoJNI。

**官方 native producer 已实际取得并独立核验（不读取 APK）：**

[FongMi/mpv-android run 44885769496](https://github.com/FongMi/mpv-android/actions/runs/44885769496)（job 136790596601 / success / 2026-11-21），实际 producer commit 1bf892e3271e73d8649f2d209027f1fb17515d15（不是当前 c92728c6）；日志锁定 FFmpeg 963c8cbbebb0250f747f0019516bda55bc638da9、MPV f964d1495355d5c6626df3de1d3eeb90ddee2aba、libplacebo dc98e2fceb82233b3bb75e9c6249e581c57f3f2d、NDK 30.0.16248370。实际 producer ffmpeg.sh blob 90e6de21643a374285a90fdde3a1369b32311451 明确启用 GPL/version3，并以聚合库作为 consumer 输入；MPVLib.kt blob 58656ed251ddec0d07ac416149428cbb22524fc8 有 stream registry 与 openStream、24 native 声明。公共源码和官方 artifact 可追溯，但 depinfo 仍有 dav1d/libass movable refs，尚未重建全套生产链、核定全部分发许可/对应源码。不可仅凭 artifact 来源认定完整许可。

从官方 Actions 下载以下 5 个 ZIP，核对 GitHub API digest、文件长度、CRC（固定摘要写入审计脚本；不是 APK 提取或外部镜像）。前 3 个来自同一成功 run，API 到期时间 2027-02-19T08:37:42Z；后 2 个来自历史 run 44040032853、43415749605，仅作来源交叉比对，不宣称与新版 ABI 混用。

| artifact ID | 内容 | bytes | SHA-256 |
| --- | --- | ---: | --- |
| 14699804350 | mpv-native | 43658512 | f07422157e0f18409084e1bf50352f142d56fca2a7cf71802b6e95621cb9d4f4 |
| 14700635872 | renderer-sdk | 14360945 | d05798ac705e10172fd517b0d0ee718c9bb3e2a0073cd5f0d1baf807dbf8e010 |
| 14699869160 | bdj | 2052197 | 3730c648dcf2e6bfa69e59dda68e33414b9201d1485337f685f8571d713888cd |
| 14310565120 | 历史 mpv-native | 43575008 | eb7ebb001bcf7fd2f70f6e8e06d7a109fb64b7daeb5700e05fec1f8ce73fb782 |
| 14032452811 | 历史 mpv-native | 43545891 | f573841e16ae8b15e3022008e5661ba2e149b3ab8354ca8b4f96f70b40b8c58c |

新增独立只读证据入口 scripts/upstream-adaptation/audit_official_native_bundle.py，Python 3.9+、GNU readelf；将上述原始 ZIP 分别命名为 fongmi-mpv-native-14699804350.zip、fongmi-renderer-sdk-14700635872.zip、fongmi-bdj-14699869160.zip、fongmi-mpv-native-14310565120.zip、fongmi-mpv-native-14032452811.zip 后运行 python3 scripts/upstream-adaptation/audit_official_native_bundle.py <zip-directory>。实际本地运行退出 2（固定已核实阻塞，非验收成功）；摘要/结构不符会抛错。入口不安装/执行 native、不下载、不改依赖、不提取 APK、不被发布/AC 自动调用。

| ABI | SO | bytes | SHA-256 | 16 KB |
| --- | --- | ---: | --- | --- |
| arm64-v8a | libffmpeg.so | 24708216 | 499d57009aab55341a3c55a1878f2bce487956003d964c856a346a911df533f8 | PASS |
| arm64-v8a | libmpv.so | 18193632 | d4705cdb3eaa8094e70395bc03623003a9708b17e3ac56742a8fd13606a4941c | PASS |
| arm64-v8a | libplayer.so | 56648 | a5483debe6d8629c11b863a9b5c5a9388882c6b76fbda08bd3109f5e383f82d8 | PASS |
| arm64-v8a | libc++_shared.so | 9485032 | 7466ed097631a564ed6bff0b47768caa76bf03270d2047b5a65c03f497b824df | PASS |
| armeabi-v7a | libffmpeg.so | 22151940 | c0a494b0e53971e3b79c5375b0d6e661bb6b4688a6fa50a577c6ae5cba960f1f | PASS |
| armeabi-v7a | libmpv.so | 14960592 | 93e73e8d16f4549a6e8d8ab2499a95d876a90a20997ccc56c9a161574a78f642 | PASS |
| armeabi-v7a | libplayer.so | 40972 | 9a1f5ba2556c15f312d63c2e6f0f90aae9b615c361b7e5dcb82ada405663334d | FAIL (0x1000) |
| armeabi-v7a | libc++_shared.so | 7567040 | 2ee592c9ba3372da027384deb1070def5ae76f3ea2246bd447360faa73ac22f4 | FAIL (0x1000) |

8/8 ELF ABI、DYN、SONAME、DT_NEEDED 文件集合检查通过，无 RPATH/RUNPATH/TEXTREL。每 ABI 1151 个版本化 FFmpeg 导出，libmpv 的 278 个 FFmpeg 版本化导入、libplayer 的 5 个 FFmpeg 版本化导入与 21 个 MPV 导入全部在对应导出集合内；24 个 Java_is_xyz_mpv_MPVLib_ JNI 导出名称（不等同 JNI 签名或运行时验证）。renderer SDK 的 87 项 SHA-256 全覆盖、每 ABI 36 headers、motion-build.properties/源 revision/manifest pin 一致，libplacebo API399、OpenGL/Vulkan，6 个静态库的 ELF member machine 正确（每 ABI motion 1、placebo 60、shaderc 239）；BD-J 2 JAR 内部 CRC/class 文件、4 个静态 archive 的 ABI 成员均通过（每 ABI libbluray 55、libfreetype 43）。未链接完整 consumer 或运行解码、ISO/BD-J、字幕、Xray。renderer 包中的 LICENSE 及 motion LICENSE/manifest 已核验；不宣称全部 GPL/LGPL 组件分发权与对应源码已齐。

历史来源比对：Diaojiangjun/suxlsbz jniUnified2 的 libffmpeg.so blobs aa8847df15e9ff2203bbc6bb1823865c89ace511 (arm64) / 5521717a7ae75dad5a287e2a9c37ffec66eae073 (armv7) 与官方 11-13 artifact 14032452811 实际字节计算 Git blob 完全相同。其 libplayer.so blobs f7ea3497c0bc59148552d60c3cb9de8ae5e428b5 / 6b455800495f9ad6d2ea676348e55e3820fa2079 与三次官方 native artifact 均相同；其 libmpv.so 未与任一这三份 artifact 字节匹配，不能据此断言不合法或 APK 提取，只能说此比对未建立来源。第三方统一 FFmpeg producer 部分可追溯，不能为其其他 native 或 Java 空壳背书。

**新的精确阻塞与恢复条件**：官方统一 FFmpeg/MPV/renderer producer 不再是完全未知，但 ARMv7 libplayer/libc++_shared 未通过既有 16KB 门禁；需要对固定 producer 源和 toolchain 修正/重建匹配的 ARMv7 输入，核定所有 native 来源和授权，不能直接用当前 ZIP 或不同日期/ABI 产物混装。缺少保全功能的 5.9.0 consumer Java/JNI（含定制 libffmpegJNI、libffmpegDoviJNI、isoJNI、media3ass、补帧、字幕、光盘），已找到的 producer motion 静态库不能替代 FFmpeg consumer renderer/controller。仍需解决 Manifest 安装权限边界、MpvPlayerEngine 及五项旧媒体待审，完整宿主编译/双 ABI APK/真实设备门禁不变。当前无满足全部条件的候选，不将审计脚本接入构建，不移植空壳、不删功能；没有重新执行 19 项已通过集成或其他 AC，没有触碰 main/Release/签名/历史，Core 保留 v26.7.28。仅将新的可复查证据及审计工具提交现有 dev 分支。官方 artifacts 仍留其原仓库，不复制入本仓库。

#### 5.9.0 consumer 合同专项复核（2026-11-26）

只复核上一节已取得的官方 producer 与缺失的 Media3 Java/JNI consumer，不重建 producer、不重复已通过的 19 项恢复集成或其他 AC。TV 仍固定 d3a0b84b，producer 为 1bf892e3271e73d8649f2d209027f1fb17515d15（run 44885769496）。

**页大小口径**：Android NDK 官方 [Build System Maintainers Guide / Page sizes](https://android.googlesource.com/platform/ndk/+/master/docs/BuildSystemMaintainers.md#page-sizes) 明确目前无计划改变 32-bit ABI 的页大小；[Android 16 KB 支持文档](https://developer.android.com/guide/practices/page-sizes) 区分 ELF LOAD 对齐与 APK 未压缩 SO 的 ZIP 对齐。上一节 armeabi-v7a 的 libplayer.so、libc++_shared.so 0x1000 只说明未通过**本项目既有更严的双 ABI ELF 16 KB 门禁**，不能据此判定 Android 平台不兼容。原脚本、断言和 APK 独立 zipalign 校验均不放宽。不为 ARMv7 对齐单独启动 CI；下列 Java/JNI 和授权阻塞与该项互相独立。

**历史官方 Libass 确有源码，但 ABI 不能直接替换新版。** 扩查 FongMi/media 的历史成功 Actions [31571172760](https://github.com/FongMi/media/actions/runs/31571172760) / [31570623136](https://github.com/FongMi/media/actions/runs/31570623136)，源码分别为 9dae39e9689ee305c83f94bd11cf3bcecb9d6171 / 32c122e4ea364fe2a13d8dc988fcdaeed2290f04；两个完整树均 9166 entries、未截断，含相同 libraries/exoplayer_libass tree eaea6cd65ec894fd0233d4d396f0b2f995586d60。job 94033300824 / 94031630081 的 Test, lint, and assemble、Verify native AAR、Upload AAR 步骤均 success；但当前 Artifact 列表为空，首个 job 原日志读取 HTTP 410，未重新取得或检查历史二进制。当前固定 3c2cbe8 树不含该模块；历史提交与当前树已分叉，不能称新版源码。

- 官方历史 [media3ass.c](https://github.com/FongMi/media/blob/9dae39e9689ee305c83f94bd11cf3bcecb9d6171/libraries/exoplayer_libass/src/main/jni/media3ass.c) blob 949c5b0db7ca8a5867e52e895920518d82651376，真实 libass 渲染、JNI_OnLoad/注册表，Apache-2.0 文件头；CMake blob 4c3c4cc3a6971172643e7d41174c969b496d8d77，双 ABI，max-page-size=16384，链接固定 libass/fontconfig/expat/harfbuzz/freetype/fribidi/unibreak。.gitmodules 指向 peerless2012/libass-cmake 固定 gitlink d3f00a43ca66e42a2c34de964b1a7dbbfa9dbc8b；其 LICENSE blob 437dfc3de7d64d9f7998e87e893b561d3f6e1e24 为 MIT，完整树有七个固定 gitlink：ass bbb3c7f1570a4a021e52683f3fbdf74fe492ae84，expat f9a3eeb3e09fbea04b1c451ffc422ab2f1e45744，fontconfig daa175d234b8a362eedd4c18c33537cc2d19cd98，freetype 42608f77f20749dd6ddc9e0536788eaad70ea4b5，fribidi 68162babff4f39c4e2dc164a5e825af93bda9983，harfbuzz c3fcbffa651cea70400552f2a8bd695ad11023c1，unibreak 304585d8e2d63187507368d612c3d5fff1486368。历史 workflow 检查八个 license entries。仅证明历史 wrapper/build recipe 的来源和授权标识；没有重新审核七个组件全部分发条款或验证新版组合。
- 将上述 C 注册表逐项解析，与 [dlgt7 LibassNative.java](https://github.com/dlgt7/media/blob/3382803f11e129af8676a0a775f98293b079797f/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/libass/LibassNative.java) blob a08a6b94b48f2582048dda07ae6ffebf8c801dc2 的 Java 声明转换为 JNI descriptors 后比较：旧 12 项、新 18 项，仅 7 项名称/descriptor 相同（仍不是语义通过），4 项同名但签名不同，1 项旧有方法 nativeFlushEvents 已不存在，新版独有 7 项。新版独有：nativeCreateLibrary、nativeReleaseLibrary、nativeProcessTimedData、nativeSetBottomPositionFraction、nativeSetFonts、nativeSetStyleOverride、nativeSetVideoColorInfo。旧 JNI_OnLoad 必须 RegisterNatives 成功，因此直接拼接会在注册阶段失败，不是简单的库名或缺 SO 问题。
  | 方法 | 历史 descriptor | 新候选 descriptor |
  | --- | --- | --- |
  | nativeCreate | (Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)J | (JLjava/lang/String;Ljava/lang/String;)J |
  | nativeSetFrameSize | (JII)V | (JIIIIIID)V |
  | nativeSetFontScale | (JF)V | (JFZ)V |
  | nativeRenderFrame | (JJ)Landroidx/media3/exoplayer/libass/LibassFrame; | (JJZZ)Landroidx/media3/exoplayer/libass/LibassFrame; |
  新版 library/track 生命周期和 viewport/颜色/样式/双字幕均须配套，不能删除 native 或用旧签名空壳实现。需取得同版真实 media3ass JNI 与 Java 及其依赖清单。

**MPV：原生 producer 与候选 consumer 有明确初始化阻塞。** 固定 producer MPVLib.kt blob 58656ed251ddec0d07ac416149428cbb22524fc8 的 24 个 native 声明，对比 dlgt7@3382803f 和 Diaojiangjun@e9b5847c 的相同 MPVLib.java blob 36da8033843061ffbcbf560ed77566ffdca4dd98，只有 17 个 native 声明；缺 command、enqueueCommandLongResult、grabThumbnail、setPropertyInt、setPropertyDouble、setPropertyBoolean、setPropertyString。更关键的是固定 producer [stream.cpp](https://github.com/FongMi/mpv-android/blob/1bf892e3271e73d8649f2d209027f1fb17515d15/app/src/main/jni/stream.cpp) blob a4ebe55984fa12de9b0a354da4a98cfcfa634d5d 要求 MPVLib$Stream、静态 openStream(String):Stream 及 read(ByteBuffer)/seek/size/cancel/close，注册 media3iso。main.cpp blob 0abeaf6b3146f41b7fbd9f961aa78f134f7179ce 在 create 时注册失败即 destroy_mpv_context 并返回/抛错；jni_utils.cpp blob 51a1ebfbf69ec871300a281a009f805a925d8f47 还要求 eventCommandReply (JIJ)V。两个 fork 缺 Stream/openStream 及三参数结果回调，不能用已通过 ELF 导出名称的官方 libplayer.so 直接替换。

固定 TV 的 MpvPlayerEngine.java blob cdd833c714e878850c2a192d1fe426c3f0b5a532:300 从当前 spec headers/auth 创建并传入 setDiscDataSourceFactory，MpvUtil.java blob 23a5812369a20c978b4cd7015af31c0cbb6a16f1:154 在 builder 传 setDataSourceFactory/default font directories。两个 fork 的 MpvPlayer（fc694f2e629e898a446f4c43e8b6dc58c4ab268d / 48f24f1da4903c18e0705cd68cb2e945c3b42647）相关字段 setter/ getter 不足以证明真实输入接管；共同 MpvMediaLoader blob 12d67d6d3fd3bb12161450dfc176de5465c0a312:89 仍直接调用 loadFile(uri, options)，无 media3iso 或 stream registry 接线。没有完整 Media3 consumer 与真实 DataSource 生命周期/取消/字幕、认证侧请求的所有权合同，不能把普通 MPV 网络路径改成全局 Xray 或靠放空 factory 编译。

**ISO、FFmpeg 与进一步候选复核：**
- FongMi/bdj-runtime@6b4bed40fc8c65480f4e1bedffbfa3be63dd99c0 的 [probe/IsoNavigationSession.java](https://github.com/FongMi/bdj-runtime/blob/6b4bed40fc8c65480f4e1bedffbfa3be63dd99c0/probe/IsoNavigationSession.java) blob 1020e68a73572ddde3c1dc6e1cb404240475a50d 明示 test facade、无播放器实现；[probe/build_apk.py](https://github.com/FongMi/bdj-runtime/blob/6b4bed40fc8c65480f4e1bedffbfa3be63dd99c0/probe/build_apk.py) blob 65e08e3492a86f52d3e8199a8e71fb9b98e29df2 强制外部 --media-iso-aar，并从该 AAR 读取 jni/{abi}/libisoJNI.so，不构建它。官方 VALIDATION.md 的 JRE/菜单 probe 证据不能作为完整 ISO consumer 来源；dlgt7 的 NativeUdfFileSystem（0edee45e6cb6e2404821e51476d726a5b4be80d9）与 IsoNavigationSession 均需 isoJNI，仍无匹配 producer。
- dlgt7 的旧 [40097806759](https://github.com/dlgt7/media/actions/runs/40097806759) / job 120883623858（716961e91418ed92f280bacefe849549c862d1a6）确有 BUILD SUCCESSFUL 及 13 个 AAR、artifact 12561383765（SHA-256 22a5a602347c80b15ee673e304092e3d3245d9ffb65c61032933538861711fd2），但该 commit LibassPlaybackSession blob 645510c1c130aceeaf41a2d7f29e82cc5601b61b 明示始终 unavailable/no-op，ISO controller blob c0615225d1d4c00d334ec4930e392a76350dcadd 不支持 ISO 导航。拒绝该历史成功 AAR，不下载、不接入。较新的 3382803f 的 [40160139860](https://github.com/dlgt7/media/actions/runs/40160139860) / job 121069784453 实际在 :lib-ui:compileReleaseJavaWithJavac 失败（PlayerView.java:33/801 将 DecelerateInterpolator 错误导入 android.animation，2 errors），未产出 AAR。即使修正单一 import，仍有上列独立缺件，不为此改第三方普通业务或重跑 CI。
- 扩查 peerless2012/libass-android@0b3617ace00b12aea552d0974978ca7e05a0c488、LumeraD3v/assrender@3542e5a2f099664d47832d03043bd499c1504a1a、jepsefan/assrender@0866d875ceaa603874d7ca424bfbb69fd8ec70d6、octans-media/open-octans-player-runtime@afa7cad5589199ab9e35d7acbf233c642aed9d16 的完整树：有独立 ASS/render/JNI 实现或其他 runtime 项目，但无同名关键 consumer 文件，API/生命周期与目标不等价，不能直接替代；kaam-dev/assrender 的额外分支读取 tree 404，未完成该分支检查。hjdhnx/easytv@7de0e043bdd36af53a08a46afdf9a7d39c0fef77 的实际锁/AAR 仍为 1.11.0-alpha01-fongmi / nextlib 1.10.0-0.12.1，公开评估明确将新光流插帧暂缓。Inliang/tvbox@16e4aa6825b1f09efa2ad5c830afcc85b6279419 和 wobuhui666/TV@3d9a1a1882116509552259c790bd24078c70fa3e 文档是官方 APK 路线或 APK 取证，不作为源码来源。FongMi/Box@4ee0c30c5148fe3bb3244c9cc85c89bc98583942 无相关 consumer 文件；官方 media 当前分支无变化，公开 Actions 仅上述历史 libass 构建，TV 公开 Actions 为网站发布。精确搜索 FfmpegMotionRenderersFactory、FfmpegMotionInterpolationController、SubtitleFontFile、nativeSetStyleOverride、isoJNI/IsoNavigationSession、nativeReadBlurayReplay、FfmpegDolbyVisionP5Native 等未取得其他完整可核验实现。代码检索主要覆盖默认分支，另查上述固定非默认 tree；不能据无结果断言所有公开或未索引源码不存在。
- 5.9 TV ExoUtil.java blob 3854f2c178a2a0c73af4a258543ccb3950de7da9 的 ExoRenderersFactory 继承 FfmpegMotionRenderersFactory；ExoPlayerSession.java blob dfde10b51a6605c6656126847b9c582a032e8c82 实际创建 FfmpegMotionInterpolationController/Libass controller，ExternalFont.java blob 6d91178353fbf391290c7820992e401fa03d39e7:460 实际 new SubtitleFontFile(file(), faceIndex)。不能以旧 FFmpeg JNI 或官方 motion 静态库代替完整新 consumer。另核对 MpvNativeLibraries.groovy blob 726d9dd79b9daee0b968c8a83eea510383f040f1：必需 libffmpegJNI.so 统一链接，libffmpegDoviJNI.so 存在时才校验统一链接；不能把后者误述为 Gradle 无条件必需文件，也不能为通过打包主动移除原有 Dovi 功能。其对应功能实现/合法来源仍需独立核定。

**恢复条件及决策**：取得同一版本的实际 Media3 consumer（含上述缺失类型与实现、完整 MPV bridge/请求生命周期、补帧 renderer/controller、FFmpeg JNI、Libass 新注册表、ISO/UDF JNI；核对 Dovi 与其他上游媒体能力），提供固定 commit/tree/构建配方或真实公开 AAR 对应源与可核验摘要；逐项核对 native descriptor、回调、资源释放、二 ABI 动态链接。官方 mpv-android wrapper LICENSE 为 MIT，FFmpeg 实际构建启用 GPL/version3，第三方 Media3 根 Apache-2.0 不自动覆盖组合 native 的对应源码、修改/构建配方及分发义务，仍须闭合全部适用许可（含依赖与先前记录的 MPEG-H 授权边界）；没有证据称候选必然非法，也没有证据批准完整分发。满足这些源/功能/许可条件后才实施最小必要接线、解决原 2 unresolved / 5 old-media-review，合批处理未过的本项目对齐门槛、完整 Leanback 双 ABI APK 与真机播放/恢复。此次是固定源码静态合同与既有远端日志核验，未运行新的 Java/JNI 构建或设备测试。无可采用的完整候选，不修改产品、依赖、guard 或 workflow，不启动 AC，不从 APK 回填、不拼接旧接口、不新增功能。保留 19/19、Core v26.7.28 和当前正式版；5.9.0 暂不可交付，仍只在 dev 留存证据。

#### 5.9.0 缺件主动补齐：第一批 MPV Java/JNI bridge（2026-11-26）

本轮只使用既有 dev，保留上一节 19/19、官方 native producer 和现有版本/签名/门禁。以 [TV #778](https://github.com/FongMi/TV/issues/778) 所列两个 AAR 为问题线索；11-01 提问，11-02 有建议从作者其他仓库补齐、提问者称找到，11-04 作者建议 AI，均未公开可重建路径；[#764](https://github.com/FongMi/TV/issues/764#issuecomment-6356349283)、[#729](https://github.com/FongMi/TV/issues/729)、[#746](https://github.com/FongMi/TV/issues/746) 不作为源码授权或构建证据。

**两件 AAR 的拆分与边界。** FongMi/media 的 `release` 2bc207851df311340767e913931ca7b28cab1794（8613 tree entries，无 mpvplayer）与 `release-1.11.0-fongmi` 3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d（9123 entries，含旧 mpvplayer/decoder_ffmpeg）均查完整 tree；公开 Git tag matching-refs 返回空，tags/forks 直接接口受当前连接器限制，不据此宣称不存在未索引的历史源码。公开作者相关项目列表与 #778 三个参与者可搜索的公开 fork 列表未提供新完整 consumer。

- `lib-mpvplayer-release.aar`：旧 `libraries/mpvplayer/build.gradle.kts` blob abf50d475ba2908baf28b145f19c8277d1d8a10b 为 media3.android-library / media3.publish，api lib-common、implementation lib-decoder-ffmpeg/lib-exoplayer；MpvLibrary blob e2b5248a997c2825f6f0ce8df47622d1260a92bb 仍用 LibraryLoader("mpv", "player")，MpvClient blob 892e3f497adc4169f34ecaa303a7212506df3ac4 使用 Java static 调用和旧回调。可单独补底层 MPVLib 桥；真实 5.9 MpvPlayer/配置/字幕/播放源/光盘 consumer 与 native 包装尚未闭合。最终按同一 Media3 源版本构建 :lib-mpvplayer:assembleRelease，使用匹配 producer 双 ABI 的 native 输入，不另引入重复 is.xyz.mpv.MPVLib 或重复 libffmpeg。
- `lib-decoder-ffmpeg-release.aar`：旧 `libraries/decoder_ffmpeg/build.gradle.kts` blob c7825ea21e01522a122603d8f15997dd684ca11e 读取 native-dependencies.properties、限定 armeabi-v7a/arm64-v8a、头文件存在才启用 CMake，api lib-decoder / implementation lib-exoplayer；旧 CMake blob 086fe3a78b1c6f7dcb70faf133e8fa22e4b83479 明确导入分立 avutil/swresample/avcodec/avformat 和 libplacebo.a，编译 ffmain/ffcommon/ffaudio/ffvideo 等源。5.9 需要统一 libffmpeg 的真实 JNI、补帧 renderer/controller 与相应 Java API；不能仅改链接名或把旧 AAR 改名。最终应在同版本 Media3 模块用固定 headers、同源 libffmpeg/renderer SDK 及对应 JNI 构建 :lib-decoder-ffmpeg:assembleRelease，核验 JNI signatures、统一链接、双 ABI 和原功能；Dovi 的条件性存在不等于可删功能。当前不伪造 Gradle 配方、不把半成品 AAR 放 app/libs。

**#778 时间窗口的公开提交追查和新增候选（均未下载或导入第三方二进位）。**
- 精确 AAR 名 commit 搜索命中 [ctowl2018/NewTV@2dc53bff](https://github.com/ctowl2018/NewTV/commit/2dc53bffb1d6f2cb5c72fd675bd5df98d6ca5ebc)，2026-11-02 06:13:11 UTC；完整 1587-entry tree 中有同名 FFmpeg AAR blob a57af349ae9c39b1c2fd71b481e7d38efd61ce40（27831856 B）、MPV AAR eb094889a52517482669777fb88cdd5385bc462c（15032957 B）。但 app/build.gradle blob ae7fc9c7d6570eb61acee951ef54aab9947c3ad5:108-111 明确排除 FFmpeg AAR，作者自述 native ffmpegInitialize 需六个 int 而 Java class 五个，CheckJNI abort；未独立执行此二进位。workflow b7985416c4492547f1b64f2a3603f867b9a006e3 直接使用预置 AAR assembleLeanbackDebug，上传 arm64 APK，不是 AAR 源码双 ABI 构建。与 #778 日期吻合不代表该回复所指路径。拒绝使用。
- [ican521/ICAN-YunYing@8f49ba09](https://github.com/ican521/ICAN-YunYing/commit/8f49ba092ccd448c0773a5bcd9aafb10933a59ae) 11-25 提交描述涉及本地 AAR 反编译，188-entry tree 有同名 AAR 但无相应完整源码构建链；[26055423/DualSub_TV@5af925b8](https://github.com/26055423/DualSub_TV/commit/5af925b881b45e4776852afc6a380d53650cb9b6) 09-16 提交为 LFS AAR；[Ray-Lin92/LinPlayer@fe33575a](https://github.com/Ray-Lin92/LinPlayer/commit/fe33575a2fe30bbe9dd5e5ad0843bdbe81259dd5) 05-22 的 build-ffmpeg.yml 9dc842c89c45f0ce601c4063d3a3a74ee825c401 使用 AndroidX Media3 与 FFmpeg n6.0，不是目标消费端。均不能作为所需新版 AAR 来源。
- [WebHTV@4e30ffaf](https://github.com/webhtv/webhtv/tree/4e30ffaf219b1db15fe5662aeff6f9820e2b32bf) 有真实锁定 recipe（lock blob 5bdde9b4d367c8cae043c9457666d796da304124，Media3 1.11.0-alpha01-fongmi，nextlib 1.10.0-0.12.1-fongmi-softload-av3a-avs3-ffmpeg901-r5）；JNI build script d4061a1db63efb70833511d939b09a9d68fcf7ef 双 ABI 链接 max-page-size，MPVLib.java 6d8bb0fb8433f3242aaecd731af83895fc98e298 仍为两参数回调且没有 Stream/openStream。MpvPlayer.java 09f1c3a66bdbb4fafe65683f1ba77e258b58b708 大量依赖本项目以外的 WebHTV app。只参考构建思想，不移植整套播放器或承认新版合同通过。
- [Riteshp2001/mpvlibAndroid@46067e8c](https://github.com/Riteshp2001/mpvlibAndroid/tree/46067e8c0edb04d83bf4a966c7c725b20988a7b6) 的 mpv-fongmi 分支 11-25 准备 1.1.8.9，MIT LICENSE 81d2ff31ab3e434d6f67fa5ac1e15e345f175db6。app/build.gradle 5641e4b413725aa57172e03d4c1aec1fae3b4d1b 为 Android library，minSdk24，4 ABI 映射、Kotlin JVM17，要求生成 native 版本元数据；Android.mk c16dab9b90d74f38961bc52238d60911e911d5dd 包含 stream.cpp 并链接 libffmpeg/mpv；stream.cpp 与固定官方 producer blob a4ebe55984fa12de9b0a354da4a98cfcfa634d5d 完全相同，main.cpp 73f611b7c688b886f2217d99ade46b9314fc5d75 真实注册 stream，jni_utils.cpp 8b33680804b35fecb170f59aca45e46700e71016 要求 (JIJ)V。MPVLib.kt 0440ec0948522cb0736221cce1822bfd7d69a4f9 有 registry 和三参数回调，但 destroyNative、command/setPropertyString 的返回类型等与官方不同，新增 coroutine/node/thumbnail 合同，不能直接混装。depinfo.sh d316948daae8906b4cba0a91d10cf41b91694d35 固定 NDK r30，仍有移动 refs；FFmpeg recipe 0fad3d81a2145bdf6d6014e1bf35ef98e8e56948 启用 GPL/version3，motion SDK recipe 2c0f817811208fa0b664246ddbd54f4cba9fc2f5。已核实历史 [run 43806107265 / job 133097139636](https://github.com/Riteshp2001/mpvlibAndroid/actions/runs/43806107265/job/133097139636)，源码 8e86c57ab85d1b6488b9ecef70ae4f506f1e3e1f，2026-11-16 原日志两 ABI 均编译 stream.cpp、链接/安装 libplayer.so，Native package verified 四个 SO，Gradle BUILD SUCCESSFUL，FFmpeg Git commit dc192e44ba013456c0fcdd723eac1677812e404d；不是 46067e8c 的构建证明，更不是 Media3 consumer AAR 或本项目门禁通过。
- [mpvRx@501f1099](https://github.com/Riteshp2001/mpvRx/tree/501f1099ff3df34f1dbc6622bc35fd21e4a7f675) 版本目录 e094a798... 固定 mpvlib 1.1.8.8，通过 Ivy 下载 release AAR；[QuantumMPV@5ea6e7ce](https://github.com/SimplyFahimOfficial/QuantumMPV/tree/5ea6e7ceccf4cab3d94e6bab3b9b6245f16f3758) 锁 7bb17e123919f8de37d3b4952b63f475d08b015c 中 FongMi AAR 实为 v1.0.9 / v1.0.10 release、source_revision c1ac6f47d7c2d1007de0731a6fb6395eda925213、FFmpeg release-9.0-fongmi；声明四 ABI 和摘要不是实际字节核验。二者是独立 App，支持参考生产链，不提供目标 Media3 consumer，不导入其 App 或二进位。

**实际源码局部补件及定向验收。** 新增 `scripts/upstream-adaptation/stage_mpv_jni_bridge.py`，不接入 prepare_candidate/Gradle/CI，也不改当前 App。用 FongMi/media@3c2cbe8 的原 Apache-2.0 Java MPVLib.java（blob 36da8033843061ffbcbf560ed77566ffdca4dd98）作为底，按官方 FongMi/mpv-android@1bf892e3 Kotlin MPVLib.kt（58656ed251ddec0d07ac416149428cbb22524fc8）与实际 native 源移植 Stream 接口、URI registry、静态 openStream、7 个真实 native 声明和三参数 long 回调；保留 Java 旧静态入口、CopyOnWriteArrayList、两参数 observer 的默认兼容及原 LibraryLoader 分工。JNI macro jni_utils.h 95f4a00e0ae69c7f187546077d35cf368af599b5 接收 jobject；实际 main/property/render/thumbnail 实现均不使用该 receiver，保持旧 Java static 调用方式，仍需 Android runtime 验证。native 定义来源：main.cpp 0abeaf6b3146f41b7fbd9f961aa78f134f7179ce、property.cpp f39455b1152d0854a0d72c9aa95c8d4d7d36e0d6、render.cpp 9ddee412d1860da16902f615eecc31a02672acf9、thumbnail.cpp ac5af164a68ed7d36b39e9732fd850beac5579ca；JNI cache 和 stream contract 见上一节。保留原 Apache notice 并附固定 producer MIT notice；只移植 Java glue，不声称组合 native 的 GPL/LGPL 等分发义务已闭合。TV 5.9 minSdk24 且启用 core library desugaring，新增 Supplier 不扩大 minSdk。

运行方式（Linux Python 3.9+ / JDK / cc，输入取自上述固定提交；检查旧 Java 与 MIT license 两个 Git blob，不联网、不使用 APK、不修改输入）：

```sh
python3 scripts/upstream-adaptation/stage_mpv_jni_bridge.py \
  --media /path/to/pinned-media --mpv /path/to/pinned-mpv-android \
  --out /tmp/MPVLib.java
```

本地 JDK 21、gcc 实际运行通过，脚本 Git blob 5bf3d7e65b2604ac18ec577bee04cd3b0d936979，生成 Java SHA-256 d5e4c9249b88bbc8b562008c79bbf44e9e57b0fcbe789cc5c96fcb7594045f0b。24/24 public static native method descriptors 与固定官方声明合同一致；host JNI C fixture 在 -Xcheck:jni 下真实查找九个 static event callbacks、openStream 和五个 Stream methods、读取 direct ByteBuffer（含 seek/EOF）、size/cancel/close、三参数回调的 64-bit request/result、旧 observer 兼容、observer 移除、URI registry 新 cursor/未注册 URI；修改输入 blob 的负向试验被拒绝。Android 类型仅为测试 fixture，C probe 不代替 libplayer.so、不调用那 24 个 native 实现，不能称 Android AAR/设备播放已验。不新增 AC，当前连接器无新 workflow dispatch 且本地合同验收已完成；不改自动触发规则、不重跑旧 19/19 和 producer。

**下一批最小缺口：** 底层 MPV Java bridge 可独立复用，但没有把 Stream 注册接入真正的 Media3 DataSource。需补匹配新版 MpvPlayer/loader 的 range/seek/size/cancel/close、异常/认证/headers、每播放 owner 唯一 URI 与 generation 退役，防止旧 owner unregister 删除新 owner；当前 registry 仅是官方 exact URI -> factory 映射，不宣称线程/owner 网络隔离已验证。普通 MPV 仍保持上游；Xray 单播放 owner 仍走现有 ExoPlayerEngine 路径，不把此 bridge 改为全局代理。FFmpeg 补帧 controller/factory/renderer、统一 libffmpegJNI 与 Dovi、Libass 新合同、ISO/UDF/BD-J 完整 JNI 和相应源码/许可仍未取得可集成版本，不能以其他播放器功能替代。两项未解宿主冲突、五项旧媒体待审、ARMv7 既有 ELF 门禁和完整 APK/真机门禁原样。阶段结果只表示第一段真实 Java glue 已通过 host 合同测试，完整 5.9.0 不可交付；main、Release、签名、原 AC 历史和 Core 保持不动。


#### 5.9.0 第二批：MPV HTTP stream owner 局部补件（2026-11-26）

新增 [独立候选与可复现验证记录](../scripts/upstream-adaptation/mpv-stream/README.md)，包括真实 HTTP WAV host 试验、单播放 owner/cursor 与作者 OkHttpDataSource/MPV Stream 接线候选。最终 host 源码连续五次通过，11/11 source close；Media3 adapter 尚未实际编译、未执行 Android/native 或整 APK，不进入 prepare_candidate/Gradle。原 Exo/Xray、TV 恢复、普通上游、Core、main 和正式版不动。详见该记录的源合同、回调归属限制及 FFmpeg/Libass/ISO 搜索边界。

# FingMi-Xray 开发与维护

本文面向维护当前 `main` 的开发者，说明**工程基线、模块接线、构建依赖、上游同步方式和验证规则**。当前开发、上游同步与后续验收基线统一为 `main`。

长期架构边界见 [PROJECT.md](PROJECT.md)。`v5.6.0-xray.5` 的恢复、native provenance 与 v7 Xray 黄金行为证据见 [RECOVERY.md](RECOVERY.md)。当前 `main` 负责架构与构建验证，v7 黄金参考负责约束 Xray 外部行为；两者不能混为旧 faithful 架构重建。

文档状态：`ORIGINAL_README.md` 是用户明确指定的冻结旧发布说明，只读不改；`AI_COLLABORATION.md` 是当前协作规则的 canonical 文档，用户调整开发限制时应同步维护。当前工程事实、长期架构和历史证据分别继续维护在本文、`PROJECT.md` 与 `RECOVERY.md`。

## 1. 当前工程基线

当前应用源代码跟随 FongMi/TV 当前 HEAD；上游自身的 `app/build.gradle` 版本名仍为 5.6.3：

- 上游目标 commit：`c616c0aa3613e87529791587a9f71b78c278c991`
- 上一固定基线：`4afc4473e22a7ed3d98ee12233e0c2a490061000`（5.6.3）
- 两者是直接父子 commit；新增 runtime 变化集中在 `catvod` 的 redirect-aware proxy selection/authentication。Release / APK 的更高版本号不改变本项目的公开源码上游基线。
- app `versionCode`：`563002`
- app `versionName`：`v5.6.3-xray.2`
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

任何超出上述范围的代码修改，在提交前都应先问：**这个变化是否是 Xray 或 TV 网络恢复的必要条件？如果不是，优先删除该差异并跟随上游。**

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
- 在切集、切台、换源、换线路、刷新或播放器重建等**逻辑播放身份变化**时结束旧会话；
- 同一播放身份内的 parser 解析结果、HTTP redirect 或 CDN URL 变化只更新当前媒体 URL，不自动停止 Xray，也不回退到直连；不支持的最终请求继续由 Xray scheme / destination guard fail-closed；
- Live 尚未建立 playback session 时，先按发布版 direct-source 规则拒绝 HTTP(S) `.strm` / YouTube indirection，成功后才清 preload 并启动 Xray；
- 把新的 `XrayHttpClient` 交给播放器；它保持发布 `pz3` 的资源语义：getter 始终返回会话持有的 OkHttp / RTSP factory，close 只负责幂等 shutdown + 异步 cancel/evict，不额外把 getter 改成同步 `IllegalStateException`；
- 在 Activity 销毁时关闭 session。

业务页面只决定“当前是什么播放身份”，不实现 Xray Core 细节。

关闭会话时先卸载播放器代理、清空会话资源引用，再幂等关闭独立 HTTP Dispatcher，异步取消请求并淘汰连接；普通 player client 不随之销毁。STOP 成功后立即解绑，已派发的 STOP 超过 1.5 秒则取消并解绑，未建立连接由 5 秒 bind timeout 收口。500 ms 仅是 controller 关闭且没有待处理 STOP 时的兜底。最后一个客户端解绑、Android 销毁 Service 后，私有进程等待停止最多 3 秒，最终调用 `killProcess` 回收 Go/native 堆；多个合法 Binder owner 尚未全部离开时不能把进程存活直接判成泄漏。HTTP 清理线程在空闲 5 秒后退出。对象可回收和应用总 RSS 立即下降不是同一指标，设备验收应同时观察 `:xray` 进程退出、连接/线程收口及多轮操作后主进程内存是否持续增长。

多个播放 Activity 交接时，由原有 `PlaybackService.claimBinding` 的旧 owner 回调先触发 Leanback 的 `onXrayBindingReplaced`，同步结束旧 Xray 身份，再执行上游 PiP 关闭和新 owner 的播放任务。不能只依赖旧 Activity 较晚的 `onStop`，因为新页可能已改变共享播放器 key，导致旧页的 owner 检查跳过代理卸载。同 owner 的重复认领不触发此钩子，Mobile 默认钩子为空；不在 `PlayerManager.start` 无条件清代理，以免误关 Live pending 时已经手动开启的新会话。

### Settings / Binder

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

## 4. TV 网络恢复

TV 网络恢复没有放进 `:xray`。

主要入口：

- `tv-recovery/src/main/java/com/fingmi/tvrecovery/TvNetworkLifecycle.java`
- `tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java`
- `app/src/main/java/com/fingmi/integration/recovery/FongMiNetworkRecovery.java`

`TvNetworkLifecycle` 由 Leanback `HomeActivity.initView()` 创建 `FongMiNetworkRecovery` 适配器时首次安装，随后注册 Application 级 Activity lifecycle 与 SCREEN_ON / SCREEN_OFF receiver 来生成前后台 / screen 网络代际；它不是 Application 冷启动时无条件创建的第二套网络服务。Home 持有适配器，适配器持有独立模块的 `NetworkRecoveryCoordinator`，仍只在 Home 的 `onResume()` / 窗口重新获得焦点时检查并执行每个待恢复 generation 的普通网络重建。Home 不再实现网络状态判断或资源重建流程，仅提供取消页面请求、进度显示、存活判断和刷新回调。

首次从 exported 播放页冷启动、之后才进入 Home 时，监控器可能没收到旧页面的 START。核心按 Activity 对象身份记录实际收到的 START，只由匹配的 STOP / DESTROY 移除；未知或重复 STOP 不得误扣仍可见的 Home。DESTROY 清理尚未退休的引用，正常 STOP 后幂等无动作。配置重建、SCREEN 代际与 DLNA 启停的既有规则保持不变；这是对黄金 `gn3` 整型计数的有意修复，回归由 `tests/test-tv-recovery-cold-entry.py` 编译真实核心和双 flavor 适配器执行，不将监控器迁入上游 App。

发布版 generation **只**由真实后台 / SCREEN_OFF 后重新进入前台 / SCREEN_ON 推进；前台 Wi-Fi、VPN 或默认网络切换本身不额外创建 generation。Home 也只在自身 `onResume()` / 重新获得窗口焦点时检查是否需要恢复，隐藏在其他播放页面后的 Home 不主动执行恢复。`recoveredGeneration` 只用于防止 Home 重建时漏掉尚未完成的 generation，不增加新的触发来源。

恢复过程按 generation **串行**：如果当前 Spider clear / 网络稳定轮询尚未结束，新 generation 先等待；旧流程发现 generation 已变化后才结束本轮并启动下一轮，禁止两个 Jar / JS / Python loader clear 并发。

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
**当前构建债（不是上游基线）**：公开 `FongMi/TV@c616c0aa...` 明确是 5.6.3，且本项目唯一上游仍是这条公开源码线。公开 `FongMi/media@3c2c...` 不包含 `libraries/exoplayer_libass/`；Libass compatibility 使用的固定 `libmedia3ass.so` 最初取自 FongMi Release 5.6.8，现从本项目保留的当前正式 APK 中读取完全相同的字节。上游原下载地址已返回 404，不再作为正常构建依赖。这只修复容器的可用性，**没有移除原生库缺少对应可重建源码的技术债**，不能称为公开上游、不能用于引入任何 5.6.8 App/播放器行为，也不能声称所有二进制输入都仅来自公开 5.6.3。

正常构建先选定本仓库当前正式 Release 的两个 ABI 资产并校验 native，再进行昂贵重建；信任边界仍为固定 SO 摘要，容器中的 DEX、资源和其它库不作为输入。实际 Release/资产身份与 APK 摘要单独记录，不能把本项目 APK 冒称原始上游 APK。同名替换会改变容器摘要，但不允许改变 native pin 或 Libass candidate 摘要。新发布先完成输入提取和新资产验证，之后才清理旧版。原上游 APK 的整包摘要校验模式仍供历史取证使用。

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

不保留 `push`、`pull_request`、`schedule`、`workflow_call` 等自动触发。

#### AI 协作执行准则

[AI_COLLABORATION.md](AI_COLLABORATION.md) 是当前 AI 协作规则的 canonical 文档；用户给出新的开发边界、Actions/AC、分支或交接要求时，应直接同步维护该文件。本文不重复维护其临时 trigger、轮询和交接细节。


当前工程主构建：

`.github/workflows/current-main-build.yml`

它负责：

1. 准备 JetBrains JDK 21 / Android SDK，并执行禁用自动下载的 `gradlew help`，实际启动上游要求的 Gradle daemon；预检在昂贵的 player/native 重建之前完成；
2. 先获取并验证本项目当前正式 APK 内固定 Libass native，再从固定公开 FongMi/media commit 重建 18-AAR player candidate，并下载 / 校验其它 compatibility 与黄金 Xray 输入；
3. 直接导入固定公开 FongMi/media 重建出的 player candidate；黄金旧 APK只用于重建与 Go JNI 配套的 libXray Java bindings 与 Xray 动态 parity；
4. 重建并导入最小 Libass compatibility AAR；
5. 执行 current Java → 黄金 v7 / arm64 native 动态 Xray chain parity（统一以 v7 发布行为为黄金 oracle，包含 KCP golden cases 与发布版 `testXray` runtime validation）；
6. 只编译 Android TV / Leanback Java；
7. 只 assemble Android TV / Leanback 两个 ABI 的 Release APK；
8. 对最终 APK执行 Media3 DEX 类定义/引用闭合、MPEG-H class/native、Xray/FFmpeg/MPEG-H/Libass runtime PT_LOAD provenance 与 merged Manifest security contract；
9. 上传短期、固定签名的 TV release artifact（保留 2 天）供临时验证；上传成功后自动删除同名旧 release，只保留最新一份。失败报告只保留 1 天。历史 recovery workflow 的 JADX/DEX、faithful APK、native dependency、player AAR 和 upstream snapshot artifacts 也只作临时复核，统一最多保留 3 天；长期可重建输入只保留源码 commit、脚本、fixture 与 hash，不再占用 Release。Gradle 命令继续使用 `--warning-mode all`；当前剩余会在 Gradle 10 失败的 deprecation 已确认全部来自固定上游同样使用的 Chaquopy Gradle plugin 17.0.0（multi-string dependency notation 与 execution-time `Task.project`），不是本仓库 Gradle 脚本。当前保持 FongMi/TV 5.6.3 的 17.0.0 pin，并让 `com.fongmi.chaquo.Platform` 继续跟随固定上游实现，不在本 fork 中为一般兼容或 warning 主动改写 Python ABI 选择逻辑。

正式发布器（文件名保留以兼容既有手动入口）：

`.github/workflows/publish-current-main-test-release.yml`

Release 的 APK 发布集合长期保留 `v5.6.0-xray.5` 黄金参考和一个当前正式版。构建输入、恢复材料、临时归档和旧测试版不得长期堆在 APK 发布集合中；用户要求的最新完整源码备份由同一发布流程生成，使用 `source-backup-<UTC 日期>-main-<源码 SHA 前八位>` 独立 Release。备份通过 `git archive` 导出确切 `BUILD_SOURCE_SHA` 的 tracked tree，包含本私有项目的固定签名及恢复配置，不包含 ignored AAR、缓存或临时构建文件；可重建输入继续由脚本及 hash 管理。若使用临时 marker 触发，归档也忠实包含该构建提交的临时 trigger/marker，备份说明必须指出这一点；run 完整结束后另恢复 main 的纯手动工作流，不重写归档并冒称原 SHA。

`test.7` 构建源码为 `439cea8d7a9d3cdb1a17b4ed962c6d68ed164508`，缺少后续 Hysteria2 备注查询边界修复；正式版替换旧测试发布。构建源码、资产 hash 与当前验收结果记录在对应 GitHub Release，历史 test.7 证据保留在本文维护记录，不能当作正式版的验证。

发布 workflow 以 `BUILD_SOURCE_SHA` 作为唯一构建与发布源码，重新准备固定依赖、执行源码 guard 与双 ABI 黄金 Xray chain parity，只编译/assemble Android TV / Leanback Release 两个 ABI，并核对最终 native provenance、Manifest、签名、应用版本、non-debuggable 与 16 KB alignment。当前显式配置 `RELEASE_TAG=v5.6.3-xray.2` 与指定旧源码备份 `PREVIOUS_BACKUP_TAG`，不会自动递增修订号。正常手动触发时 `BUILD_SOURCE_SHA = github.sha`，权限保持 `contents: write + actions: read`，同一发布流程使用 concurrency 排队而不取消正在进行的发布。

`scripts/build/publish-current-release.py` 负责上传和替换，`tests/test-release-publication.py` 验证发布失败与清理顺序。两个 APK 和源码 ZIP 先分别上传到草稿并逐文件核对 name / digest / size；两份新产物完整后才进入切换。已有同名正式版必须由用户明确要求并选中 `replace_existing`；旧 APK 暂存为 rollback 草稿，直到新正式 APK、源码备份及各自 Git tag 都验证成功才清理。只删除显式指定的旧备份，不按 `source-backup-*` 通配删除。失败时保留可诊断/恢复的草稿，不把失败说成替换成功；正常收尾只留下黄金版、当前正式版及最新源码备份。

GitHub 的按 tag 获取已发布 Release 接口不会返回草稿；草稿创建和旧版转 rollback 后，必须使用已知 Release ID 校验状态、tag 和全部资产。存在性检查同时包含分页草稿列表；最终正式发布仍检查公开 tag、Git ref、资产摘要及 latest，不能因草稿查询 404 就放松校验。测试替身必须保留“draft 按 tag 查询为 404、按 ID 可读”的真实区别。

仅发布阶段失败时，可用纯手动 `resume-verified-release.yml` 续发原 Actions 已验证 APK，避免重复编译。续发先验证原 run 的仓库、workflow、触发方式、源码及全部构建/验收步骤，再读取该 run 的失败报告，通过明确草稿 ID 下载原资产并重验摘要、签名、Media3 DEX 类链接、Manifest 和内嵌源码。源码 ZIP 仍归档原 APK 的构建 SHA；执行续发工具的较新 main 仅含发布基础设施修复时，也不得把它冒称 APK 的构建来源。原 run、报告或资产不满足条件就停止，不能拿本地包或未经完整验收的草稿补位。

切换后期失败没有自动回滚，正式入口可能暂时缺失；此时先读取失败 artifact 内 `publication-before.json` / `publication-result.json`，核对正式 tag、rollback 草稿和新草稿，再恢复入口或继续切换，不能直接复用已占用的 rollback tag 盲目重跑。需要时可通过 `rollback_tag` 手动输入一个预先指向旧 APK 源码的 tag，避免 runner token 为旧提交创建 tag 的权限限制；成功后该临时 tag 自动清理。

### 固定签名与 Release 构建校验

版本命名、修订号递增、versionCode 公式和覆盖升级约定以 [PROJECT.md](PROJECT.md#版本命名与覆盖升级) 为准；后续 AI 的强制发布要求见 [AI_COLLABORATION.md](AI_COLLABORATION.md#11-ai-开发与发布的版本约束)。本节维护签名恢复、构建配置与产物验证方法。

- 新固定签名为 RSA-4096 / SHA256withRSA，有效期 100 年，自此用于本地与手动 workflow 的正常发布。PKCS12 文件 `signing/fingmi-xray-release.p12`、恢复配置 `signing/release-signing.properties` 和证书 fingerprint 文件按用户授权存入**私有仓库**；配置包含密钥密码，不能输出到日志或复制到公开项目。源码备份也包含它们，应同时保存到用户离线备份。
- `app/build.gradle` 直接读取此固定配置，Debug 也复用同一签名；缺少文件时构建失败，不回退到临时开发证书。两个 current-main workflow 不再生成签名，正式包使用 Release variant。历史 recovery workflow 仅用于冻结旧行为取证，不作为当前正式发布入口。
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

Release 文件名沿用上游 finalizer 的 `leanback-armeabi_v7a.apk` / `leanback-arm64_v8a.apk`，对外资产命名为 `FongMi-Xray-TV-v5.6.3-xray.2-<ABI>.apk`。设备 ART/真实节点/电视待机仍属于真机验收，不因 GitHub 标记为正式版而自动视为通过。

当前 build 与 publish workflow 都必须先执行：

- `tests/test-xray-android-runtime-compat.py`：防止 Java 21 可编译、但旧 Android ART 运行时不存在的 API 再进入 `:xray`，并防止 `main` 构建重新退回“官方旧 Java bindings + 单独替换发布版 Go JNI”的不匹配组合；
- `tests/test-xray-core-parity.py`：守住配置生成、存储 / TOFU、Service 重试清理、Settings 核心语义、手机导入的 EventBus / operation 中断边界与发布版错误去敏链，并要求 current public destination guard 与发布 `qz3` readable mirror 保持逐行为等价；同时调用 `tests/test-xray-service-execution.py`，编译执行真实 Service、generation gate 与错误去敏类，验证启动/停止、准备期间替换/取消、回调失败后的清理、仍运行的 native Core 防护与取消后禁止信任写入。Android、native、配置构建及 pin 存储为确定性边界替身，实际 native 配置另由双 ABI chain 验证；
- `tests/test-xray-playback-parity.py`：守住 VOD / Live、播放器代理切换、媒体旁路、本地 scheme、artwork/logo 与资源释放语义，并调用 `tests/test-xray-side-request-lifecycle.py`，编译真实弹幕/字幕 API 与上游 `ApiCallback`，验证 HTTP / 下载完成后排队回调的 Xray 取消、owner 关闭、replacement 与 reentrant 边界；`tests/test-xray-danmaku-client-binding.py` 另执行真实页面初始化/选择方法，覆盖服务尚未绑定、直连、代理与断开后的 client 选择，避免只检查代理已经就绪的路径；
- `tests/test-xray-playback-address-parity.py`：把 public HTTP(S)/RTSP/RTSPT、私网/保留目标、Unicode whitespace，以及 Live pending `.strm` / YouTube indirection 边界与冻结发布证据做 differential parity；
- `tests/test-xray-playback-binding-handoff.py`：由 playback parity 调用，执行真实 Activity / Service 绑定方法与 `XrayPlaybackSession`，覆盖新旧播放页交接、相同媒体 key、旧页迟到关闭、重复认领、Live pending 及默认 Mobile/PiP 行为；平台、播放器与远端服务为明确替身；
- `tests/test-xray-session-races.py`：锁住发布版 STOP / timeout / callback 的竞态顺序；
- `tests/test-xray-service-client-lifecycle.py`：直接编译真实 Service client，锁住 bind timeout、cancel/unbind、Binder death 与 stale callback / connection generation；
- `tests/test-xray-normalizer-parity.py`：把当前 share-link normalizer 与 display helper 对发布版 readable reference 做纯 JVM differential parity；
- `tests/test-xray-transport-security-parity.py`：把 TLS / HY2 TOFU identity、首次信任、证书变化拒绝、已有 pin 与大小写/migration 边界对发布 reference 做 differential parity；
- `tests/test-upstream-update-disabled.py`：防止 FongMi 上游自更新入口、直接 release endpoint 调用或 APK 安装权限重新进入当前 fork；
- `scripts/build/check-elf-runtime.py --self-test`、`check-final-apk-native.py --self-test`、`check-final-apk-manifest.py --self-test`：先验证最终 ELF/Manifest gate 自身的判定逻辑；
- `tests/test-build-hygiene.py`：防止错误 XLIFF namespace、非 positional 多参数 string、FongMi/Chaquopy 上游边界再次被 fork-only 改写、Release-only media restore 回流，以及仍基于 Node 20 的旧 Actions major 再进入构建；
- `tests/test-tv-network-recovery.py`：锁住正式 `gn3` 的前后台 / SCREEN generation 来源，并用纯 JVM harness 验证 recovery 顺序、连续稳定检查、DoH resolver snapshot 与跨 generation 串行清理。

`tests/` 是 `main` 的统一回归入口，不再另维护目录 README。除上述 workflow guard 外：

- build/publish 的 Gradle 编译步骤必须同时执行 `:xray:testDebugUnitTest` 与 `:tv-recovery:testDebugUnitTest`，`test-build-hygiene.py` 检查这两个入口不可被遗漏。Python source/JVM guards 与 Gradle 模块 JUnit 是不同验证层，不能互相替代；workflow 仍只允许手动触发。

- `tests/test-current-native-share-chain.py` + `tests/xray-current-chain/`：执行 current Java normalize/security/config 链，并分别调用固定 v7 / arm64 发布 `libgojni.so`，对 26 组 conversion/runtime oracle 与发布版 `testXray` 做动态 parity；其中 6 组覆盖 KCP golden cases。
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

`recovery-*` workflow 只保留给历史取证、来源重建或必要的二进制复核；它们不是 `main` 的发布前置条件。历史恢复说明见 [RECOVERY.md](RECOVERY.md)。

### 本地

编译、测试或 assemble 前，需要先准备 `app/libs` 与 `libxray/libs/libXray.aar` 所需的固定依赖。最完整的依赖准备顺序以 `current-main-build.yml` 为准。仅执行 `help` 的 daemon 预检不依赖这些生成 AAR。

完成依赖准备后，主要验证命令为：

```bash
bash gradlew --no-daemon :xray:testDebugUnitTest :tv-recovery:testDebugUnitTest :app:compileLeanbackDebugJavaWithJavac
bash gradlew --no-daemon :app:assembleLeanbackDebug
```

集中复查时，除上述源码/JVM入口和双 ABI native chain 外，应核对 Gradle XML 中实际执行的 tests/failures/errors/skipped。需要确认重新执行而非 `UP-TO-DATE` / `FROM-CACHE` 时，在对应 task 后加 `--rerun`；不要为普通文档调整重复构建。可用 `--offline` 复用已经校验的本地依赖。

云端受限文件系统中，Java 用户目录与 Maven/Gradle 缓存必须使用可写路径；Robolectric 会在 Java `user.home` 写下载锁，不能只设置 Maven local repository。当前云端以 `-Duser.home=/workspace` 和 `/workspace/.m2/repository` 完成测试；Gradle 自动下载的 JetBrains JDK 需通过 `-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts` 信任环境系统 CA。代理沿用环境提供的配置，不关闭 TLS 验证。播放器公开源码构建还会安装 NDK `29.0.14206865` 与 `28.2.13676358`。wrapper 未带执行位时可使用 `bash gradlew`。 `check-final-apk-manifest.py` 读取 apkanalyzer 的合并输出，因此检查时需将 Java 参数传给 `JAVA_OPTS` 并移除该子进程的 `JAVA_TOOL_OPTIONS`，避免 JVM 的 “Picked up” 提示混入 XML；参数不变、TLS 验证仍开启。

## 8. 跟随 FongMi/TV 上游

升级上游时只以当前 `main` 和目标 FongMi/TV 上游为架构开发输入，不从历史 recovery faithful tree 继续开发；但 `:xray` 的外部行为仍必须保持与 `v5.6.0-xray.5` v7 黄金参考一致。

固定上游树中的 `website/` 静态站源码可以随上游保留，但它不属于本 fork 的产品功能维护面；本仓库不迁入上游自动 Pages workflow，并按项目文档规则不维护 `website/README.md`。

建议流程：

1. 固定目标 FongMi/TV commit；
2. 比较当前 main 与目标上游；
3. 以上游新代码为主体覆盖/合并普通业务、UI、播放器、设置和工具代码；
4. 只重新应用 Xray 与 TV 网络恢复必需的最小 hook / adapter；
5. `:xray` 除非模块 API 本身需要变化，否则尽量不动；
6. 不把上一版本中与两大模块无关的 fork 差异继续携带到新上游；
7. 重新核对 VOD / Live identity 边界；
8. 重新核对 PlayerManager、Exo / MPV、DRM、RTSP 与媒体旁路；
9. 重新核对 TV 网络 generation / DLNA；
10. 执行当前构建 workflow；
11. 再进行 Android TV 运行回归。

如果上游改变了播放器 API，优先新增小型适配层，不把上游大块代码复制进 `:xray`。

## 9. 验证清单

当前验收对象是**当前 `main` 架构 + `v5.6.0-xray.5` v7 的 Xray 外部行为语义**。正常发布不要求重建完整 5.6.0 faithful APK，但凡修改 Xray / 播放代理 / Service 生命周期，必须继续用冻结发布证据、source guards 或动态 native parity 证明没有偏离黄金参考。历史 recovery workflow 只在修改历史证据、来源提取脚本或需要重新核对二进制 provenance 时运行。

影响 Xray / 播放器 / 网络生命周期的修改，至少考虑以下场景：

### Xray 基础

- Android 12 / SDK 32 等旧 ART 上的节点保存、删除、测试；
- v7 / arm64 测试包的 Service bind、Java → libXray invoke 与错误返回；
- 节点保存、删除、测试；
- 手机导入；
- VOD 开启 / 关闭；
- Live 开启 / 关闭；
- Xray 启动失败后的直连恢复；
- Service disconnect / Binder death / stale callback。

### 播放身份

- 切集与自动下一集；
- 切频道；
- 换线路 / 换源；
- 同一播放身份内实际 URL / CDN / parser 结果变化时 **不** 重置 Xray；随后切换到新的逻辑播放身份时才重置；
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

## 10. 维护记录

本节只保留会长期影响后续开发判断的迁移决策和故障结论；普通 commit、run、临时 trigger 与一次性排障过程由 Git / Actions 保存，不在文档重复记录。

### 2026-09-27 — libXray Java/native ABI 必须成套

曾验证“官方 v26.7.28 Java bindings + 历史 API v2 `libgojni.so`”会在 JNI 初始化阶段因模型类不匹配导致 `:xray` 进程失败。因此当前构建从黄金发布 APK恢复与发布 JNI 配套的 `libXray/**` generated bindings 和双 ABI JNI，同时保留官方 AAR 的通用 `go/**` runtime。后续升级必须把 generated Java bindings 与 JNI 当成同一 ABI 单元处理。

### 2026-09-28 — TV-only 与 v7 Xray 黄金参考

项目只交付 Android TV / Leanback，输出 armeabi-v7a 与 arm64-v8a；Mobile 不是本 fork 的 Xray 验收目标。当前模块化架构不要求恢复旧版混合源码结构，但 Xray 的 normalize / display、VALIDATE / TEST / START / STOP、Binder generation / timeout、播放代理、旁路请求、失败恢复和资源释放等外部行为以 `v5.6.0-xray.5` v7 为黄金参考。

### 2026-09-29 — full-JADX 扩大外围审计边界

筛选后的 readable JADX 不是完整调用图。后续 Xray 审计必须从旧 PlayerManager / Service / security helper 反向枚举 caller，覆盖字幕、弹幕、EPG/XML、DRM、RTSP、artwork/logo、MediaSession、preload、外部播放器与手机导入等“类名本身不含 Xray”的路径。该原则已由 core/playback parity guards 固化。

同阶段 TV 网络恢复补齐普通 API client 与 playback client 隔离、Glide 动态取得新 API client、图片失败缓存复位、generation 串行恢复以及 stale task/callback 拒绝；Manifest 不再用 BootReceiver 形成第二条恢复入口。

### 2026-09-30 — 媒体边界回到公开上游

播放器与普通业务重新明确只以公开 FongMi/TV + 固定公开 FongMi/media 为主体。任何只存在于高于公开源码的 Release / APK 中、但未公开的 Dolby、MPV bridge、remote ISO、native UDF / disc navigation 等都不属于本 fork 的恢复目标。保留的媒体差异只允许是当前公开源码可构建所需的最小 compatibility adapter；Libass native 的非源码来源另见下方“构建债”说明。

最终 APK 验收同时提升为硬门槛：Xray、FFmpeg、MPEG-H、Libass 的 runtime PT_LOAD provenance 与 merged Manifest security contract 必须在 assemble 后直接验证，不能只检查构建输入。

### 2026-10-01 — 以上游完整树重新建立基线

为清除旧 `main` 中多轮维护留下的不可追溯差异，重新以 `FongMi/TV@c616c0aa3613e87529791587a9f71b78c278c991` 完整树为基线，再只应用 Xray、Android TV 网络恢复、禁用上游 APK 自更新、构建/测试基础设施及不可避免的 compatibility 差异。无法归类的普通业务差异一律恢复上游。

### 2026-10-02 — DoH race 收口并统一回 `main`

TV 待机网络审计发现 `OkDns.lookup()` 在 reset/rebuild 并发时存在离锁后重复读取 volatile `doh` 的 TOCTOU 窗口。当前实现改为在同步边界内快照本次 lookup 使用的 `Dns resolver`，再在锁外执行实际 DNS 请求，并由 `tests/test-tv-network-recovery.py` 锁定该约束。

完成源码、Xray/TV 网络、上游差异与最终构建验证后，干净重建结果成为唯一 `main` 基线。该运行代码基线已通过自动源码/native/assemble/Manifest 门槛；此后 fresh 黄金网络恢复对比只新增了 Spider cleanup 异常隔离修正，当前 HEAD 尚未为这一小修重复跑完整构建。尚未发布新的测试 Release，Android TV 真机 Xray 与待机/长后台网络恢复仍是下一层验收。

随后以当前 `main` 代码反向核对长期文档，确认全部上游同路径差异仍只落在 Xray、TV 网络恢复、禁用上游自更新、构建/测试基础设施与最小 compatibility 范围；同时修正文档中对 Xray 本地 DataSource scheme 的错误描述，并补齐 Core DNS/私网保护、Exo-only proxy 注入、Home-owned 网络恢复与实际 CI guard 清单。

### 2026-10-02 — 黄金 TV 网络恢复 fresh 对比与 Spider cleanup 修正

同一份 fresh v7 full-JADX 重新核对 `gn3`、Home 恢复逻辑、`l61`、`ha2`、`la2`、Glide 与 Spider clear。generation 来源、Home resume/focus 触发、普通 API client 与 player client 隔离、DNS/DoH 重建、异步 Spider clear、两次稳定 Internet 检查、约 500 ms 轮询与 DLNA 生命周期均与当前架构保持同一外部语义。

当前保留几项有证据支持的增强：Glide 不再永久固定旧 API client；网络恢复会清除瞬时图片失败集合；DoH lookup 在同步边界内快照 resolver；`recoveredGeneration` 使 Home 重建后只跳过真正完成过的 generation。fresh 对比同时发现 Jar/JS/Python loader 的 `forEach(Spider::destroy)` 不具备黄金版“单个 destroy 失败仍继续清理”的容错，已改为逐 Spider try/catch，并让 QuickJS module-cache clear 失败也不阻断状态清空。该修正不改变 recovery 顺序，只恢复黄金版清理失败隔离语义。

### 2026-10-02 — fresh v7 full-JADX / DEX 独立 Xray 完整性复核

为避免把旧 recovery 结论当成前提再次自证，单独用固定 `v5.6.0-xray.5` APK 再跑一次完整 recovery analysis（run `36910320478`），取得 fresh v7 full-JADX 与双 ABI DEX/dexdump。审计从完整 APK 重新枚举 Xray direct classes、AIDL/Binder glue、Service/session/settings 状态机，并以旧 `PlayerManager(th2)` 的 current-client、Xray-active 与 proxy transition 方法反向穷举所有 caller，覆盖 DRM、RTSP、字幕、弹幕、EPG/XML、artwork/logo/MediaSession、preload、外部播放器和手机导入。

结果没有发现当前 `main` 尚未映射的 Xray runtime path；旧 AIDL 六个事务与当前 `validate/test/start/stop/resetSecurity/cancel` 一一对应，5s bind、1.5s cleanup、30s startup、45s settings timeout 也由 fresh JADX/DEX 重新确认。fresh v7 与仓库 selected reference 的 3 个差异仅是 TV 网络 helper 的格式整理，已恢复为 fresh 文本；此后 63 个 `shared/sources/` 文件与 fresh v7 blob 全部一致。运行代码没有因此修改。

该结论仍限定为**已取证行为/调用链完整映射**：旧 APK 的原始未混淆 Java 源码和 libXray 原始 Go 源码并未找回。native 继续使用正式 APK 固定 SHA 的 `libgojni.so` 与匹配 generated bindings，并由此前成功的双 ABI current-chain parity 验证；最终 Android TV 真机仍是更高层级验收。


### 2026-10-03 — 第三轮只审 Xray / TV recovery 未发现新的确定 Bug

继续严格按长期维护边界只检查 Xray 与 Android TV 待机/长后台网络恢复，不扩查普通 FongMi 业务。第三轮刻意避开前两轮已反复覆盖的 START/STOP 主路径，重点复核 XrayPreferences / XrayCertificatePins 迁移、share-link normalizer、错误去敏、Binder client/Service cancel、SOCKS/RTSP socket、播放 identity、Live metadata client，以及 TvNetworkLifecycle、NetworkRecoveryCoordinator、API/DNS/DoH reset、proxy selector/auth、BaseLoader/Spider completion、Glide failure epoch 与 Home destroy/recreate。

本轮没有构造出新的确定 current-only Bug。证书 pin store 与 legacy mirror 的 prefs/字段/KeyStore alias/迁移逻辑一致；settings close/phone-import abandon 的“只 unbind、不 remote-cancel”也与冻结 legacy/DEX 行为一致，不擅自改动。VOD newIntent/换集/换源和 Live 切频道/切线路/catch-up 均确认经过 Xray identity reset；只有刚成功 START 后继续同一 pending Live channel 的恢复路径明确保留同 identity。BaseLoader.clear(after) 由 per-loader Throwable 隔离加外层 finally 保证 completion callback，不会因单个 Spider.destroy 失败永久卡住 recovery。

同时把纠偏前最终审计状态 `70b720bf...` 与 current 运行 blob 逐项反查：LiveActivity、VideoActivity、SettingActivity、ImgUtil、XrayProxySocketFactory、XrayShareLinkSecurity、XrayGenerationGate、XrayService、XrayPlaybackSession、XrayServiceClient、XraySessionController、XraySettingsController 均逐 blob 一致；唯一 XrayConfigFactory 差异就是已经由真实双 ABI `testXray` 证明不兼容、并从 current 淘汰的 `::ffff:0:0/96` runtime 增强。没有发现漏重放的其它有效 Xray/TV-recovery 修复。

仍保留两项只作为观察风险而不修改：黄金 TV recovery 的约 6 秒稳定性轮询上限，以及不主动退休 dedicated player client 的后台播放保留策略。二者都有黄金/现行边界依据，目前缺少真机或更强证据证明是 current Bug；不得仅凭理论推演再次扩张 recovery 状态机。

### 2026-10-03 — 第二轮审计纠正 Xray close 误报

第二轮只读反查重新沿真实同步调用顺序核对 `XrayPlaybackSession.close()`，确认上一轮把 owner 销毁误判成资源泄漏。实际顺序是 `close() -> end() -> stop(false) -> XraySessionController.stopSession()`；`stopSession()` 在提交 Binder STOP 后会**立即同步** `notifyState(IDLE)`，而此时 `XrayPlaybackSession.closed` 尚未置位，所以既有 `onXrayStateChanged(IDLE)` 已经同步执行 `clearResources(false)` 并关闭 `XrayHttpClient`。如果 controller 原本已是 IDLE，`XrayPlaybackSession.stop(false)` 本身也会直接清理 resources。因此 published/test.6 的原实现没有这条泄漏。

为保持纯净基线，上一轮追加到 `XrayPlaybackSession.close()` 的重复 cleanup 与对应 parity guard 已全部撤回，运行代码重新回到已发布验证状态。该纠错再次确认：后续 Xray/TV-recovery 修复必须沿完整同步/异步调用链证明问题，不能只看最终 callback 分支推断资源泄漏。

同轮继续复查 TV recovery generation / DNS-DoH reset / Spider clear / Glide epoch / Home stability poll。黄金 `l61` 本身在约 6 秒稳定性轮询上限后会结束该 generation，即使 INTERNET capability 尚未连续稳定两次；这仍保留为黄金行为/真机风险观察项，没有凭静态推演扩张 recovery 状态机。

### 2026-10-03 — 纯净基线发布验证通过并替换测试 Release

修正 native 未接受的 mapped-IPv6 runtime 增强后，重新触发 publish run `37100464365`，build source 为 `1b7976f7ddd742e65392819c4cd5013407e23545`。该 run 全部步骤通过：fork source guards、Android SDK 36/37、固定 player/native 输入重建、双 ABI 黄金 Xray native/runtime parity、reconstructed Libass candidate、Leanback compile、双 ABI assemble、MPEG-H/native provenance、最终 Manifest security contract 与 Release 发布均为 success。

发布结果为 `v5.6.3-xray.test.6` pre-release，tag target 精确指向上述 build source；资产仅有两个 Android TV APK：
- armeabi-v7a：`sha256:af4e725c59a9b92e49ce1c4391219c788c3c2d67f37e958881d70ae0cd121f39`
- arm64-v8a：`sha256:2d482e2d71de00ae7bd75186a80387acc6a2a5896a7db8a2e4453eb1a9c59168`

发布成功后已先恢复 publish workflow 为 `workflow_dispatch` only，再删除临时 marker，避免清理提交再次触发 Actions。随后只同步 README/DEVELOPMENT 文档，没有修改运行代码。当前 Release 集合只保留黄金 `v5.6.0-xray.5`、当前测试 `v5.6.3-xray.test.6` 与一份用户明确要求的最新 `source-backup-*` 源码备份；旧测试/临时发布不长期保留。自动构建已验证，但 Android TV 真机 Xray 与待机/长后台恢复仍需实际设备验收。

### 2026-10-03 — 发布 native parity 淘汰未验证 mapped-IPv6 runtime 增强

发布 run `37097786995` 在 source guards、Android SDK 准备、player/native 输入重建和 libXray AAR 准备均通过后，首次在真实黄金 `libgojni.so -> testXray` runtime validation 阶段失败；第一条 `vless-kcp-srtp-seed` 即返回与冻结 v7 oracle 不同的 response。该 case 只是 26 条 runtime validation 的第一条，current 与黄金 runtime request 唯一被测试归一化允许的结构差异是此前静态审计加入的 `::ffff:0:0/96` reserved prefix，因此这次 native 证据证明该“IPv4-mapped IPv6 私网防护”并未满足实际 Core 配置合同。

按纯净基线原则，current 已删除这条未经过 native 验证的 runtime 增强，同时移除 parity 中为它设置的特例，恢复对黄金 runtime JSON 的**完全一致比较**。黄金已有的 `::ffff:0:0:0/96` 保持不变；如未来仍要补 mapped-IPv6 安全缺口，必须先证明候选配置能被固定双 ABI `testXray` 接受，不能再仅凭静态 CIDR 推理提交。

### 2026-10-03 — 全量文档与冻结发布说明反查

重新检查仓库 7 份 Markdown（6 份项目文档 + `LICENSE.md`），并完整读取冻结的 `ORIGINAL_README.md` 后，以其用户级产品合同反查 current 源码与长期文档。确认 no-VPN、当前播放会话手动启用、VOD/Live identity 边界、节点测试/手机导入、独立 `:xray` 进程、资源释放与 TV 长后台网络恢复仍有 current 实现；v2rayN 标准单节点重新明确为主要分享链接兼容/测试目标。

同时修正文档自身漂移：只有 `ORIGINAL_README.md` 冻结，`AI_COLLABORATION.md` 必须随用户开发限制更新；**该次审计当时** Releases 尚无 `v5.6.3-xray.test.6`，只有黄金版与用户要求的 source-backup；README 的 CI SDK 列表同步为 workflow 实际安装的 Android 36 + 37.0 / Build Tools 36.0.0 + 37.0.0。RECOVERY 另修正黄金 STOP/callback 竞态的前后矛盾，并明确冻结 README 的“换地址/后台状态”是用户级概括，DEX/JADX 证据对 logical identity / resolved URL / 后台保留播放给出更精确语义。

### 2026-10-03 — 纠正 5.6.8 文档与构建边界

再次检查全部长期 docs 后确认，公开上游仍严格是 FongMi/TV 5.6.3（`c616c0aa...`）；Release/APK 的更高版本号不得被写成 current 上游或功能目标。README、PROJECT、RECOVERY 当前没有 5.6.8 基线表述；AI 协作规则与 DEVELOPMENT 已把一般性的高版本 Release 叙述改成“高于公开源码的 Release-only”。

同时确认这不是纯文档问题：current/publish workflow 仍下载 FongMi Release 5.6.8 Leanback APK，只为 Libass compatibility 提取 `libmedia3ass.so`。该路径现明确登记为**待移除构建技术债**，不是允许继续维护的第三项能力，也不能用来恢复 5.6.8 的 Dolby/MPV/ISO 等行为。当前业务源码仍只维护 Xray 与 TV recovery，但在这项 Libass 二进制输入清理完成前，不再把仓库描述成“所有构建输入也严格只来自公开 5.6.3”。

### 2026-10-03 — 回到 source-backup 后只重放 Xray / TV recovery 已确认修复

按用户要求，`main` 先强制恢复到源码备份 tag `source-backup-2026-10-02-main-6a4117c8` 对应的 exact commit `6a4117c8d52a37af117daf6c716969293400bb87`，再重新审计该点之后 274 个提交及其最终净差异。此前由静态竞态推演扩散出的 Config replay/task owner、BaseLoader barrier/Spider lease、deferred Cast/BOOT/navigation、Setting/Live recovery UI 等实验链没有重新带回；普通 FongMi Config/UI/业务源码继续以 source-backup/固定公开上游为准。

重新提交的运行代码只保留两类：

- **Xray**：VOD new-intent identity/ready-state 边界；Live XML/EPG 在 proxy install、手动关闭与 ERROR rollback 时的播放网络身份重新接管；native cleanup、Binder bind/asInterface/link/unlink/unbind/cancel/callback 的 Runtime/Linkage failure 收口；本地 proxy 安装/卸载失败后的资源与 Core 回滚；replacement START / bind-pending / failure callback 的 reentrant owner 竞态；Settings result/timeout/delete/reset 的 owner、partial-delete 与 listener 隔离；首次 TOFU pin 只在拥有该 operation/session 的成功路径提交；RTSP SOCKS connect/bind 失败时关闭新建 socket。
- **Android TV 网络恢复**：保持 source-backup 的 generation → 普通 API/DNS/DoH reset → async Spider clear → stable network → Home refresh 小边界，仅补 `ImgUtil.networkFailureEpoch`，使退休网络代际晚到的 Glide `onLoadFailed()` 不再重新污染新 generation 的图片失败集合或覆盖恢复后的图片状态。

与上述修复直接对应的 current-native/share、core/playback、ServiceClient、session/settings、transport-security 与 TV recovery source/JVM guards 一并重放。TV recovery guard 额外锁定普通 `KeepActivity/SiteApi/BaseConfig/VodConfig/LiveConfig/WallConfig/LiveParser/ConfigEvent/Notify` 必须保持固定上游 Git blob，防止后续再把恢复状态机扩散进普通业务层。

这次重放完成时尚未触发 GitHub Actions/AC，也没有把旧 run 冒充为新 HEAD 验证。source-backup 之前已有的构建/native/Manifest 证据仍只证明当时对应代码；该状态随后由 2026-10-03 的 publish run `37100464365` 完成自动验证，见后续记录。

### 2026-10-04 — 用户分享链接核验与 Xray 旁路排队回调修正

重新对照公开 `FongMi/TV@c616c0aa3613e87529791587a9f71b78c278c991`（5.6.3）完整树核查差异，恢复两处不需要改变普通上游行为的细节：`ViewModelTaskRunner.cancelAll()` 回到上游仅取消并清空 futures 的实现，保留 Xray/TV recovery 所需的定向 `cancel(type)`；`ChannelAdapter.onViewRecycled()` 回到上游实现，Xray logo 抑制继续只由专用状态及绑定路径负责。没有用高于公开源码的 APK 恢复上游功能；既有 5.6.8 Libass native 输入债仍按前述边界保留，尚未移除。

用户提供的六条单节点链接（HY2 IPv6 + mport、域名 Reality XHTTP packet-up、IPv4 Reality gRPC gun、VMess KCP、VLESS / Trojan WS TLS）与五组 IPv6/域名端点变体，均用当前真实 Java normalize/security/config 链和冻结 legacy reference 完成完全一致比较，再用 SHA 固定的黄金 v7 `libgojni.so` 执行真实转换及 `testXray` 配置校验。额外逐字段核对 server address/port、SNI、Reality 参数、Host/path、gRPC authority/serviceName、KCP seed 与 HY2 跳跃端口；没有把域名替换成导入时解析的 IP。既有 26 条 native/runtime oracle（含 6 条 KCP）也全部通过。原始用户凭据只用于工作区外临时测试，不写入源码、fixture 或文档。

固定公开 Xray Core 的 `recovery/node-dns-tests` 在本地合成 DNS/TCP/UDP 环境通过 9 个子场景：AAAA-only、双栈、IPv6 字面地址与 nil/AsIs dial 设置。该证据验证节点域名引导使用系统解析器、IPv6 字面地址不发起 DNS，且节点地址与 TLS SNI 分离；它不代表实际 Android 网络或用户节点一定可达。HY2 `insecure=1` 继续遵循黄金 TOFU 证书 pin 语义，本次配置测试使用合成证书探测结果，没有执行真实节点握手。

本轮复现一个 current Xray 集成缺陷：弹幕/字幕 HTTP 或下载完成后先清空 request owner，而 `ApiCallback.post()` 的 UI 结果尚未执行；此时开启 Xray，取消逻辑误判没有请求，旧网络结果仍会送达，搜索对话框的取消 completion 也被遗失。当前只把 owner/completion 的退休延后到 UI 结果实际执行完毕，HTTP/下载句柄仍及时清空；按 request id 收口，避免旧结果清理回调中创建的新请求。字幕 ZIP 解包后的排队交付同样受该 owner 保护，上游 `ApiCallback` 保持原样。

新增 `tests/test-xray-side-request-lifecycle.py` 用确定性 HTTP / Download / 主线程队列边界编译执行真实 API：修复前复现 stale callback，修复后 16 个场景通过，并已接入现有 playback parity guard，build/publish 无需新增 workflow 步骤即可运行。本轮本地 14 个标准验证入口均通过；证据限于源码/JVM、v7 native 配置校验与本地 Core DNS，不包含当前改动的 APK assemble、Android ART、真实播放或 TV 待机验收。未触发 GitHub Actions 或发布。

再次复核公开上游 HEAD 与当前声明版本，仍为上述 5.6.3 基线；普通 Config、Keep、SiteApi、LiveParser、Event/Notify 等源码保持上游 blob。沿弹幕/字幕调用方、Xray playback identity / START-STOP / proxy cleanup，以及 TV SCREEN/background generation → Home 串行恢复 → API/DNS/DoH reset → Spider cleanup → Glide epoch 重新检查，没有复现新的确定问题。约 6 秒网络稳定性轮询上限与后台保留 dedicated player client 继续作为已登记的真机观察项，不据静态推测扩张上游业务状态机。

### 2026-10-04 — 公开上游完整差异与两项维护模块独立复核

环境发布后的验证重跑只证明工具链和既有测试仍可执行，不能代替独立代码审查。本次另从固定公开 `FongMi/TV@c616c0aa3613e87529791587a9f71b78c278c991` 完整树重新生成并逐项读取差异：上游 1,120 个受 Git 跟踪路径中，1,061 个文件逐字节一致；57 个同路径修改（其中 42 个 Java 文件）及 2 个网站文件删除均重新检查。这里的计数不包含本项目新增的 Xray、恢复、兼容层、测试与冻结取证文件，不能据此声称所有新增代码也来自上游。

保留差异逐项核对其 Xray、TV recovery、禁用 APK 自更新、构建基础设施或公开 media API 兼容理由。额外直接读取固定公开 `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d` 的 `MpvPlayer`、`MpvPlayerConfig`、`MpvSubtitleOptions`：该版本没有 current app 调用所需的 secondary-track selection/reset/suppression 等接口，因此现有选轨与字幕位置适配不能作为无关业务修复直接删除。前一轮恢复的 `ViewModelTaskRunner.cancelAll()` 和 `ChannelAdapter.onViewRecycled()` 继续保持公开上游实现；没有新增普通 Config、导航或播放器功能状态机。

Xray 复核覆盖 normalizer/security/config、Service 单线程运行与 operation/session gate、Binder 绑定/死亡/超时、settings/save/delete/reset、播放 identity、Exo/DRM/RTSP 注入、弹幕/字幕/EPG/XML、artwork/logo/preload 以及停止、失败和 owner 销毁的实际调用顺序。再次排除几种仅看局部代码产生的误报：上游 `ProxyRedirectInterceptor` 只有未显式设置 proxy 时才重新选路，故不会覆盖 Xray 明确设置的 SOCKS；`close()` 通过同步 IDLE 回调先卸载代理，再置 closed；清空预加载请求后，已排队的 preload 结果仍需通过 controller 的 pending-request 匹配。没有把上游通用 `LiveData.postValue()` 改造成另一套交付机制，也不以取消 Future 代替对观察者/request identity 的检查。

TV recovery 复核覆盖 SCREEN/background generation、配置重建排除、Home resume/focus、清理期间 generation 再变化、销毁后的 completion/poll、普通 API 与 player client 隔离、DNS/DoH reset、Jar/JS/Python destroy 异常隔离、Glide 动态 client 与失败 epoch。锁顺序沿实际 Startup DoH supplier 反查，该 supplier 读取设置并构造 DoH 数据，没有反向获取 OkHttp 锁；没有仅凭类之间的理论调用关系添加锁或 loader barrier。

本次独立审查未复现新的确定运行缺陷，没有追加运行代码修复。重新执行 session-races、service-client-lifecycle、playback-parity（包含真实弹幕/字幕 API 的 16 个确定性场景）和 TV-network-recovery 四个针对性入口，均通过；这些证据包含真实 Java 类配合 Android/Binder/网络边界替身的 JVM 测试与源码合同检查，不等于 Android ART、APK assemble 或 TV 真机运行。本次没有重跑 native 节点连通性或触发 Actions。

第 2 点仍有明确构建例外：现有 Libass compatibility 输入从 5.6.8 APK 提取固定 hash 的原生库，且存在为兼容重建的 media 接口；它不是公开 5.6.3 源码本身。该技术债并未因此消失，也不能作为继续跟进更高版本 APK 功能的依据。约 6 秒恢复轮询上限与后台保留 player client 仍沿用已取证行为，留待真机验证，不宣称当前代码无 Bug。

### 2026-10-04 — 独立恢复模块与集中 FongMi 接线

按用户要求进一步独立维护两项自有能力，新增 `:tv-recovery` Android library，将 `NetworkRecoveryCoordinator` 与 `TvNetworkLifecycle` 移入 `com.fingmi.tvrecovery`。恢复协调算法保持原样；lifecycle 中的 DLNA 服务调用替换为宿主提供的 `Renderer` 接口。模块只依赖 Android/annotation，不引用 FongMi、catvod、Xray 或应用适配类。既有 coordinator 单元测试随核心移入模块。

新增应用自有 `com.fingmi.integration.recovery.FongMiNetworkRecovery` 适配器，集中普通 API/DNS/Glide reset、Spider clear、系统网络能力判断、主线程调度、已恢复 generation 标记及 flavor DLNA 接线。Home 只提供页面取消、进度、存活判断、刷新回调，并保留原有 resume/focus/check/destroy 调用；普通 FongMi Config、SiteApi、播放器业务等没有随拆分重写。Xray 核心继续独立维护在既有 `:xray`，应用封面适配 `XrayArtworkBitmapLoader` 仅移动到 `com.fingmi.integration.xray`，行为未改。Xray 核心版本、JNI/bindings、转换/security/runtime 配置、固定 native 来源及 workflow 均未调整。

新增模块边界与实际适配器 JVM 验证，分别编译执行 Leanback/Mobile 接线；既有 14 个本地验证入口全部通过。实际执行 `:tv-recovery:assembleDebug :tv-recovery:testDebugUnitTest` 成功，独立 AAR 生成、Android Java 编译与两个迁移的 JUnit 测试通过。云端 Gradle 使用当前 session proxy 和系统 CA 信任，不为此修改上游 Gradle/toolchain 设置。本次没有构建完整应用 APK、触发 Actions、更新核心版本或发布 Release，Android 真机验收仍未完成。

后续上游同步应保留两个核心模块，先采用公开 FongMi 树，再核对应用自有适配层及页面/播放器所需接入点。核心独立不意味着零上游接线：网络资源、播放器与 UI 属于宿主，接口变化仍需适配与回归验证；不得因此接管普通上游业务或把网络恢复并入 Xray。

### 2026-10-04 — 云端完整 TV APK 构建与模块拆分接线修正

用户明确要求本地编译并上传 Release。本次完整 Leanback javac 发现拆分恢复模块时误删了 HomeActivity 的 `ImgUtil` import，而上游 `ImgUtil.logo()` 调用仍保留；仅恢复该 import，不改变上游 logo 或恢复流程。此前核心/适配器 JVM 验证没有编译完整 HomeActivity，不能代替应用编译。固定 Media3 container AAR 加入构建产物忽略规则，二进制不提交 Git。发布 workflow 仍为纯手动，当前测试目标推进为 `v5.6.3-xray.test.7`。

固定公开 FongMi/media 17-AAR candidate 已在云端重建成功；Libass 的 10 个真实 Robolectric 测试通过，extractor SHA-256 `feb8be30e3d431391ce4b3b165a6cbfb18313969d7ba7da2d6ccfeb96d25ee68` 与 candidate SHA-256 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861` 均符合仓库固定值。最初 Robolectric 因只读用户目录失败，改用可写 Java user.home 后通过，没有为此更改上游源代码。既有 14 个 source guards 及 ARMv7/ARM64 各 26 个真实黄金 JNI 转换/runtime 用例均通过。Xray v26.7.28 与两 ABI 黄金原生库保持原样，FongMi 公开源码基线仍为 5.6.3。完整 Leanback javac 重编译与 APK assemble 均成功，APK build source 为 `631cbcf0948370bdbf8c4a337d44fbd979c68485`。

两个完整 APK 的最终 Xray / FFmpeg / MPEG-H / Libass ELF 运行段均匹配验证过的 AAR；双 ABI 单独打包，DEX 包含 Xray service、独立 recovery core 及 app adapter；Manifest、apksigner 与 16 KB page zipalign 校验通过。该源码重新跑完 14 个标准验证入口。本轮没有 Android ART 启动、真实节点握手、播放或 TV 待机验收。

| 本地完整测试 APK | SHA-256 |
| --- | --- |
| armeabi-v7a | `44385f3a3a7b62d0b894efa7020eb253de310d08b5eaa751523272764c20ffdd` |
| arm64-v8a | `5915528ac25ac4ee6f09391275868c119fd1d6123253970a01862b86292ae05e` |

两 APK 使用同一云端 Debug 测试证书 SHA-256 `0d71ccd96f6c91f8e3d1e9c9e7f37d5e1c3ce4b4bb407a0a7d85ade1475a6c2b`，与黄金版及 test.6 证书不同，不能覆盖安装；测试前需备份配置。该证书不等同历史正式发布签名。完整 APK 保存在本地 `app/build/outputs/apk/leanback/debug/`。

云端向 GitHub uploads endpoint 的直接发布失败：GitHub CLI、urllib 与 curl（HTTP/1.1、HTTP/2）均返回 HTTP 400 `Bad Content-Length`；1 KB 和更小的临时未发布探测也同样失败，未留下任何远端资产，不能归因于 APK 内容或文件大小。保持原测试 Release，清理本轮空草稿后，仅尝试一次已有纯手动 publisher 作为必要发布替代；该路径会重新构建，必须以它实际产出的 source / digest 为准，不能把上述本地 APK hash 当作 Actions 发布资产 hash。

### 2026-10-04 — 再次逐项上游审查与 Hysteria2 备注边界修复

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

### 2026-10-05 — 模块取消、资源关闭与网络边界复查

再次刷新公开 FongMi/TV HEAD，仍为 5.6.3 的 `c616c0aa3613e87529791587a9f71b78c278c991`。重新计算当前 tracked tree 差异，仍为 1061 个同路径相同文件、57 个修改文件、2 个删除文件、376 个新增文件；宿主、网络恢复、媒体兼容及 libXray 输入的 blob 自上一轮逐项审查以来均未变化。复查 Service/Binder 的取消与代际门控、START/STOP 替换、播放代理卸载、媒体旁路回调、Loader 清理、API/DNS/DoH 重建及 Home 销毁后的迟到回调，没有复现新的确定运行缺陷，也没有追加普通上游修复。既有 Libass 构建债仍未移除。

补跑真实 Gradle 单元测试发现一条过期 Xray 断言：`livePendingResolverRetainsCurrentIdentity()` 仍期待临时 URL 解析成不同最终 URL 时 `resolved()` 返回 false。历史提交 `59e231f` 已将该接口语义改成报告 URL 变化，同时保留播放 identity/generation；生产调用方不再用此返回值关闭代理，当时漏同步了该测试。仅修正测试预期，并补充最终 URL 与重复解析不变化的断言，保留 generation 不变及换线清空 URL 的原有检查；不改运行代码。`bash gradlew :xray:testDebugUnitTest --rerun :tv-recovery:testDebugUnitTest --rerun --offline --no-daemon` 随后成功，XML 确认 Xray 3 项、recovery 2 项实际执行，失败、错误、跳过均为 0。既有 14 个标准本地验证入口全部通过；这些入口此前并不包含 Gradle JUnit，不能把它们的通过等同全部模块测试通过。

另在仓库外编译真实当前 Java，验证 1188 组 Hysteria2 域名/IPv4/IPv6、默认/跳跃端口、真实 query、literal/encoded 备注组合，参数隔离与重复规范化均通过。用真实 `XrayProxySocketFactory` 对本地 SOCKS5 测试服务执行 8 次握手，验证不可本地解析的域名仍以域名交给代理、字符串 IPv4/IPv6 和 InetAddress overload 的目标地址及端口正确、local bind 与无参 socket 路径正常。再执行固定 v7 Go JNI 的 6 个 VMess QR insecure 字段边界，生成的 TLS `allowInsecure` 均为 false，排除该组输入绕过 security query 处理的疑点。这些是宿主 JVM/环回 socket 和 QEMU native 的验证，不包含 Android ART、真实远端 DNS/节点握手、APK assemble 或电视息屏/长后台验收。本轮 Xray 核心版本、运行源码和发布资产不变，未触发 Actions。


### 2026-10-05 — 集中复查与验证入口补齐

重新读取公开 FongMi/TV HEAD，仍为 `c616c0aa3613e87529791587a9f71b78c278c991` / 5.6.3。再次生成完整 tracked-tree 差异并逐项读取 57 个修改文件；审查起点的 1061 个同路径相同文件、2 个删除文件和 376 个新增文件与上一轮一致。新增应用类另按 Xray、恢复 flavor/资源适配及固定公开 media 缺失 API 的兼容用途核对。普通上游业务不追加修复，既有 MPV/字幕兼容接线和 5.6.8 Libass 固定 native 输入债没有被当作公开上游源码，也未进一步扩大。本轮没有反编译 APK 或更新 Xray，AAR 中双 ABI Go JNI 与既有黄金 hash 逐字节一致。

集中核对 normalizer/security/config、Service/generation、Binder 与设置取消、播放身份/代理卸载、媒体旁路回调，以及恢复 lifecycle → Home adapter → API/DNS/DoH → Spider → Glide 的实际调用链，未复现新的确定运行缺陷。两个独立核心没有反向引用 FongMi 业务；宿主仍保留必要接线。本轮不修改运行源码，修改只涉及测试、手动构建验收与文档。

这次把已有验证层一起执行并明确区分：

- 14 个标准 source/JVM/验证器自测入口通过；其中包括真实弹幕/字幕 API 的 16 个排队回调场景及 Leanback/Mobile 恢复适配 JVM 检查。
- 实际 Gradle JUnit 强制重跑：Xray 3 项、recovery 2 项，XML 的失败、错误、跳过均为 0；完整 Leanback Release Java 编译单独 `--rerun` 成功。
- 双 ABI 各 26 个 current Java → 固定黄金 JNI → current runtime → native `testXray` 用例通过；另各 5 个备注边界用例通过。
- 仓库外补查 1188 组 Hysteria2 备注参数隔离/幂等组合及 8 次实际 JVM/环回 SOCKS5 握手，域名交给代理及 IPv4/IPv6 地址、端口、local bind 正常。
- 新增 `test-xray-service-execution.py` 编译执行真实 Service/gate/sanitizer，9 个确定性场景通过：正常启停、live 时拒绝测试、准备期间替换/停止、无法交付启动回调后的清理、停止失败时仍运行 Core 的防护、取消重置私有进程请求及取消后禁止信任写入。Android/native/config/pin 为替身，不冒充真实 Binder/ART；已接入现有 core parity 入口。

前轮遗漏 Gradle JUnit 属于验证流程缺口。现有两个手动 build/publish workflow 的编译步骤加入两个模块的 JUnit tasks，并由 build-hygiene guard 要求保留；这补齐未来手动验收，不改变触发方式，本轮未触发 Actions。README 删除误留的 test.6 校验值，改为引用本文件中经 GitHub 实际资产 digest 核对的 test.7 表，避免重复维护。历史 test.6 记录仍保留其原资产摘要。

这些证据不包含当前 APK assemble、Android ART、真实远端节点握手/播放或 TV 息屏、Fast Start、长后台验收。约 6 秒恢复轮询上限、后台保留 player client 及 Libass 输入债仍是已登记的限制；已发布 test.7 也仍不包含后续 main 的备注修复。不得把本轮未发现新的确定缺陷表述为所有场景无 Bug。

### 2026-10-05 — 复查测试有效性与上游边界

再次读取公开 FongMi/TV HEAD，仍为 `c616c0aa3613e87529791587a9f71b78c278c991` / 5.6.3；复查起点 main 为 `b3e5cf2`。重新生成 tracked-tree 清单：1061 个同路径相同文件、57 个修改文件、2 个删除文件、377 个新增文件。前三类路径与前轮逐项审查清单一致，新增清单只多了前轮的 Service 执行测试。另逐字节核对 `app`、`catvod`、`xray`、`tv-recovery`、`libxray`、`compat` 的 Git diff，自 `b7a30ba` 起没有运行源码或输入变化；双 ABI Go JNI 仍与固定黄金文件完全相同，未更新核心或反编译 APK。

本轮重新阅读 Service/gate 的失败清理、取消与信任提交，Binder client 的断连/回调代际、设置取消与重入，以及 recovery lifecycle/coordinator → Home adapter → API/DNS/DoH 的关闭与恢复接线，没有复现新的确定运行缺陷。独立核心仍不反向依赖 FongMi 业务，宿主保留必要适配；没有发现需要新增恢复的无关上游修复。既有 MPV/字幕公开 media API 兼容和 Libass 的 5.6.8 APK 固定 native 输入债仍存在，不能宣称所有输入都只有公开 5.6.3。

为确认测试能捕获错误，在仓库外临时副本中分别移除五处保护，真实 Java 编译均成功，原测试随后分别在预期行为断言失败：运行中禁止测试、无法交付 START 回调后的核心清理、取消操作的归属判断、恢复 owner 关闭后的迟到清理回调、失效 Home 禁止刷新及标记恢复。每组独立运行，未改仓库运行代码，也不把人为注入的错误计作产品 Bug。正向 14 个标准验证入口、其中真实 Service 的 9 个场景，以及强制重跑的 Gradle JUnit（Xray 3 项、recovery 2 项，失败/错误/跳过均为 0）全部通过；Leanback Release Java 编译 `--rerun` 成功。双 ABI 各 26 个固定 JNI 转换/runtime/native `testXray` 黄金用例，以及各 5 个备注边界链用例重新执行通过。

本轮只有审查记录修改，没有新增运行修复、改测试预期、触发 Actions 或发布 APK。证据仍限于本地编译、宿主 JVM 与 QEMU native；Android ART/Binder、真实节点握手/播放及电视息屏/长后台恢复仍需要真机验收。不能用反向验证通过代替这些设备层验证。


### 2026-10-05 — 正式发布命名与持久签名

按用户要求，将显示版本和 Release tag 统一为 `v5.6.3-xray.1`，Android versionCode 设为 `563001`，新增固定 RSA-4096 发布签名并按授权连同恢复配置保存到私有项目。软件设置直接显示既有 `BuildConfig.VERSION_NAME`，无需修改上游 UI。Xray-core、公开 FongMi 源码基线及两个模块业务行为不变；此次差异限于版本/签名、构建与发布验证、对应文档。

旧 `test.7` 对应 `439cea8`，源码备份对应 `41896214`，均早于本次来源；正式 APK 包含后续 Hysteria2 备注解析修复。手动 current-main/build 与 publish 入口改用 Release variant 和持久签名，保持纯 `workflow_dispatch`；原生库验证器支持上游 Release finalizer 的实际文件名，新增签名/版本/non-debuggable/16 KB alignment/内嵌 Git revision 校验。签名验证器同时支持 Build Tools 37 的 `V2 Signer:` 格式，并用旧临时签名 APK 验证拒绝路径。

完整本地 Release 混淆、资源压缩、Lint 与 assemble 已通过。首次离线运行缺少 Lint 传递依赖 `stax-api` / `xpp3`，联网补齐后成功，没有禁用检查或修改上游业务。14 个 source/JVM/验证器入口通过；实际 JUnit 强制重跑 Xray 3 项、recovery 2 项通过。双 ABI APK 的版本与同签名、Manifest 安全接线、四类原生库 PT_LOAD、单 ABI 打包、MPEG-H class/native 及 16 KB 对齐通过。提交后再次打包，以保证 APK 内嵌 Git revision 与发布 tag 的构建源码完全一致；最终 digest 以 Release 资产为准。正式状态是发布渠道选择，Android ART、真实节点、电视覆盖安装与待机/长后台恢复仍未实测。

旧发布及旧备份仅在新 APK / 新 tracked-tree ZIP 的远端 digest 与 tag 核对后清理。新源码备份包含签名文件和恢复配置，不包含临时产物；签名不可重建，后续维护必须复用并由用户保留离线副本。

### 2026-10-08 — 独立复核上游边界与七条用户分享链接

本轮重新读取项目文档并读取远端源码基线；公开 FongMi/TV HEAD 仍为 `c616c0aa3613e87529791587a9f71b78c278c991` / 5.6.3，审查起点为 `3fab84a`。重新生成完整 tracked-tree 差异：1061 个同路径文件完全一致、57 个修改、2 个删除、381 个新增。审查分别沿上游差异、Xray 生命周期与安全配置、TV 恢复及分享链接转换链展开，不将旧测试记录当作本轮通过证据。

57 个修改文件逐项检查后，未发现本轮需要再恢复的无关上游业务修改。另读取固定公开 media 的实际 MPV API，确认现有兼容映射对应公开源码缺失接口。9 个普通 Config/API/UI 文件及先前恢复的通用取消/频道回收方法仍保持上游；两个核心模块没有反向依赖宿主。既有 Libass 高版本 APK 原生库构建债仍存在，本轮不反编译更高版本 APK、不引入其业务行为。

七条用户链接加 30 个 IPv4/IPv6/域名、跳跃端口与编码变体，在双 ABI 各完成 37 例 current Java → 固定黄金 JNI → current runtime → native `testXray`；744 项字段断言通过，归一化、安全转换与 runtime 配置均与冻结恢复 Java 一致。特别确认 Argo 的连接域名与 TLS SNI / WS Host 分离，`/?ed=2560` 保留正确；HY2 IPv6 / 跳跃端口、Reality XHTTP / gRPC、VMess KCP seed 及 VLESS / Trojan WS 参数同样通过。双 ABI 各 26 项冻结 native oracle 通过，当前 AAR 中 JNI 与黄金文件逐字节相同。固定公开 core 的本地 DNS / IPv6 TCP / UDP 9 个子场景另通过；这是源码与环回环境证据，不能替代 Android 上的实际节点解析。真实用户凭据只作仓库外私有测试输入，未连接用户服务器；证书探测及 pin 存储为确定性边界。

本轮确认并修复一个独立于节点导入的 Xray 问题：公网 IPv6 **媒体 URL** 的 `URI.getHost()` 包含 `[]`，真实 destination guard 只接受裸 IPv6，VOD / Live 因而拒绝启用 Xray。旧测试共用简化 guard，掩盖了这处真实组合缺陷。本轮先替换为真实 current / legacy guard 并得到预期失败，再只修 `XrayPlaybackAddress` 的 URI 边界；135 个回归场景随后通过，私网/保留/zone/mapped 地址继续拒绝。黄金 APK 原始 DEX 也直接传递带括号主机，这是已登记的有意修复，证据与历史差异见 [RECOVERY.md](RECOVERY.md#公网-ipv6-播放地址current-有意修复)。不改 FongMi 业务文件、核心配置或冻结 oracle。

修复后重新执行 14 个标准 source/JVM/验证器入口，全部通过；Gradle JUnit 强制重跑 Xray 3 项、recovery 2 项，失败/错误/跳过均为 0，Leanback Release Java 编译强制重跑成功。另以真实 Service 和替身平台/native 执行 3 个销毁故障场景，覆盖正常停止、stop 连续异常、prepare 阻塞后的中断及禁止启动/信任写入；恢复核心另验证 8192 种网络稳定性序列、27 个代际/关闭场景及 5000 轮前后台/息屏/配置重建组合，均通过。没有复现其它确定的 Xray 资源释放或待机恢复缺陷，不据理论竞态扩张上游状态机。

本次只更新源码修复、对应测试及证据文档；RECOVERY 中遗留的拆分前归属说明也已纠正。Xray 核心、应用版本与固定签名保持不变，未触发 Actions 或重发 APK；已发布 `v5.6.3-xray.1` **尚不包含本轮公网 IPv6 媒体地址修复**。测试不包含 Android ART/Binder、真实节点握手/播放、设备 RSS 或电视待机/长后台验收；约 6 秒恢复兜底与后台 player 保留仍是既有设备观察项。

### 2026-10-08 — 发布前全新复查与同名替换流程

按用户明确要求，以 `6e7ac98` 再次独立读取当前源码与公开上游，重新验证模块边界、135 个真实地址检查场景、7 条链接及 30 个变体的双 ABI 配置链；未确认新的生产缺陷。额外使用真实 OkHttp 5.5.0 与环回 SOCKS 验证运行/排队请求取消、keep-alive 连接回收、基础 client 隔离和公网 IPv6 请求路径，两场景通过。恢复部分新增多 Home owner 的 6 种回调交错及网络/DLNA 异常测试，真实 OkDns / Doh / OkHttp 完成 100 轮重建；确认派生 DoH client 与被清理的 transport 共享池和 Dispatcher。固定公开 core 的 3 个 WS Build 场景确认 `ed` 提取为 early-data 大小并从握手 path 移除。Android 平台/调度仍为明确替身，不等同真机验收。

本次用户明确授权 GitHub Actions 编译，并作为单次例外同名替换 `v5.6.3-xray.1`、更新旧 `source-backup-2026-10-05-main-357402dc`。版本名称、`563001` 与正式签名保持不变；发布器补齐同源码备份、草稿逐资产校验、旧包 rollback 保留及验证后清理，避免构建/上传失败先丢失现有版本。源码备份名称按实际构建 SHA 和 UTC 日期生成；最终是否发布成功及产物摘要以完成后的 Actions / Release 核验为准，准备流程不代表发布已完成。

### 2026-10-08 — Actions 工具链故障与 Xray 内存复核

实际 Actions 失败发生在 Gradle daemon 启动阶段，尚未进入应用编译：workflow 安装 Temurin 21，而公开上游 `gradle-daemon-jvm.properties` 要求 JetBrains 21，备用 Foojay 下载地址返回 HTTP 400。两个 current-main build/publish 入口改为通过 `setup-java` 预装 JetBrains 21，并在 player/native 重建前用禁止自动下载的 `gradlew help` 实际启动 daemon；保留上游工具链条件，不更换 Xray core、版本或签名。官方 JBR 21.0.11 下载已按官方 SHA-512 校验；全新独立缓存下正向 daemon 启动通过，普通 OpenJDK 21 的负向控制按预期拒绝 vendor 不匹配；没有生成 player/Libass/libXray AAR 的干净 tracked tree 同样通过 `help`。失败 run 尚未执行发布步骤，旧正式包及旧备份保留。

同一官方 JBR 下强制重跑模块 JUnit 与 Leanback Release Java 编译通过，XML 确认 Xray 3 项、TV recovery 2 项，失败、错误、跳过均为 0；build hygiene 与 9 个发布事务测试通过，两个 workflow 的 YAML 和纯手动触发结构通过检查。本地编译通过不等同于新 Actions 已完成 assemble / 发布。

内存专项重新组合真实 `XraySessionController` 与 `XrayServiceClient` 执行 9 类共 9000 次启停、绑定失败、超时、重入与迟到回调序列，终止后 binding、DeathRecipient、pending 引用及 Handler 任务均清空。真实 OkHttp 5.5.0 与本地 SOCKS/HTTP 完成 102 次资源生命周期，FD 数 `13→13`，204 个弱引用跟踪对象全部可回收；另一个独立宿主验证完成 10 次活动/空闲连接关闭和 250 次 client 创建销毁，连接池与请求计数归零，普通 player client 不受影响。真实 Service 的 4 类销毁故障验证包含停止异常、准备阻塞及忽略 Java 中断的边界，均到达最终私有进程终止请求。这些没有复现持续泄漏；Android/Binder/native 使用明确替身的部分只能证明清理路径，不能冒充电视 ART、真实进程退出或 PSS/RSS 实测。

沿实际宿主顺序复现并修复两处 Xray 接线缺陷。首次页面初始化先配置弹幕 view、后请求绑定播放服务，原 fork 的 client 选择无条件调用 `player()`，导致服务为空时 NPE；改为未绑定时沿用上游 `OkHttp.player()`，绑定后继续选择当前播放 client。另一处是新播放页改变共享播放器 key 后，旧页 `onStop` 的 owner 检查不再成立，可能关闭 HTTP 资源却未卸载共享播放器的旧代理。实际编译的 PlayerManager / PlaySpec / XrayHttpClient 组合复现了对已 shutdown client 的保留；新 binding 交接钩子在新页播放任务前同步结束旧 Xray。新增回归分别在修前以 NPE、移除交接钩子时以旧资源未释放断言失败，修后通过。改动只落在三个宿主文件的 Xray 必要接线，不改上游 `PlaybackService`、`PlayerManager` 通用逻辑，也不为上游自身问题追加修补。

两处宿主修复完成后，重新执行 14 个标准验证入口（包含新增初始化/交接回归）全部通过；官方 JBR 下 Leanback Release Java 再次强制编译通过，发布事务 9 项通过。Xray 模块源码、核心 AAR、TV recovery、版本和签名均未变化；完整 APK assemble 和远端替换仍由授权的手动 Actions 流程执行，以实际 run 及资产核验为准。

### 2026-10-11 — Actions 磁盘峰值修复

继续处理前次发布失败。真实 runner 的 JetBrains 安装、daemon 预检、源码 guard 和双 ABI Xray native chain 已通过，随后 Robolectric 下载 Android 测试运行库时返回 `java.io.IOException: No space left on device`；这是磁盘耗尽，不是十条 Libass 用例分别出现行为错误。既有清理位于 Libass 测试之后，两个完整 native harness 同时占用空间；本地相同目录的实占约为 v7 2.7 GiB、arm64 3.5 GiB（用于说明规模，不冒充 runner 的实测剩余容量）。

两个 current-main workflow 将清理提前到各自消费者完成后，避免两个测试运行环境同时长期保留；仅删除本次工作目录下已使用完的输入，不清系统工具链、依赖缓存、当前 AAR 或签名。build hygiene 在隔离临时目录执行真实 cleanup shell，验证已消费 Xray 文件删除、后续 Libass 输入及 AAR 字节完整，并检查清理位于验证之后、Maven 之前。所有测试、固定 hash 与发布校验保持开启，workflow 仍只手动触发。

官方 JBR 21.0.11 下以新外部目录重新完成 Libass 构建，Robolectric 10 项通过，失败、错误、跳过为 0；extractor SHA-256 仍为 `feb8be30e3d431391ce4b3b165a6cbfb18313969d7ba7da2d6ccfeb96d25ee68`，candidate 仍为 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861`，双 ABI native / Java contract 通过。本轮不修改运行源码、公开上游基线、Xray 核心、版本或固定签名。

另完成包含前轮两处宿主修复的本地双 ABI Release assemble，实际执行 R8/L8、打包及签名，原生库运行段、Manifest、固定证书、`v5.6.3-xray.1` / `563001`、non-debuggable、16 KB 对齐和内嵌源码核对均通过。此本地 APK 来源为 `950d8a6`，只作为完整构建证据；远端最终包由提交构建流程修复后的 Actions 重新产出，不能复用本地摘要冒充其结果。清理回归、9 项发布事务测试、YAML 与 Bash 语法检查通过；设备安装及电视运行仍未实测。

### 2026-10-11 — 下载输入失效与冷入口恢复修复

后续 Actions 已通过工具链预检和公开 media 的 17-AAR 构建，失败点是既有 5.6.8 APK 下载 HTTP 404；这次不是 artifact 配额或 runner 磁盘错误。已保存必要失败证据并按用户授权清空 Actions artifacts，核对 artifacts/caches 均为 0。一次性提取后清理的长期授权写入 AI_COLLABORATION；10 日新增的非 canonical 临时审查文档早已删除，没有新增验证结果或运行源码变化，不重新创建。

本项目现有正式双 ABI APK 内的 Libass SO 与原固定输入逐字节一致；正常构建改为一次选定当前正式 Release、按资产 ID 下载并校验两份 SO。容器摘要与来源如实记录，原始上游整包校验模式仍保留，固定 native/candidate 摘要不变。先校验可用输入再执行昂贵 player 构建，禁止用新版本 APK、修改 hash 或放松最终校验来绕过故障；来源债和历史重建限制见第 6 节。

新鲜公开 TV tree 对照仍为 5.6.3，逐项复查现存宿主差异，没有确认需要恢复的无关业务修改。恢复模块则复现了可达的冷 Live → 首次 Home 晚注册问题：旧 Live 的 STOP 误扣可见 Home，错误进入后台且漏掉 SCREEN 恢复代际。只改独立核心的 Activity 身份配对及销毁引用清理；旧核心负向回归明确失败，新核心双 flavor 回归、8192 种稳定性序列、27 个迟到回调场景、5000 轮生命周期组合和 Recovery JUnit 2 项通过。普通上游 App/Home 不变。

Xray 当前源码重新验证 9000 次 Controller/Client 清理序列、102 次真实 OkHttp/SOCKS 开关（FD `13→13`、204 个弱引用可回收）及四类 Service 终止边界，未确认新泄漏。七条分享链接与 30 个变体在 arm64 完整 native/runtime 链通过，372 项字段断言、26 项冻结 oracle、本地 DNS/IPv6 TCP/UDP 9 项和 WS early-data 3 项通过。当前云主机高 PID 触发 API24 ARM32 Bionic 旧 mutex 的 16 位 owner TID 限制，v7 harness 在进入链接转换前阻塞；本轮本地不能声称双 ABI 均通过，Actions 仍保留原双 ABI 验证门槛。没有连接用户节点，也没有修改 Xray 核心或签名。

修改后的 Xray JUnit 3 项与完整 Leanback Release Java 强制重编译通过，14 个标准验证入口、发布事务 9 项及 native 输入边界 13 项通过。新的资产 ID 下载入口已实际下载双 ABI 并验证；官方 JBR 下分别用保留正式包和原上游容器完整重建 Libass AAR，两份产物逐字节相同，SHA-256 仍为 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861`，49 个类及双 ABI JNI 合约通过。JVM/环回与边界替身证据不代替电视 ART、真实进程 PSS/RSS、握手播放、息屏或 Fast Start 验收；新 APK 与源码备份的最终替换以实际 Actions 成功和远端资产核验为准。

### 2026-10-11 — 编译通过后的草稿发布 API 修复

包含前述修复的 `943357e2` 已在 Actions 完成公开 media、Libass、双 ABI Xray native、模块测试、TV 编译与 Release assemble；最终 native、Manifest、固定签名、版本、源码标识和对齐检查全部通过。双 ABI 各 26 个黄金 native/runtime oracle 也通过，补足本地 v7 高 PID 环境无法启动 harness 的验证限制。失败发生在最后发布阶段，两个正确的新 APK 已上传至草稿，旧正式版未切换。

根因是发布器用 `GET releases/tags/<tag>` 读取草稿，真实 API 返回 404；`GET releases/<id>` 则能读取正确草稿。原测试替身错误地允许按 tag 读取 draft，漏掉了此边界。修复新草稿和旧版 rollback 草稿的 ID 校验，保留全部状态、资产和 Git ref 检查，测试替身按真实 API 行为调整。16 项发布事务测试通过；修前代码在新回归中明确复现原错误。

补充仅续发原已验收资产的手动入口，避免为发布工具修复重复编译应用。11 项来源与失败注入测试、build hygiene 和 workflow 语法检查通过；真实只读演练已走完原 run/jobs、artifact ZIP、草稿资产 ID 下载、APK 摘要/源码/固定签名/Manifest 核验。Actions artifact ZIP 下载使用 JSON API 的默认 Accept，Release 资产下载才使用 octet-stream；两类 API 区分已由实际请求及回归约束。本次没有修改应用、Xray、恢复模块、公开上游版本或签名，续发 APK 和配套源码备份仍准确对应原构建 `943357e2`，不冒称来自后续发布工具提交。

续发 Actions 已成功完成：`v5.6.3-xray.1` 为非预览且 latest，两个资产 ID/摘要与原 Actions 构建报告一致；配套 `source-backup-2026-10-11-main-943357e2` 已发布，下载后的 ZIP 摘要及全部 1507 个 tracked blob（包括固定签名恢复文件）逐项核对通过。旧正式包、指定旧备份、stage/rollback 临时 Release 和 tag 均在最终验证之后清理。保存失败排错证据后删除已消费的 Actions 报告，artifacts/caches 再次核对为 0。发布工具修复和后续记录留在 main，APK/备份的构建源码身份保持原样；真机验收边界仍不变。


### 2026-10-11 — 直播初始化缺少基础解码模块

用户真机报告 `NoClassDefFoundError: androidx.media3.decoder.DecoderInputBuffer`。复核正式版双 ABI APK，确认最终 DEX 引用了但未定义 12 个基础 decoder 类型；播放器重建脚本只导出 17 个 AAR，漏掉公开固定 Media3 源码已有的 `lib-decoder`。AAR 的 `classes.jar` 不内嵌 Gradle 的项目传递依赖，复制依赖方 AAR 并不能自动包含 decoder。Android 默认 ProGuard 配置中的 `-dontwarn androidx.**` 使该缺失没有阻止 R8 出包，已有 `-keep DecoderInputBuffer` 也不能创建未输入的类。这是本 fork 构建集成遗漏，不是应在上游播放器业务中修补的问题。

本轮修复补齐同一固定公开源码的基础 decoder 产物，并补充依赖集合与最终 DEX 定义/引用的校验。验收必须先证明旧正式 APK 会被新检查拒绝，再验证修复包；原来的 assemble、签名、原生库和 Manifest 通过结果不能替代 Java 运行时链接完整性。设备直播/点播与实际解码验收仍需与云端证据区分。修复前后运行对照中，原 24 个 AAR 摘要完全不变，仅增加固定公开源码编译的 decoder：修复前 Java 编译通过但 4 项运行用例均失败；修复后 API 28/35 的真实普通音视频/文本、FFmpeg 音视频、MPEG-H renderer 构造及 ExoPlayer 重复创建/释放共 4 项通过，失败、错误、跳过均为 0。最终 DEX 检查器在两个实际故障 APK 上均明确拒绝 12 个缺失类型；检查器 12 项回归及候选依赖 9 项回归通过。完整固定公开源码的 18 个 AAR 已重建并通过符号依赖校验。此次修补按正常版本规则推进为 `v5.6.3-xray.2` / `563002`，不沿用此前 `.1` 同名替换的一次性例外。随后本地完整 Leanback Release assemble（R8 混淆与资源压缩开启）通过，双 ABI 最终 DEX 中被引用的 46 个 Media3 类型均有定义，三个显式保留 buffer 均存在。双 ABI native PT_LOAD、14 项 Manifest 权限/服务接线、固定正式证书、`563002`、non-debuggable、16 KB 对齐校验全部通过。该本地包用于提交前验证；正式发布必须由 Actions 从修复提交重新构建，不把本地工作树包冒称提交后的 CI 产物。Actions 发布与配套源码归档尚待远端验收。

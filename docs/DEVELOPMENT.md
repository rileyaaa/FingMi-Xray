# FingMi-Xray 开发与维护

本文面向维护当前 `main` 的开发者，说明**工程基线、模块接线、构建依赖、上游同步方式和验证规则**。当前开发、上游同步与后续验收基线统一为 `main`。

长期架构边界见 [PROJECT.md](PROJECT.md)。`v5.6.0-xray.5` 的恢复、native provenance 与 v7 Xray 黄金行为证据见 [RECOVERY.md](RECOVERY.md)。当前 `main` 负责架构与构建验证，v7 黄金参考负责约束 Xray 外部行为；两者不能混为旧 faithful 架构重建。

文档状态：`ORIGINAL_README.md` 是用户明确指定的冻结旧发布说明，只读不改；`AI_COLLABORATION.md` 是当前协作规则的 canonical 文档，用户调整开发限制时应同步维护。当前工程事实、长期架构和历史证据分别继续维护在本文、`PROJECT.md` 与 `RECOVERY.md`。

## 1. 当前工程基线

当前应用源代码跟随 FongMi/TV 当前 HEAD；上游自身的 `app/build.gradle` 版本名仍为 5.6.3：

- 上游目标 commit：`c616c0aa3613e87529791587a9f71b78c278c991`
- 上一固定基线：`4afc4473e22a7ed3d98ee12233e0c2a490061000`（5.6.3）
- 两者是直接父子 commit；新增 runtime 变化集中在 `catvod` 的 redirect-aware proxy selection/authentication。Release / APK 的更高版本号不改变本项目的公开源码上游基线。
- app `versionCode`：`563`
- app `versionName`：`5.6.3`
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

`:app` 直接依赖 `:xray`，`:xray` 再依赖 `:libxray`。这样可以把 Xray 的 Service、配置与网络资源从 FongMi 业务代码中分离。

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

- `app/src/main/java/com/fongmi/android/tv/network/TvNetworkLifecycle.java`
- `app/src/main/java/com/fongmi/android/tv/network/NetworkRecoveryCoordinator.java`

`TvNetworkLifecycle` 由 Leanback `HomeActivity.initView()` 首次安装，随后注册 Application 级 Activity lifecycle 与 SCREEN_ON / SCREEN_OFF receiver 来生成前后台 / screen 网络代际；它不是 Application 冷启动时无条件创建的第二套网络服务。`NetworkRecoveryCoordinator` 仍由 Home 持有，并只在 Home 的 `onResume()` / 窗口重新获得焦点时检查并执行每个待恢复 generation 的普通网络重建。

发布版 generation **只**由真实后台 / SCREEN_OFF 后重新进入前台 / SCREEN_ON 推进；前台 Wi-Fi、VPN 或默认网络切换本身不额外创建 generation。Home 也只在自身 `onResume()` / 重新获得窗口焦点时检查是否需要恢复，隐藏在其他播放页面后的 Home 不主动执行恢复。`recoveredGeneration` 只用于防止 Home 重建时漏掉尚未完成的 generation，不增加新的触发来源。

恢复过程按 generation **串行**：如果当前 Spider clear / 网络稳定轮询尚未结束，新 generation 先等待；旧流程发现 generation 已变化后才结束本轮并启动下一轮，禁止两个 Jar / JS / Python loader clear 并发。

每一轮顺序：

1. 取消旧业务请求；
2. 重建普通 API / DNS / DoH transport，但不销毁播放器专用 client；
3. 串行清理 Spider；
4. 以约 500 ms 周期等待网络稳定，连续两次具备 Internet capability 后继续，最多约 12 次检查；
5. 刷新 Home。

DLNA 生命周期使用 flavor-specific `TvDlnaLifecycle`：

- Leanback 实际启停 DLNA renderer；
- Mobile 为 no-op。

因此 Mobile 不需要依赖 Leanback-only 的 DLNA Service。

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

player candidate 每次从固定公开源码现场重建 17 个 AAR，并由 `player_candidate.py` 校验文件集合、manifest digest 与关键 class；其中包含公开源码本来就有的 `lib-decoder-mpegh`。最终 Leanback APK继续校验 `MpeghAudioRenderer` 与对应 ABI 的 `libmpeghJNI.so`。

### app adapter

app 中只保留当前公开播放器 API 与本 fork 接线所需的小型 adapter，例如 `LibassFontFile`、`DanmakuPlayerViewController`，以及 Xray 播放网络注入所需的 PlayerManager / Exo / MPV hook。不能因为 adapter 存在，就继续维护一套偏离上游的播放器功能。

### MPV 与 Release-only 证据边界

current player candidate 使用固定公开 FongMi/media 的 MPV 源码。current `MpvPlayerEngine` / `MpvUtil` 只保留当前 app 调用面所需的 secondary subtitle、font 与 config option 兼容映射。

历史上曾对高于公开源码的 Release-only Dolby、MPV stream、remote ISO、`libisoJNI.so` 和 disc-navigation 做过取证；这些材料只属于历史研究证据，**不属于 `main` 的实现目标**。current build 不得恢复这些 Release-only 功能，也不得把对应播放器行为带回公开上游代码。发现这类差异时，默认恢复公开上游实现，除非它是 Xray、TV 网络恢复或当前构建不可避免的最小兼容条件。

## 6. 二进制依赖

大型 AAR / APK / SO 不作为普通源码直接提交。`main` 的二进制处理只服务于可重复构建和 Xray provenance，不用于追平 FongMi Release-only 播放器功能。

当前可重复构建依赖：

- 从固定公开 `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d` 现场重建的 17-AAR player candidate；
- 历史 `v5.6.0-xray.5` 黄金 APK：只为 Xray API v2 Java bindings / Go JNI 提供成套 provenance，并作为 Xray 外部行为与 native parity 的黄金参考；current player / FFmpeg 不从该 APK 回灌；
- 官方 libXray v26.7.28 AAR 外层容器；
- 按固定公开 Media3 输入重建的 Libass compatibility AAR；
**当前构建债（不是上游基线）**：公开 `FongMi/TV@c616c0aa...` 明确是 5.6.3，且本项目唯一上游仍是这条公开源码线。公开 `FongMi/media@3c2c...` 不包含 `libraries/exoplayer_libass/`，而仓库当前的 Libass compatibility 构建仍从 FongMi Release 5.6.8 Leanback APK 提取 `libmedia3ass.so` 作为 native 容器。这一输入只是此前为了补齐公开源码缺失 player AAR 所留下的**待移除构建技术债**，不能称为上游、不能用于引入任何 5.6.8 App/播放器行为，也意味着当前仓库尚不能按“二进制输入也严格只有公开 5.6.3 + Xray + TV recovery”来描述。

公开历史 `FongMi/media@9dae39e9689ee305c83f94bd11cf3bcecb9d6171` 曾包含一版 `libraries/exoplayer_libass/` 与 native 构建源码，但它与固定 `3c2c...` 是分叉历史，当前不能在没有 ABI 验证的情况下直接冒充 5.6.3 的可替代输入。后续清理这项构建债时，优先寻找与 5.6.3 公开源码/公开 media 可验证对应的来源；不得因为现有脚本“能构建”就继续把更高版本 Release 当长期依赖。

`libXray/**` generated bindings 与 `libgojni.so` 必须作为同一 JNI ABI 单元恢复；不能把官方旧 bindings 与黄金 API v2 JNI 单独拼接。当前 `scripts/build/build-published-libxray-aar.py` 从固定黄金 APK恢复匹配的 `libXray/**` bindings 与双 ABI JNI，同时保留官方 v26.7.28 AAR 中未经过 App R8 混淆的通用 `go/**` runtime。

最终 APK native 验证使用 ELF `PT_LOAD` runtime image，而不是 whole-file SHA：Android Gradle strip 可以改变 section metadata，但不能改变运行时 load segments。当前最终门槛核对 Xray、公开 FongMi/media 重建得到的 FFmpeg、MPEG-H 与 Libass 四类 native，并单独检查 merged Manifest：XrayService 必须 `exported=false` / `process=:xray`，同时拒绝 BootReceiver、`RECEIVE_BOOT_COMPLETED`、`REQUEST_INSTALL_PACKAGES` 与 VPN service permission 回流。普通 FongMi 权限不因为本 fork 的一般性安全偏好而额外改写；只有 Xray、TV 网络恢复或防止上游 APK 自更新覆盖 fork 所必需的 Manifest 差异可以长期保留。

current / publish workflow 会在主 Gradle compile / assemble 前清理已消费的 APK、JADX、native harness、Libass extractor 与 reconstruction workdir。修改 compatibility 输入或 hash 时必须同步修改对应 verifier；不得重新加入任何高于公开源码的 Dolby/MPV/ISO Release-only restorer。

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

1. 准备 JDK / Android SDK；
2. 从固定公开 FongMi/media commit 重建 17-AAR player candidate，并下载 / 校验当前 compatibility 与黄金 Xray 输入；
3. 直接导入固定公开 FongMi/media 重建出的 player candidate；黄金旧 APK只用于重建与 Go JNI 配套的 libXray Java bindings 与 Xray 动态 parity；
4. 重建并导入最小 Libass compatibility AAR；
5. 执行 current Java → 黄金 v7 / arm64 native 动态 Xray chain parity（统一以 v7 发布行为为黄金 oracle，包含 KCP golden cases 与发布版 `testXray` runtime validation）；
6. 只编译 Android TV / Leanback Java；
7. 只 assemble Android TV / Leanback 两个 ABI 的 Debug APK；
8. 对最终 APK执行 MPEG-H class/native、Xray/FFmpeg/MPEG-H/Libass runtime PT_LOAD provenance 与 merged Manifest security contract；
9. 上传短期 TV debug artifact（保留 2 天）供临时验证；上传成功后自动删除同名旧 debug，只保留最新一份。失败报告只保留 1 天。历史 recovery workflow 的 JADX/DEX、faithful APK、native dependency、player AAR 和 upstream snapshot artifacts 也只作临时复核，统一最多保留 3 天；长期可重建输入只保留源码 commit、脚本、fixture 与 hash，不再占用 Release。Gradle 命令继续使用 `--warning-mode all`；当前剩余会在 Gradle 10 失败的 deprecation 已确认全部来自固定上游同样使用的 Chaquopy Gradle plugin 17.0.0（multi-string dependency notation 与 execution-time `Task.project`），不是本仓库 Gradle 脚本。当前保持 FongMi/TV 5.6.3 的 17.0.0 pin，并让 `com.fongmi.chaquo.Platform` 继续跟随固定上游实现，不在本 fork 中为一般兼容或 warning 主动改写 Python ABI 选择逻辑。

测试发布器：

`.github/workflows/publish-current-main-test-release.yml`

Release 的 APK 发布集合长期保留 `v5.6.0-xray.5` 黄金参考和一个当前可上真机测试的 pre-release。构建输入、恢复材料、临时归档和旧测试版不得长期堆在 APK 发布集合中；用户明确要求的完整源码备份可使用 `source-backup-*` 独立 Release，APK 发布器在校验“黄金版 + 当前测试版”时忽略这类源码备份，不会自动删除它们。

GitHub Releases 当前只有 `v5.6.0-xray.5` 黄金参考与用户要求保留的 `source-backup-2026-10-02-main-6a4117c8` 源码备份，**没有当前可上真机测试的 pre-release**。过去成功的主构建、native parity、Leanback assemble 与 Manifest gate 只证明当时对应源码；2026-10-03 从 source-backup 重放确认修复后的当前 HEAD 尚未重新完成 Gradle compile / assemble 或 Android TV 真机回归。后续若发布测试包，应以当前 HEAD 为唯一 BUILD_SOURCE_SHA 重新验证。

发布 workflow 以 `BUILD_SOURCE_SHA` 作为唯一构建与发布源码，重新准备固定依赖、执行源码 guard、执行当前 Java → 发布版 native 动态 Xray chain parity、只编译/assemble Android TV / Leanback 两个 ABI，并在发布前重复执行最终 APK MPEG-H、四类 native runtime provenance 与 merged Manifest security contract。**当前 YAML 仍显式配置 `RELEASE_TAG=v5.6.3-xray.test.6`、`PREVIOUS_RELEASE_TAG=v5.6.3-xray.test.5`；它不会自动递增版本号。** 因此按现状手动触发会创建/替换 `test.6`（当前该 Release 不存在），若要发布 `test.7` 或其它 tag，必须同时更新 workflow 与 `tests/test-build-hygiene.py` 中对应的 release-set guard。正常手动触发时 `BUILD_SOURCE_SHA = github.sha`；发布 job 保持最小权限 `contents: write + actions: read`。临时触发、轮询与清理规则只以 [AI_COLLABORATION.md](AI_COLLABORATION.md) 为准，本文不重复保存一次性操作历史。

当前 build 与 publish workflow 都必须先执行：

- `tests/test-xray-android-runtime-compat.py`：防止 Java 21 可编译、但旧 Android ART 运行时不存在的 API 再进入 `:xray`，并防止 `main` 构建重新退回“官方旧 Java bindings + 单独替换发布版 Go JNI”的不匹配组合；
- `tests/test-xray-core-parity.py`：守住配置生成、存储 / TOFU、Service 重试清理、Settings 核心语义、手机导入的 EventBus / operation 中断边界与发布版错误去敏链，并要求 current public destination guard 与发布 `qz3` readable mirror 保持逐行为等价；
- `tests/test-xray-playback-parity.py`：守住 VOD / Live、播放器代理切换、媒体旁路、本地 scheme、artwork/logo 与资源释放语义；
- `tests/test-xray-playback-address-parity.py`：把 public HTTP(S)/RTSP/RTSPT、私网/保留目标、Unicode whitespace，以及 Live pending `.strm` / YouTube indirection 边界与冻结发布证据做 differential parity；
- `tests/test-xray-session-races.py`：锁住发布版 STOP / timeout / callback 的竞态顺序；
- `tests/test-xray-service-client-lifecycle.py`：直接编译真实 Service client，锁住 bind timeout、cancel/unbind、Binder death 与 stale callback / connection generation；
- `tests/test-xray-normalizer-parity.py`：把当前 share-link normalizer 与 display helper 对发布版 readable reference 做纯 JVM differential parity；
- `tests/test-xray-transport-security-parity.py`：把 TLS / HY2 TOFU identity、首次信任、证书变化拒绝、已有 pin 与大小写/migration 边界对发布 reference 做 differential parity；
- `tests/test-upstream-update-disabled.py`：防止 FongMi 上游自更新入口、直接 release endpoint 调用或 APK 安装权限重新进入当前 fork；
- `scripts/build/check-elf-runtime.py --self-test`、`check-final-apk-native.py --self-test`、`check-final-apk-manifest.py --self-test`：先验证最终 ELF/Manifest gate 自身的判定逻辑；
- `tests/test-build-hygiene.py`：防止错误 XLIFF namespace、非 positional 多参数 string、FongMi/Chaquopy 上游边界再次被 fork-only 改写、Release-only media restore 回流，以及仍基于 Node 20 的旧 Actions major 再进入构建；
- `tests/test-tv-network-recovery.py`：锁住正式 `gn3` 的前后台 / SCREEN generation 来源，并用纯 JVM harness 验证 recovery 顺序、连续稳定检查、DoH resolver snapshot 与跨 generation 串行清理。

`tests/` 是 `main` 的统一回归入口，不再另维护目录 README。除上述 workflow guard 外：

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

直接运行 Gradle 前，需要先准备 `app/libs` 与 `libxray/libs/libXray.aar` 所需的固定依赖。最完整的依赖准备顺序以 `current-main-build.yml` 为准。

完成依赖准备后，主要验证命令为：

```bash
./gradlew --no-daemon :app:compileLeanbackDebugJavaWithJavac
./gradlew --no-daemon :app:assembleLeanbackDebug
```

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

发布成功后已先恢复 publish workflow 为 `workflow_dispatch` only，再删除临时 marker，避免清理提交再次触发 Actions。随后只同步 README/DEVELOPMENT 文档，没有修改运行代码。当前 Release 集合只保留黄金 `v5.6.0-xray.5`、当前测试 `v5.6.3-xray.test.6` 与用户明确要求的 `source-backup-2026-10-02-main-6a4117c8` 源码备份；旧测试/临时发布已不在集合中。自动构建已验证，但 Android TV 真机 Xray 与待机/长后台恢复仍需实际设备验收。

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

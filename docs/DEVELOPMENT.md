# FingMi-Xray 开发与维护

本文面向继续维护当前 `main` 的开发者，说明**当前工程基线、模块接线、构建依赖、上游同步方式和验证规则**。

长期架构边界见 [PROJECT.md](PROJECT.md)。`v5.6.0-xray.5` 的恢复、native provenance 与 v7 Xray 黄金行为证据见 [RECOVERY.md](RECOVERY.md)。当前 `main` 负责架构与构建，v7 黄金参考负责约束 Xray 外部行为；两者不能混为旧 faithful 架构重建。

## 1. 当前工程基线

当前应用源代码跟随 FongMi/TV 当前 HEAD；上游自身的 `app/build.gradle` 版本名仍为 5.6.3：

- 上游目标 commit：`c616c0aa3613e87529791587a9f71b78c278c991`
- 上一固定基线：`4afc4473e22a7ed3d98ee12233e0c2a490061000`（5.6.3）
- 两者是直接父子 commit；新增 runtime 变化集中在 `catvod` 的 redirect-aware proxy selection/authentication，不代表从 5.6.3 到 Release 5.6.8 之间存在五轮 App 架构重写。
- app `versionCode`：`563`
- app `versionName`：`5.6.3`
- Java：21
- Gradle wrapper：9.7.1
- Android Gradle Plugin：9.3.1
- `compileSdk` / `targetSdk`：37
- `minSdk`：24

当前 `main` 是现行源码、架构、上游同步和发布构建基线。Xray 外部行为则以用户长期验证稳定的 `v5.6.0-xray.5` armeabi-v7a 正式 APK 为黄金参考，并由 readable reference、source guard、JVM lifecycle test 与真实发布 native 动态 parity 映射到当前模块。正常发布不要求重新构建旧 faithful APK。

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
- `tests/test-xray-android-runtime-compat.py` 在 current-main 构建前扫描这些风险，并同时检查 libXray / gomobile 的 release keep rule。

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

设置页的 VALIDATE / TEST / RESET_SECURITY 由 `XraySettingsController` 串行拥有单一 operation generation，45 秒 timeout、abandon、client replacement 与 stale callback 丢弃都在 controller/client 边界收口。

RESET_SECURITY 保持发布版顺序：先占有 reset generation 并替换 Binder client，再清本地安全配置；本地清理成功后才清 UI，最后派发远端 security reset。同步失败时会清 active generation 并再次替换 client，避免旧 Binder 状态继续持有操作。

`XrayServiceClient` 保留约 5 秒 bind timeout、remote cancel 后 unbind、Binder death / binding died / null binding / disconnect 收口，以及 ServiceConnection / callback generation 过滤。

### 播放器

`PlayerManager` 通过 `setPlaybackProxy(...)` 切换当前播放网络资源。

启用 Xray 后：

- 预加载不会复用普通直连身份；
- Exo engine 按当前 proxy 边界重建；
- `ExoMediaSourceFactory` 的 HTTP / HTTPS 使用 Xray client；
- DRM license 跟随相同 DataSource；
- RTSP / RTSPT 使用 Xray SocketFactory；
- Xray 播放 DataSource 不允许用本地 / 非 HTTP(S) scheme 静默绕过当前会话。

关闭或切换身份后，播放器重新回到普通 FongMi 网络资源。

## 4. TV 网络恢复

TV 网络恢复没有放进 `:xray`。

主要入口：

- `app/src/main/java/com/fongmi/android/tv/network/TvNetworkLifecycle.java`
- `app/src/main/java/com/fongmi/android/tv/network/NetworkRecoveryCoordinator.java`

`TvNetworkLifecycle` 负责生成前后台 / screen 网络代际；`NetworkRecoveryCoordinator` 每个需要恢复的 generation 执行一次普通网络重建。

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

## 5. 当前媒体兼容层

FongMi/TV 5.6.3 对 Media3 / MPV 的调用面与当前固定的部分播放器二进制存在差异。仓库没有用 compile-only 空壳掩盖差异，而是保留明确的 compatibility layer。

### Media3 / Libass

当前构建流程固定一组 FongMi/media AAR 输入，再通过仓库中的源码和补丁重建 5.6.3 所需的 Libass compatibility AAR。

主要材料：

- `compat/media3-libass/`
- `compat/media3-libass/tests/`
- `compat/media3-libass/media-tests/`
- `scripts/build/build-libass-extractor.py`
- `scripts/build/build-libass-candidate.py`
- `scripts/build/check-libass-contract.py`
- `scripts/build/import-libass-candidate.py`

恢复 / 适配范围包括：

- native loader；
- Matroska / ASS extractor hook；
- primary / secondary subtitle 状态；
- parser 与 playback session；
- clock / renderer；
- EGL / GLES frame 生命周期；
- PlayerView controller；
- subtitle sample timestamp。

player candidate 的信任根是固定 `FongMi/media` commit；每次构建都会生成包含 17 个 AAR SHA-256 的 manifest，并由 `player_candidate.py` 验证文件集合、manifest 与关键 class。17 个模块包含 `lib-decoder-mpegh`，并要求最终 Leanback APK 同时包含 `androidx.media3.decoder.mpegh.MpeghAudioRenderer` 与对应 ABI 的 `libmpeghJNI.so`。Media3 container、Libass output、发布 APK / native 等其余不可重建输入继续按 workflow / fixture 中的固定 hash 校验。

### app adapter

当前 app 还包含 FongMi 5.6.3 调用面需要的少量 adapter，例如：

- `LibassFontFile`
- `DanmakuPlayerViewController`

这些是当前 app 与固定媒体依赖之间的兼容边界。

### MPV

固定 player candidate 仍以 `FongMi/media@3c2cbe8...` 的公开 MPV 源码为基础；current app 的 `MpvPlayerEngine` / `MpvUtil` 只做现有 secondary subtitle、font 与 config option 的兼容映射。这层 adapter 不能冒充 5.6.7 / 5.6.8 Release 的新版 MPV bridge。

后续对 5.6.8 full-JADX、5.6.7 / 5.6.8 Release notes 与双 ABI native 做定向复核后，已经确认 Release MPV bridge 与固定 public source 存在真实 ABI/行为差异。第一阶段已经进入 current source/build chain：

- `apply-media3-mpv568-overlay.py` 在固定 public MPV 源码上恢复 `MPVLib.enqueueCommandLongResult(...)`、三参数 command reply、`MPVLib.Stream` / stream registry、`MpvClient` long-result callback 与 `MpvCommandDispatcher` script load/unload；
- Release `libplayer.so` 的 JNI 字符串已经独立证明它要求 `MPVLib$Stream`、`openStream`、`read/seek/size/cancel/close` 和 `eventCommandReply(long,int,long)`，因此这些不是仅凭 JADX 猜出的接口；
- 双 ABI `libplayer.so` 与 `libmpv.so` 已由 `published_568_mpv_contract.py` 固定 SHA，并由独立 restorer/checker 作为一个 bridge native 单元恢复；current/publish 与 final APK provenance gate 已接入，并已在最新 full current-main TV build 中通过；
- 5.6.8 subtitle 路径的 `secondary-sub-scale` 已补入 Media3 subtitle defaults 和 app `MpvUtil` ownership，并由 overlay unit test / source guard 约束；
- 5.6.7 Release 明确包含“播放腳本”“ISO 原盤起播、光碟選單”，5.6.8 又继续声明“改善 mpv 字幕及原生播放元件”，因此这些属于发布行为，不是未暴露的内部实验接口。

**第二阶段仍未完成：** `MpvMediaLoader` 尚未接入 Release 的 HTTP(S) ISO → `media3iso://.../disc.iso` stream provider/random-access reader；固定 public source虽有 Java ISO extractor / `IsoDataReader`，但没有 5.6.8 APK 中的 `libisoJNI.so` 及对应 `IsoNavigationSession` / native UDF bridge，光碟菜单/native ISO 路径仍需单独 provenance。`libnodebridge.so` 的 Release-only 更新也尚未迁移。

### 5.6.8 Release-only 媒体同步状态

FongMi/TV 公开 HEAD `c616c0aa...` 与 Release 5.6.8 不是完整一一对应的源码快照。当前必须把“公开源码同步”与“Release-only media provenance”分开判断。

当前 `main` 已完成：

- TV 公开源码的 redirect-aware proxy 修复已合并，并保留 TV network recovery 的独立 API/player client 边界；
- Release-only 音量增强上限已同步到真实 20 dB（`AudioSetting.MAX_BOOST = 2000`）并有 source guard；
- 5.6.8 Libass 双 ABI native 已建立独立 contract，并完成 JNI/render/ownership/Media3/GL 验证；
- 5.6.8 FFmpeg native closure 已由 `published_568_ffmpeg_contract.py` 固定双 ABI provenance，并通过 `restore-published-568-ffmpeg.py` / `check-published-568-ffmpeg.py` 整套恢复，closure 包含 `libavcodec.so`、`libavdevice.so`、`libavfilter.so`、`libavformat.so`、`libavutil.so`、`libffmpegDoviJNI.so`、`libffmpegJNI.so`、`libswresample.so`、`libswscale.so`；
- 5.6.8 Dolby P5/P7 overlay 已真正进入固定 17-AAR player candidate：P5 renderer / VideoSink / native policy、P7 converter lifecycle、`DefaultRenderersFactory`、`DecodeTrackSelector` 与 R8 keep contract 都已接线；
- current / publish workflow 已切到完整 5.6.8 FFmpeg closure，不再走历史“只替换 5.6.0 单个 `libffmpegJNI.so`”路径；
- full current-main TV build 已实际通过：17-AAR rebuild/verifier、5.6.8 FFmpeg restore/check、Xray 双 ABI native parity、Libass rebuild/import、Leanback Java compile、v7/arm64 APK assemble、MPEG-H final packaging、Xray/FFmpeg/MPEG-H/Libass final `PT_LOAD` provenance 和 merged Manifest security contract 全部成功。

**当前边界：** 5.6.8 MPV bridge 第一阶段（long-result/script JNI、Stream ABI、secondary subtitle scale、双 ABI `libplayer.so` / `libmpv.so` provenance）已接入 current source/build chain，并已通过最新 full current-main：17-AAR rebuild、mpvplayer unit tests、Leanback Java compile、双 ABI APK assemble，以及最终 APK 中 `libplayer.so` / `libmpv.so` 的 PT_LOAD provenance。remote ISO stream、disc-menu native path / `libisoJNI.so` 与 `libnodebridge.so` 仍未迁移。因此现在仍不能说“5.6.8 播放器 / media 已完整同步”。Android TV 真机上的 P5/P7、Xray、网络生命周期与 MPV/ISO 行为仍属于最终运行时验收层。

## 6. 二进制依赖

大型 AAR / APK / SO 不作为普通源码直接提交。

当前可重复构建依赖以下几类输入：

- 固定 FongMi/media player candidate 由 `scripts/build/build-player-aar-candidate.sh` 从 `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d` 现场重建；`scripts/build/player_candidate.py` 校验固定 commit、17 个 AAR（包含 `lib-decoder-mpegh`）、manifest digest 与关键播放器 class。candidate 验证完成后立即删除 FongMi/media 临时 checkout、`buildout` 与 staging，只保留重建后的 candidate ZIP，避免前置媒体重建占满 GitHub-hosted runner 磁盘。构建输入不再放进项目 Release；
- 从 SHA 固定的 5.6.8 Leanback 双 ABI APK 恢复的完整 FFmpeg native closure，以及 MPV bridge 的 `libplayer.so` / `libmpv.so`（分别由 decoder / MPV AAR restorer 与 verifier 约束）；
- 官方 libXray v26.7.28 AAR 外层容器，以及从固定历史发布 APK 恢复、彼此匹配的 API v2 gomobile Java bindings 与 v7 / arm64 Go JNI；
- 按固定输入重建的 Libass compatibility AAR。

Libass compatibility AAR 的 Java/compat 源码仍由仓库重建；其中不可由当前固定 FongMi/media commit 直接重建的 `libmedia3ass.so` 从固定官方 APK 提取。原先固定的 FongMi 5.6.6 Release 已被上游删除。后续取证确认 FongMi 5.6.7 与 5.6.8 的双 ABI `libmedia3ass.so` 完全同字节，但它们已经不是历史 5.6.5/5.6.6 native：v7 为 `58bc83730285c9a4ba40bf71d4deeea8be7e69dfb7d1a053f6a77aea006ad6ee`，arm64 为 `7e160faba4f64abb7551b48d07ae886af73464d3079978dcd55352e7b22bd6b3`。current `main` 已新增 `published-568-native-contract.json`，固定 5.6.8 immutable APK whole-file SHA、双 ABI SO SHA、ELF machine、17 个 JNI RegisterNatives descriptor 与 `LibassFrame` / `LibassImage` constructor ABI；旧 5.6.5 fixture 继续只作为已恢复 Java/render 行为参考。5.6.8 Libass candidate 已通过双 ABI JNI lifecycle、synthetic ASS render parity、ownership、Media3 72-test suite 与 GL contract；重建 candidate SHA 仍固定为 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861`。任何后续 native 迁移仍必须同时通过这些 contract 与最终 APK PT_LOAD gate，不能只改 hash 放行。

两条 current workflow 在 player / libXray / 双 ABI native parity / Libass 输入全部验证并导入 `app/libs`、`libxray/libs` 后，会在主 Gradle compile / assemble 前删除已消费的 APK、JADX、QEMU/native harness、Libass extractor 与 reconstruction workdir，只保留实际构建依赖和最终输出路径，避免 GitHub-hosted runner 因验证工作区与 Gradle 中间产物叠加而耗尽磁盘。

FFmpeg 与 libXray 现在使用不同的发布 provenance，不能再合并描述成同一个旧 APK 来源。FFmpeg closure 取自 SHA 固定的 FongMi 5.6.8 Leanback v7 / arm64 APK，并整套恢复进 `lib-decoder-ffmpeg-release.aar`；libXray API v2 的 Java/native 绑定仍来自历史 `v5.6.0-xray.5` 黄金发布 APK。current-main 仍会下载该历史 Xray Release 并按固定 SHA 作为 provenance / reproducibility 输入。libXray 的 gomobile Java bindings 与 `libgojni.so` 必须视为同一个 JNI ABI 单元：不能把官方 v26.7.28 的 `classes.jar` 与历史发布版 API v2 `libgojni.so` 单独拼接，否则 native 初始化可能查找官方旧 bindings 不包含的模型类（例如 `libXray.AgeDecryptConfig`）并导致进程崩溃。当前构建由 `scripts/build/build-published-libxray-aar.py` 从经过 SHA 校验的黄金 APK 恢复发布版 `libXray/**` Java bindings，保留官方 v26.7.28 AAR 中干净、未经过 App R8 混淆的通用 `go/**` gomobile runtime classes，再与同一黄金发布版的 v7 / arm64 Go JNI 配套放回官方 AAR 外层容器。**在这一构建链中，5.6.8 APK 负责当前 FFmpeg/Libass 等 media provenance；5.6.0-xray.5 APK 负责 Xray native/bindings provenance 与 Xray 外部行为黄金参考。** current-main 不要求恢复旧 faithful 架构或完整 APK。

最终 APK 的 native provenance 不再用 whole-file SHA 直接比较。Android Gradle packaging 会对 native strip，整文件 digest 可以变化而运行时负载段保持相同；`scripts/build/check-elf-runtime.py` 因此比较 ELF `PT_LOAD` runtime image，并只归一化 strip 会改写的 section-table metadata。`scripts/build/check-final-apk-native.py` 会递归发现两个 Leanback ABI 的最终 APK，并分别核对 Xray `libgojni.so`、完整 5.6.8 FFmpeg closure、MPEG-H 与 Libass native 都仍与已验证 AAR 的 runtime image 一致。最终 Manifest 另由 `scripts/build/check-final-apk-manifest.py` 从 APK 直接解析，锁住 XrayService `exported=false` / `process=:xray`，并拒绝 BootReceiver、`RECEIVE_BOOT_COMPLETED`、`READ_PHONE_STATE`、`REQUEST_INSTALL_PACKAGES` 与 VPN service permission 回流；app Manifest 还显式用 `tools:node="remove"` 阻断依赖合并进来的 `READ_PHONE_STATE`。

`current-main-build.yml` 会下载、校验并准备这些固定依赖，再进行 Java 编译和 APK assemble。

当前 compatibility 构建脚本集中在 `scripts/build/`，历史来源提取工具集中在 `scripts/recovery/`，当前源码回归入口位于 `tests/`。修改任何二进制来源或 hash 时，必须同步修改对应验证脚本 / workflow，不能只把一个新 AAR 丢进 `app/libs`。

`compat/` 是 current-main 的构建输入，不是历史 recovery：`compat/media3-libass/src/` 保存实现，`patches/` 保存固定 Media3 extractor / subtitle 所需补丁，`tests/` 与 `media-tests/` 保存 compatibility 契约、JNI 和 SecondaryText 等媒体 fixture。其行为由 current-main 测试约束，不要求逐字复刻 v5.6.0 的媒体实现。

## 7. 构建

### GitHub Actions

仓库所有可执行 workflow 都必须保持**纯手动**。GitHub 官方 helper action 同时保持 Node 24 兼容 major（当前为 checkout v7、setup-java v6、setup-python v7、upload-artifact v7），避免 runner 强制兼容旧 Node 20 action 所产生的弃用告警：

```yaml
on:
  workflow_dispatch:
```

不保留 `push`、`pull_request`、`schedule`、`workflow_call` 等自动触发。

#### AI 协作执行准则

AI 与用户共同开发时的固定操作限制独立维护在 [AI_COLLABORATION.md](AI_COLLABORATION.md)。其中包括 CI 禁止原地轮询、Actions 状态必须从最新 runs 列表重新确认、会话接近平台时限时立即交接返回，以及及时维护文档但禁止流水账式更新。


当前工程主构建：

`.github/workflows/current-main-build.yml`

它负责：

1. 准备 JDK / Android SDK；
2. 从固定 FongMi/media commit 重建 player AAR candidate，并下载 / 校验其余固定媒体与黄金发布输入；
3. 从固定 5.6.8 双 ABI APK 恢复并校验完整 FFmpeg native closure与 MPV `libplayer.so` / `libmpv.so` bridge，同时重建 Java bindings 与 Go JNI 配套的 libXray compatibility AAR；
4. 重建并导入 Libass compatibility AAR；
5. 执行 current Java → 发布版 v7 / arm64 native 动态 Xray chain parity（统一以 v7 发布行为为黄金 oracle，包含 KCP golden cases 与发布版 `testXray` runtime validation）；
6. 只编译 Android TV / Leanback Java；
7. 只 assemble Android TV / Leanback 两个 ABI 的 Debug APK；
8. 对最终 APK 执行 MPEG-H class/native、Xray/FFmpeg/MPV/MPEG-H/Libass runtime PT_LOAD provenance 与 merged Manifest security contract；
9. 上传短期 TV debug artifact（保留 2 天）供临时验证；上传成功后自动删除同名旧 debug，只保留最新一份。失败报告只保留 1 天。历史 recovery workflow 的 JADX/DEX、faithful APK、native dependency、player AAR 和 upstream snapshot artifacts 也只作临时复核，统一最多保留 3 天；长期可重建输入只保留源码 commit、脚本、fixture 与 hash，不再占用 Release。Gradle 命令继续使用 `--warning-mode all`；当前剩余会在 Gradle 10 失败的 deprecation 已确认全部来自固定上游同样使用的 Chaquopy Gradle plugin 17.0.0（multi-string dependency notation 与 execution-time `Task.project`），不是本仓库 Gradle 脚本。当前保持 FongMi/TV 5.6.3 的 17.0.0 pin，待上游或 Chaquopy 升级时再单独验证 Python runtime 与双 ABI assets，不在本 fork 中为消 warning 私自升级。自定义 `com.fongmi.chaquo.Platform` 在 FongMi/TV 5.6.3 基础上补了 process-bitness 修复：先用 `Process.is64Bit()` 选择 `SUPPORTED_64_BIT_ABIS` 或 `SUPPORTED_32_BIT_ABIS`，再在同位数列表中挑选 Python ABI；选中的 ABI 仍必须同步到 Chaquopy 17 的 `AndroidPlatform.ABI`，因为其 `java.android.importer` 会读取这个内部字段来装载 ABI-specific requirements ZIP。

测试发布器：

`.github/workflows/publish-current-main-test-release.yml`

Release 只承载发布版本：长期保留 `v5.6.0-xray.5` 黄金参考和一个当前可上真机测试的 pre-release。构建输入、恢复材料、临时归档和旧测试版不得长期堆在 Releases；新测试版验证成功后发布器会清理上一测试版和历史 `build-inputs-5.6.3`，并校验 Release 集合只剩黄金版 + 当前测试版。

它以 `BUILD_SOURCE_SHA` 作为唯一构建与发布源码，重新准备固定依赖、执行源码 guard、执行 current Java → 发布版 native 动态 Xray chain parity、只编译/assemble Android TV / Leanback 两个 ABI，并在发布前重复执行最终 APK MPEG-H、四类 native runtime provenance 与 merged Manifest security contract，然后才发布新的测试 Pre-release；成功包不再额外复制一份到 Actions artifact。正常手动触发时 `BUILD_SOURCE_SHA = github.sha`。

如果因为当前 GitHub connector 缺少 workflow dispatch 能力而临时触发 publish，必须采用**两阶段 marker 触发**：先用只修改 workflow 的 arm commit 增加临时 `push`，并用 `paths` 把它限制为 `.github/.trigger-publish-current-main-test`；因此 arm commit 自身不应触发完整 run。随后用第二个只修改该 marker 的 commit 真正触发完整 run；workflow 会验证 trigger commit 的唯一变更就是 marker，并以该 commit 自身作为 checkout / build / Release target。完整 run 执行期间必须保持 publish workflow 的临时 `push` 不变，并禁止再向 `main` 提交其他内容；只有 Release 创建、tag / digest 验证和上一版测试 Release 替换全部成功后，才恢复为纯 `workflow_dispatch` 并删除 marker。若 arm commit 因 trigger 配置错误而产生 run，source guard 必须在进入 SDK、native parity 或 Gradle 构建前拒绝它。历史 `test.4` 的发布记录仍说明：Release 完成前不能提前撤回临时 trigger，否则 default branch 与显式 Release target 的 workflow 树可能产生差异并触发 GitHub Release API 权限失败。

这个约束来自已复核的发布记录：成功的 `test.4` 显式 Release target 自身只修改 marker；两次失败的 `test.5` 显式 target 自身都直接修改 workflow YAML，并在 `gh release create` 得到 `HTTP 403: Resource not accessible by integration`；同日 `build-inputs-5.6.3` 未显式指定 SHA target 时又能由同类 `contents: write` Actions token 正常创建。因此临时启用 `push` 的 workflow 修改 commit 不得直接作为显式 Release target。发布 job 保持最小权限 `contents: write + actions: read`。新测试 Release、tag 指向的 `BUILD_SOURCE_SHA` 与两个 Leanback APK digest 全部验证成功后，workflow 才删除 YAML 中指定的上一版测试 Release / tag。其他历史 Release 不在这条替换链中，也不参与当前版本的最终验收。

两个 current-main workflow 都必须先执行：

- `tests/test-xray-android-runtime-compat.py`：防止 Java 21 可编译、但旧 Android ART 运行时不存在的 API 再进入 `:xray`，并防止 current-main 构建重新退回“官方旧 Java bindings + 单独替换发布版 Go JNI”的不匹配组合；
- `tests/test-xray-core-parity.py`：守住配置生成、存储 / TOFU、Service 重试清理、Settings 核心语义、手机导入的 EventBus / operation 中断边界与发布版错误去敏链，并要求 current public destination guard 与发布 `qz3` readable mirror 保持逐行为等价；
- `tests/test-xray-playback-parity.py`：守住 VOD / Live、播放器代理切换、媒体旁路和资源释放语义；
- `tests/test-xray-session-races.py`：锁住发布版 STOP / timeout / callback 的竞态顺序；
- `tests/test-xray-service-client-lifecycle.py`：直接编译真实 Service client，锁住 bind timeout、cancel/unbind、Binder death 与 stale callback / connection generation；
- `tests/test-xray-normalizer-parity.py`：把 current share-link normalizer 与 display helper 对发布版 readable reference 做纯 JVM differential parity；
- `tests/test-upstream-update-disabled.py`：防止 FongMi 上游自更新入口、直接 release endpoint 调用或 APK 安装权限重新进入当前 fork；
- `tests/test-build-hygiene.py`：防止错误 XLIFF namespace、非 positional 多参数 string、Chaquopy ABI handoff 丢失、Release-backed build input 回流，以及仍基于 Node 20 的旧 Actions major 再进入构建。
- `tests/test-tv-network-recovery.py`：锁住正式 `gn3` 的前后台 / SCREEN generation 来源，并用纯 JVM harness 验证 recovery 顺序、连续稳定检查和跨 generation 串行清理。

`tests/` 是 current-main 的统一回归入口，不再另维护目录 README。除上述 workflow guard 外：

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

`recovery-*` workflow 只保留给历史取证、来源重建或必要的二进制复核；它们不是 current-main 的发布前置条件。历史恢复说明见 [RECOVERY.md](RECOVERY.md)。

### 本地

直接运行 Gradle 前，需要先准备 `app/libs` 与 `libxray/libs/libXray.aar` 所需的固定依赖。最完整的依赖准备顺序以 `current-main-build.yml` 为准。

完成依赖准备后，主要验证命令为：

```bash
./gradlew --no-daemon :app:compileLeanbackDebugJavaWithJavac
./gradlew --no-daemon :app:assembleLeanbackDebug
```

## 8. 跟随 FongMi/TV 上游

升级上游时只以当前 `main` 和目标 FongMi/TV 上游为架构开发输入，不从历史 recovery faithful tree 继续开发；但 `:xray` 的外部行为仍必须保持与 `v5.6.0-xray.5` v7 黄金参考一致。

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

本节允许按日期、版本或里程碑持续维护，但只记录**会长期影响后续开发判断**的故障结论、迁移决策和验证基线；单次失败尝试、临时 trigger、普通 commit / run 流水不在这里展开。

### 2026-09-27 — libXray Java/native ABI 必须成套恢复

`v5.6.3-xray.test.3` 暴露出官方 v26.7.28 Java bindings 与历史 API v2 `libgojni.so` 混搭会在 JNI 初始化阶段查找缺失模型类并杀死 `:xray` 进程。current-main 因此固定使用 `scripts/build/build-published-libxray-aar.py`：从固定发布 APK 恢复匹配的 `libXray/**` API v2 bindings 与 v7 / arm64 JNI，同时保留官方 AAR 中未经过 App R8 混淆的通用 `go/**` runtime。后续升级 libXray 必须整套替换 Java bindings + JNI，不能只换其中一侧。

### 2026-09-28 — Xray 行为黄金参考与 TV-only 验收确定

后续 Xray 维护采用“**current 模块化架构 + v5.6.0-xray.5 v7 外部行为黄金参考**”。项目只维护 Android TV / Leanback，输出 armeabi-v7a 与 arm64-v8a；Mobile 不再是本 fork 的 Xray 构建目标。已恢复并自动锁定 session STOP/timeout/callback、Settings RESET_SECURITY、Binder client generation、播放代理/旁路/资源释放、normalizer/display 等发布语义。

### 2026-09-28 — 双 ABI current-chain 动态 parity 建立

current Java 的 normalize → transport security → runtime config 链会分别交给固定 SHA 的 v7 / arm64 发布 `libgojni.so`，并以 v7 冻结 oracle 比对 conversion 与 runtime `testXray`。固定链覆盖 26 组分享链接，其中 6 组为 KCP golden cases。该验证证明的是 Java/native 组合在这些冻结输入上的动态等价；它不替代 Android TV 真机上的 ART、Binder、播放器和真实网络生命周期回归。

### 2026-09-28 — 文档体系收敛

长期项目文档收敛为 README、PROJECT、DEVELOPMENT、AI_COLLABORATION、RECOVERY 和冻结 ORIGINAL_README 六份。tests / compat 的维护说明归入本文，recovery / apk-reference 的说明归入 RECOVERY；目录内不再重复维护 README。开发记录允许保留精选的日期/版本里程碑，但不把 Git / Actions 过程复制成流水账。

### 2026-09-29 — full-JADX 重新定义了 Xray 审计证据边界

此前长期保存在 Git 中的 `docs/apk-reference/shared/sources/` 是筛选后的 readable evidence，不是完整 APK 源码宇宙；因此不能再用 selected JADX 宣布“源代码级 100% 还原”。重新对黄金 APK 做 full JADX 后，发现多组名称本身不含 Xray 的混淆类会经旧 `PlayerManager` 间接取得 Xray-aware playback client / proxy 状态，字幕、弹幕、PlayerView 重建和 preload 等路径必须按最终调用关系反查，而不能只搜索 Xray 文件名。

这轮反查确认 current 已承接字幕、弹幕、DRM、RTSP、preload、VOD artwork 与 MediaSession artwork 的发布语义，同时找到一个真实外围缺口：Live 当前频道 widget 的远程 logo 在 Xray active 时仍可能经普通 Glide 请求。current 已补成与频道列表相同的 suppression：Xray running 时取消并清空远程 logo，stop / error 后恢复加载。VOD artwork 原本已有 Xray guard；MediaSession remote artwork 在 Xray active 时按黄金行为直接 block，而不是改走 Xray 下载。

### 2026-09-29 — TV 网络恢复补齐旧 client、图片失败缓存与 single-entry 边界

Glide 原先在初始化时固定保存 `OkHttp.client()`，普通 API client 在待机 / 换网恢复后被重建时，Glide 仍可能继续持有旧 transport。现在 `OkGlideModule` 每个请求动态取得当前 API client；网络 generation 恢复时也会清理 `ImgUtil` 的 transient failed URL 集合，使网络恢复后的图片重新具备重试机会。

网络恢复仍保留 generation、`recoveredGeneration`、stale callback / task-id 拒绝、Spider 串行 clear、API 与 playback/Xray client 隔离等 current 改进。Leanback Manifest 已取消 BootReceiver 与 `RECEIVE_BOOT_COMPLETED`，避免在 Home / `TvNetworkLifecycle` 之外形成第二个独立网络入口。约 6 秒稳定检查之后网络才恢复的慢唤醒场景仍属于真机验证项；没有证据前不增加永久轮询或默认网络 callback。

### 2026-09-29 — 升级兼容补上字幕偏好与 Chaquopy process ABI

字幕设置迁移会按 legacy caption 状态 → `subtitle_style_source` → `subtitle_style` 的顺序读取，避免升级用户丢失已有样式偏好。

Chaquopy 资产选择不再直接按设备 `Build.SUPPORTED_ABIS` 的跨位数顺序挑选；先用 `Process.is64Bit()` 确定实际 App process bitness，再从对应的 32/64-bit ABI 列表中选择 Python native requirements。这个边界特别针对支持 64-bit 的电视上安装 32-bit Leanback APK 的场景。

### 2026-09-30 — MPEG-H、gomobile runtime 与冷启动 LiveConfig 重新收口

current player candidate 已从 16 个 AAR 修正为 17 个，补回固定 FongMi/media 源码本来就存在的 `lib-decoder-mpegh`；current build / publish 还会在最终 Leanback APK 检查 `MpeghAudioRenderer` 与 `libmpeghJNI.so`，避免再次出现源码支持但最终 APK 丢扩展的情况。

`scripts/build/build-published-libxray-aar.py` 继续保留官方 v26.7.28 AAR 中未混淆的通用 `go/**` runtime。进一步核对确认：官方 v26.7.28 `go.mod` 固定 `golang.org/x/mobile v0.0.0-20260709172247-6129f5bee9d5`，与发布 JNI BuildID 指向的 x/mobile commit 一致；因此目前没有证据支持“官方 go runtime 与黄金 JNI 来自不同 gomobile ABI 世代”的担忧。这个结论是 source/provenance 级证据，不替代 Android 真机 native 运行验证。

Leanback Manifest 已不再注册 BootReceiver，但冷启动 LiveConfig 仍有两层静态入口：Home 初始化无条件执行 `LiveConfig.get().init().load()`；如果 Live 被以 empty 状态启动，`LiveActivity.checkLive()` 也会再次执行 `init().load(callback)`。因此去掉 boot-time network callback 不会在代码结构上删除首次 LiveConfig 初始化路径；冷启动真机仍应保留回归测试。

### 2026-09-30 — 最终 APK provenance / Manifest 验收提升为发布硬门槛

此前 current build 对 MPEG-H 已有最终 APK packaging gate，但 Xray、FFmpeg、Libass 与最终 merged Manifest 仍主要依赖构建输入 / 源码层证据。现在 current build 与 publish 都会在 assemble 后直接验证最终产物：双 ABI APK 中的 Xray `libgojni.so`、FFmpeg、MPEG-H、Libass 必须与已验证 AAR 的 ELF runtime `PT_LOAD` image 一致；Manifest 必须保留 Xray 私有进程与非 exported 约束，并拒绝 boot、电话、安装包和 VPN 相关敏感权限/组件回流。

native 比较刻意不使用最终 APK 内 SO 的 whole-file SHA。Android Gradle strip 会改 ELF section metadata，因此整文件 SHA 不同并不代表运行时代码被替换；验证器只归一化 strip-only section-table header 字段，真正的 runtime load segment、flags、地址和内容仍必须一致。这个 gate 证明的是最终 APK packaging provenance，不替代 Android TV 真机上的 ART/JNI/网络行为验证。

### 2026-09-30 — full-JADX 第二轮外围调用图审计补回 Player rebuild 弹幕 client

本轮不再只搜索文件名或直接 `Xray` 文本，而是从黄金 APK full JADX 的 `th2`（旧 PlayerManager）反向枚举 Xray-aware 方法 caller：`m9321h` / `m9315H` 的 HTTP client handoff、`m9332s` 的 active-session guard、`m9324k` / `m9325l` 的当前播放 URL / session 状态，再逐个映射到 current。已重新核对自动/手动弹幕搜索、字幕 search/detail/download、Live EPG/XML、MediaSession remote artwork、VOD/Live artwork、RTSP/DRM、外部播放器 chooser、/media 状态 JSON 与手机导入入口。

这轮找到一个此前测试没有锁住的真实外围遗漏：黄金 `ye2/af2` 在每次 Player/engine rebuild 后都会重新注入 Xray-aware 弹幕 OkHttp client；current 的通用 `PlaybackActivity.syncPlayerView()` 只重新绑定 Player、danmaku controller/source 和 debug view。虽然 START/STOP/ERROR 的 Live/Video Xray callback 另有显式刷新，decode/未来 engine rebuild 仍不应依赖这些特定回调。current 已在 `syncPlayerView()` 的 `setPlayer` 后统一执行 `updatePlaybackDanmakuClient()`，并把这一行为加入 playback parity guard。

同时把 full-JADX 反查出的但原 guard 未显式锁住的外围 surface 加入测试：Xray 手机导入 Push 页面、server `/media` 的当前 URL/状态字段、外部播放器 chooser 使用当前 URL/headers/position/title、VOD active-Xray artwork 阻断。这样以后不再靠人工记住这些“类名不带 Xray、但通过旧 PlayerManager 间接取得 Xray 状态/client”的路径。

### 2026-09-30 — 同步 FongMi/TV 最新 redirect-aware proxy 基线

核对 FongMi/TV 当前 HEAD 后确认，最新源码 `c616c0aa3613e87529791587a9f71b78c278c991` 只是上一固定 5.6.3 基线 `4afc4473e22a7ed3d98ee12233e0c2a490061000` 的直接子 commit，提交主题为 `Fix proxy selection across redirects`；上游 `app/build.gradle` 的 `versionName` 仍为 5.6.3。FongMi/Release 的 5.6.7 / 5.6.8 版本号因此不能机械理解成五轮 TV 源码架构升级。

这笔上游变化只进入 `catvod` 网络基础层：新增 redirect-aware `ProxyRedirectInterceptor`，让 300/301/302/303/307/308 后续请求继续使用正确的 proxy policy；`OkProxySelector` 用 generation 使旧 policy 在 clear 后失效；`OkAuthenticator` 依据 request 上的 policy 选择认证信息，并在代理切换时避免把旧 `Proxy-Authorization` 带到新代理；同时补上跨 host Authorization 清理、no-redirect 行为、follow-up 上限和连接池复用回归测试。

FingMi-Xray 合并时没有用上游 `OkHttp.java` 整文件覆盖 current：继续保留 TV 网络恢复的独立 API / player client、`resetApiNetworkForResume()`、DNS generation reset 与异步旧 client 清理，只把上游 redirect policy 接入共同 builder。额外的 `tests/test-tv-network-recovery.py` coexistence guard 同时锁定“上游 proxy redirect 修复存在”和“Home 网络 generation 只重建 API client、不破坏后台 playback client”，防止未来同步任一侧时覆盖另一侧。

### 2026-09-30 — 5.6.8 Release 二进制取证纠正 Libass / 媒体同步边界

5.6.6 Release 被删除后，current-main 首次切换到 5.6.8 immutable APK 容器时，原有 SO hard pin 正确拦截了变化：5.6.8 v7 `libmedia3ass.so` 实际为 `58bc8373…`，并非旧 `052c81b5…`。随后对 5.6.7 / 5.6.8 双 ABI APK 做独立 inventory，确认两版 Libass SO whole-file SHA 与 PT_LOAD runtime image完全一致，说明这是最迟自 5.6.7 起的上游新 native 基线，而不是 5.6.8 的偶然重打包。双 ABI ELF 中 17 个 RegisterNatives descriptor 与 current reconstructed `LibassNative.java` 逐项一致，`LibassFrame(int, LibassImage[])` 与七参数 `LibassImage(..., textureId)` constructor ABI 也保持不变；但 API 相同不能替代 render/ownership 行为验证，因此迁移仍需跑完整 native contract。

同一次 Release diff 还确认 5.6.7 → 5.6.8 的 DEX 确实变化，native 变化集中在 `libavcodec.so`、`libmpv.so`、`libnodebridge.so`；Libass 在两版之间不变。5.6.8 full-JADX 明确包含 `FfmpegDolbyVisionP7Converter`，而固定 `FongMi/media@3c2cbe8` 源码树没有该类；因此公开 FongMi/TV/media HEAD 不能被当作 5.6.8 Release 的完整源码快照。上游同步必须区分“公开源码可直接合并”和“Release-only 媒体二进制/行为需单独 provenance”的两层证据。

同轮 DEX 还确认 TV 音量增强滑杆真实上限为 `2000`（20 dB，步长 100），而公开源码仍为 1200；该差异不依赖未公开 native，已在同步分支直接更新 `AudioSetting.MAX_BOOST` 并加入 source guard。Dolby Vision Profile 7、Libass、FFmpeg/MPV 等媒体变化不采用反编译代码直接回填，必须优先寻找真实公开源码；找不到时只能作为发布二进制 provenance 输入，并明确记录证据层级。

### 2026-09-30 — 黄金 Xray 第三轮反向调用审计补齐 UI / rebuild / security 边界

在 full-JADX 第二轮之后继续从黄金 `th2` / Service / security helper 反向枚举所有 caller，而不是仅检查直接包含 Xray 文本的文件。本轮确认 Player snapshot 的 7 项状态（position、playWhenReady、playbackParameters、repeatMode、volume、audioOffset、textOffset）、ERROR/STOP/换源的 snapshot 保留与恢复顺序、RTSP/DRM/DataSource scheme/public-destination guard、Service cleanup/RESET_SECURITY 与 TLS/HY2 TOFU identity 都与黄金语义一致。

本轮同时补回三个可观察差异：通用 Player/engine rebuild 后重新执行 `updatePlaybackDanmakuClient()`；VOD 控制条恢复黄金顺序“下一集 → Xray → 上一集 → 解析 → 播放器”；Xray core executor 线程名恢复 `fongmi-xray-core`，并删除黄金 APK 没有的逐次 native invoke stderr 日志。对应 playback/core parity guard 已锁住这些行为。

另外新增 `tests/test-xray-transport-security-parity.py`，用纯 JVM differential harness 对 current 与 readable legacy transport-security 实现做一一比较，覆盖 HY2/TLS identity、first trust、重复 trust、证书变化拒绝、port hopping、websocket host fallback 的大小写边界、已有 pcs/vcn 不重复 probe、migrated uppercase pin 不被静默规范化等行为；current-main 与 publish 都执行该 guard。

### 2026-09-30 — recovery dexdump 与 current-main 临时触发都改为显式 source guard

Android build-tools 37 的 plain `dexdump` 会把 class 边界打印成带填充空格的 `Class #N            -`。本轮真正导致 targeted extraction 恒为 0 的根因，是 workflow heredoc 里的 Python raw regex 被双重转义成了字面 `\\s` / `\\d`，location 输出的换行也被写成了字面 `\\n`。现已改为真实 `\s` / `\d` / `\n`，并显式固定 `-l plain`；同时继续用 raw DEX descriptor（例如 `La04;`），不把 JADX synthetic `p000/` display package 当作 DEX 名字。修复后 recovery workflow 已完整通过 full JADX、双 ABI APK/DEX inventory 与 targeted dexdump。

`current-main-build.yml` 现在和 publish 一样固定 `BUILD_SOURCE_SHA` 并验证临时 push 的 source commit。连接器无法直接调用 `workflow_dispatch` 时，只允许两阶段 marker 触发：先临时给 workflow 增加只监听 `.github/.trigger-current-main-build` 的 push path，再提交只改变该 marker 的 source commit；真正 build 只接受 marker-only commit。正常仓库状态仍必须是 pure `workflow_dispatch`，marker 也必须在验证结束后删除。



### 2026-10-01 — 5.6.8 Dolby/FFmpeg closure 通过 full current-main；Manifest 与 MPV/ISO 边界收口

针对 5.6.8 Release-only Dolby / FFmpeg 的定向 APK/JADX/native 取证已经从“接口准备”推进到 current 构建链闭环。P5 renderer、P5 VideoSink/native policy、P7 converter lifecycle、`DefaultRenderersFactory`、`DecodeTrackSelector`、R8 keep 与完整 5.6.8 FFmpeg native closure 均已接入固定 17-AAR player candidate；current / publish 不再恢复历史 5.6.0 单个 `libffmpegJNI.so`。

当前 full current-main TV build 已验证通过以下层级：

- 固定 FongMi/media player candidate 的 17-AAR rebuild/verifier；
- 5.6.8 双 ABI FFmpeg closure restore/check；
- current Java → 黄金 v7 / arm64 Xray native parity；
- 5.6.8 Libass rebuild/import；
- Leanback Java 编译；
- armeabi-v7a / arm64-v8a 两个 TV Debug APK assemble；
- MPEG-H 最终 class/native packaging；
- Xray、完整 FFmpeg closure（含 `libffmpegDoviJNI.so`）、MPEG-H、Libass 在最终 APK 中的 `PT_LOAD` provenance；
- 最终 merged Manifest security contract；
- current-main debug artifact 上传与旧 artifact 清理。

验证过程中修正了三类构建门槛问题：Libass importer 仍持有 superseded candidate SHA；最终 APK 实际位于 `leanback/debug/`，native / Manifest gate 必须递归发现产物；最终 merged Manifest 从外部依赖带入 `READ_PHONE_STATE`，app 主 Manifest 现在用 `tools:node="remove"` 明确剔除，并由 source guard 与最终 APK checker 双重锁定。最后一轮 full build 已在这些修复后完整成功。

同一阶段继续审计 5.6.7 / 5.6.8 Release，确认 MPV / ISO 仍是独立未完成面：Release MPV bridge 新增 long-result script command、stream registry / `media3iso://` remote ISO、secondary subtitle scale；固定 public `libplayer.so` 与 Release 字节不一致，`libmpv.so` 也已变化；Release 还包含 public source 没有的 `libisoJNI.so` / native disc-navigation 路径。后续必须把 MPV Java bridge + `libplayer.so` + `libmpv.so` 作为同一 ABI 单元恢复/验证，并单独建立 ISO native provenance，不能只换一个 SO。5.6.8 `libnodebridge.so` 变化也继续作为独立 provenance 项处理。


### 2026-10-01 — 5.6.8 MPV bridge 第一阶段接入并通过 full current-main

5.6.8 targeted native audit 重新对固定 public `libplayer.so/libmpv.so` 与 Release 双 ABI二进制做了独立 ELF/JNI 对比。Release `libplayer.so` 明确新增 `enqueueCommandLongResult`，command reply descriptor 从 `(JI)V` 升为 `(JIJ)V`，并按类名/方法名调用 `MPVLib$Stream` 的 `read/seek/size/cancel/close` 与静态 `openStream`；同时其 NEEDED 包含 `libmpv.so`、`libavcodec.so`、`libswscale.so`。这证明新版 Java bridge、`libplayer.so`、`libmpv.so` 不能拆开迁移。

current 已新增 MPV overlay、双 ABI native contract/restorer/checker，并把 overlay identity、关键 class、mpvplayer unit-test task、importer immutable mutation、current/publish restore/check 和最终 APK PT_LOAD gate 接入现有 17-AAR 构建链。app 的 MPV managed options 也已加入 `secondary-sub-scale`。随后 run `36758945496` 在 marker source `dc7b5b06...` 上完整成功：source guards、17-AAR rebuild、MPV bridge unit tests、5.6.8 MPV native restore/check、Xray parity、Libass、Leanback Java compile、双 ABI APK assemble、MPEG-H、最终 Xray/FFmpeg/MPV/MPEG-H/Libass PT_LOAD 与 merged Manifest security contract 全部通过。remote ISO / disc menu 与 `libisoJNI.so` 仍保留为下一阶段；真机 MPV script/stream 行为仍需运行时验收。
### 2026-10-01 — MPV remote ISO stream 第二阶段接入并通过 full current-main

在第一阶段 MPV bridge 已通过 full current-main 后，继续按 5.6.7/5.6.8 Release 证据恢复 HTTP(S) ISO 的 `media3iso://` stream 路径。Release full-JADX 已确认触发条件为 MediaItem MIME `video/x-iso` 或 URI path 以 `.iso` 结尾（忽略大小写）；只有 HTTP/HTTPS 会注册临时 `media3iso://<uuid>/disc.iso`，本地 ISO 只去除 fragment 后直接交给 mpv。

current overlay 已升级为 `fongmi-tv-5.6.8-mpv-bridge-v2`，新增：

- `MpvPlayerConfig` 可选 `DataSource.Factory`；未提供时由 `MpvPlayerComponents` 使用 `DefaultDataSource.Factory(applicationContext)`，与 Release fallback 语义一致；
- `MpvRequestHeaders` 可把 MediaItem request metadata 的普通 headers、User-Agent、Referer 转为 Media3 DataSource request headers；
- `MpvIsoStreamManager` 负责 ISO 检测、`media3iso://` 注册、换源 / stop / release 的 unregister/cancel 生命周期；
- `MpvIsoStream` 实现 Release `MPVLib.Stream` 的 `read/seek/size/cancel/close` 可观察接口，64 KiB read buffer、seek 时重新打开 Range、EOF 返回 0，并把 DataSource I/O 失败作为 Java runtime exception 暴露给 JNI；
- mpvplayer 新增 datasource dependency 和 `MpvIsoStreamTest`，candidate builder/verifier 也要求 `MpvIsoStream` / `MpvIsoStreamManager` class 确实进入 `lib-mpvplayer-release.aar`；
- build hygiene 同步锁住 overlay v2、`media3iso://`、DataSource factory 与新 class，防止后续回退成“只有 Stream ABI、没有实际 ISO provider”。

证据边界：Release 内部还有一层约 4 MiB page、3 worker 的并行 Range 预取/cache；当前第二阶段先恢复 URI/header/seek/read/size/cancel 生命周期与 JNI 可观察行为，没有把该内部性能优化冒充成已逐实现等价。随后 run `36796521437` 在 marker source `4c3cc9dd...` 上完整成功：source guards、17-AAR rebuild、MPV bridge/ISO overlay unit tests、5.6.8 MPV native restore/check、Xray parity、Libass、Leanback Java compile、双 ABI APK assemble、MPEG-H、最终 Xray/FFmpeg/MPV/MPEG-H/Libass PT_LOAD 与 merged Manifest security contract 全部通过。`libisoJNI.so`、`IsoNavigationSession` / native UDF、disc-menu 以及 `libnodebridge.so` 仍未迁移；remote ISO 真机 Range/seek/cancel 行为仍属于运行时验收层。

### 2026-10-01 — native ISO UDF bridge 第三阶段接入并通过 full current-main

继续复用 5.6.7 / 5.6.8 Release 取证后确认：双 ABI `libisoJNI.so` 在 5.6.7 → 5.6.8 间字节不变，因此这是从 5.6.7 起存在并由 5.6.8 继续携带的 Release-only native ISO 单元，而不是 5.6.8 才出现的独立变化。5.6.8 JADX 同时确认 `androidx.media3.extractor.iso.udf.NativeUdfFileSystem` 通过 `System.loadLibrary("isoJNI")` 提供 `nativeOpen/nativeClose/nativeFindFile/nativeListFiles`，并在不支持的 image 上回退到公开 Java `UdfFileSystem`。

current 已新增 `fongmi-tv-5.6.8-iso-native-udf-overlay-v1`：在固定 public media source 上 clean 恢复 `NativeUdfFileSystem`、让 `UdfFileSystem` 采用 native-first / Java-fallback，并在 `IsoParsedMedia.close()` 关闭 native UDF handle。双 ABI `libisoJNI.so` 由独立 `published_568_iso_contract.py` 固定 SHA，只允许从 SHA 固定的 5.6.8 Leanback APK 添加到 rebuilt `lib-extractor-release.aar`；current/publish restorer/checker、importer immutable mutation、build hygiene 和 final APK PT_LOAD provenance gate 已接入。

当前边界仍然明确：这一阶段只恢复 native UDF filesystem bridge，不把大型 Release `IsoNavigationSession` 状态机/光碟菜单行为冒充成已完成。该状态机包含 disc type/menu、title/chapter/clip、track selection、seek、overlay/still/resume 等大量 JNI surface，后续应按 clean implementation + native provenance 单独闭环。\n\n第三阶段在 full current-main 中暴露出一个真实组合问题：Libass 重建得到的 extractor AAR 是确定性裸重建产物，而在它之前导入的 5.6.8 ISO restore 已经向当前 extractor 加入双 ABI `libisoJNI.so`。Libass importer 不能简单用裸 extractor 覆盖当前 AAR，否则会把已恢复的 ISO native 删除。现在 importer 会先验证当前 extractor 中的两份 `libisoJNI.so` 必须与 `published_568_iso_contract.py` 固定 SHA 一致，再只把这两项 native entry 合并进确定性 Libass extractor；合并产物还会先跑 `check-published-568-iso.py`，最后再做 class/native ownership inventory 后原子替换。Libass 裸 extractor 与 candidate 的确定性 SHA 分别固定为 `f4667540c598416895cae5c4201fbe1c0e30c88d2673395a23db91b1b107278b` 和 `f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861`。\n\nrun `36808601960`（source `38e8fe7b4fadef1d7f649bc9bbc1994915121945`）随后完整成功：17-AAR rebuild、5.6.8 FFmpeg/MPV/ISO native restore、Xray 双 ABI parity、Libass rebuild/import、Leanback Java compile、双 ABI TV Debug APK assemble、MPEG-H、最终 Xray/FFmpeg/MPV/ISO/MPEG-H/Libass native provenance 与 merged Manifest security contract 全部通过。临时 push trigger 与 marker 已在成功后用单一原子提交 `303b109c1cbfa7c62de1379d5e59deb4ab877b39` 一并移除，正常仓库状态恢复为 pure `workflow_dispatch`。Android TV 真机 ISO/UDF 与后续 disc-menu 行为仍属于运行时验收层。


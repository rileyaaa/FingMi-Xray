# FingMi-Xray 开发与维护

本文面向继续维护当前 `main` 的开发者，说明**当前工程基线、模块接线、构建依赖、上游同步方式和验证规则**。

长期架构边界见 [PROJECT.md](PROJECT.md)。`v5.6.0-xray.5` 的恢复、native provenance 与 v7 Xray 黄金行为证据见 [RECOVERY.md](RECOVERY.md)。当前 `main` 负责架构与构建，v7 黄金参考负责约束 Xray 外部行为；两者不能混为旧 faithful 架构重建。

## 1. 当前工程基线

当前应用基于 FongMi/TV 5.6.3：

- 上游目标 commit：`4afc4473e22a7ed3d98ee12233e0c2a490061000`
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

native 调用前后会输出不含节点、凭据或配置正文的阶段日志，例如 `native invoke begin/end: getFreePorts`。如果只有 begin 没有 end，ADB / logcat 就可以把问题继续缩小到 libgojni、ARM 转译或 native runtime。

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

固定 candidate 与相关 AAR 的具体 SHA 由 `current-main-build.yml` 和对应 fixture 保存；构建时按 hash 校验，不在本文重复维护另一份容易过期的 pin 表。

### app adapter

当前 app 还包含 FongMi 5.6.3 调用面需要的少量 adapter，例如：

- `LibassFontFile`
- `DanmakuPlayerViewController`

这些是当前 app 与固定媒体依赖之间的兼容边界。

### MPV

固定 MPV AAR 缺少 5.6.3 app 使用的部分 secondary subtitle / font 新接口。

`MpvPlayerEngine` / `MpvUtil` 通过固定二进制已有能力做映射，包括 secondary subtitle 与 MPV config option。它是一层兼容桥，不应描述成“已经恢复了一个不存在的新版 MPV 二进制”。

## 6. 二进制依赖

大型 AAR / APK / SO 不作为普通源码直接提交。

当前可重复构建依赖以下几类输入：

- 固定 FongMi/media player candidate；长期副本保存在项目 Release `build-inputs-5.6.3`，workflow 下载后继续按固定 SHA 校验，不再依赖会过期的 Actions artifact；
- 当前构建使用的 FFmpeg JNI；
- 官方 libXray v26.7.28 AAR 外层容器，以及从固定历史发布 APK 恢复、彼此匹配的 API v2 gomobile Java bindings 与 v7 / arm64 Go JNI；
- 按固定输入重建的 Libass compatibility AAR。

目前 FFmpeg JNI 与 libXray API v2 的 Java/native 绑定来源仍可追溯到历史 `v5.6.0-xray.5` APK，因此 current-main workflow 会下载该历史 Release 并按固定 SHA 作为 provenance / reproducibility 输入。libXray 的 gomobile Java bindings 与 `libgojni.so` 必须视为同一个 JNI ABI 单元：不能把官方 v26.7.28 的 `classes.jar` 与历史发布版 API v2 `libgojni.so` 单独拼接，否则 native 初始化可能查找官方旧 bindings 不包含的模型类（例如 `libXray.AgeDecryptConfig`）并导致进程崩溃。当前构建由 `scripts/build/build-published-libxray-aar.py` 从经过 SHA 校验的发布 APK 恢复发布版 `libXray/**` Java bindings，保留官方 v26.7.28 AAR 中干净、未经过 App R8 混淆的通用 `go/**` gomobile runtime classes，再与同一发布版的 v7 / arm64 Go JNI 配套放回官方 AAR 外层容器。**在这一构建链中，旧 APK 负责提供固定二进制 provenance；同一 v7 APK 另作为 Xray 外部行为黄金参考，但 current-main 不要求恢复或通过 5.6.0 faithful 架构 / 完整 APK 重建。** 当未来为当前架构建立新的独立 libXray 发布源后，应整套切换 Java bindings 与 native，并同步更新 pin。

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
2. 下载并校验固定媒体输入；
3. 准备并校验固定 FFmpeg JNI，并重建 Java bindings 与 Go JNI 配套的 libXray compatibility AAR；
4. 重建并导入 Libass compatibility AAR；
5. 执行 current Java → 发布版 v7 / arm64 native 动态 Xray chain parity（统一以 v7 发布行为为黄金 oracle，包含 KCP golden cases 与发布版 `testXray` runtime validation）；
6. 只编译 Android TV / Leanback Java；
7. 只 assemble Android TV / Leanback 两个 ABI 的 Debug APK；
8. 上传短期 TV debug artifact（保留 2 天）供临时验证；上传成功后自动删除同名旧 debug，只保留最新一份。失败报告只保留 1 天。历史 recovery workflow 的 JADX/DEX、faithful APK、native dependency、player AAR 和 upstream snapshot artifacts 也只作临时复核，统一最多保留 3 天；长期 build input 只进入项目 Release。Gradle 命令继续使用 `--warning-mode all`；当前剩余会在 Gradle 10 失败的 deprecation 已确认全部来自固定上游同样使用的 Chaquopy Gradle plugin 17.0.0（multi-string dependency notation 与 execution-time `Task.project`），不是本仓库 Gradle 脚本。当前保持 FongMi/TV 5.6.3 的 17.0.0 pin，待上游或 Chaquopy 升级时再单独验证 Python runtime 与双 ABI assets，不在本 fork 中为消 warning 私自升级。

测试发布器：

`.github/workflows/publish-current-main-test-release.yml`

它以 `BUILD_SOURCE_SHA` 作为唯一构建与发布源码，重新准备固定依赖、执行源码 guard、执行 current Java → 发布版 native 动态 Xray chain parity、只编译/assemble Android TV / Leanback 两个 ABI，然后直接发布新的测试 Pre-release；成功包不再额外复制一份到 Actions artifact。正常手动触发时 `BUILD_SOURCE_SHA = github.sha`。

如果因为当前 GitHub connector 缺少 workflow dispatch 能力而临时触发 publish，必须采用**两阶段 marker 触发**：先单独提交一次只给 publish workflow 临时增加 `push`；这个“arm” commit 自身会触发一条 run，但 workflow 的首个 source guard 会因为它不是 marker-only commit 而立即失败，不进入 SDK、native parity 或 Gradle 构建。随后用第二个只修改 `.github/.trigger-publish-current-main-test` 的 commit 真正触发完整 run；workflow 会验证该触发 commit 的唯一变更就是 marker，并以该 commit 自身作为 checkout / build / Release target。完整 run 执行期间必须保持 publish workflow 的临时 `push` 不变，并禁止再向 `main` 提交其他内容；只有 Release 创建、tag / digest 验证和上一版测试 Release 替换全部成功后，才恢复为纯 `workflow_dispatch` 并删除 marker。成功的 `test.4` 就是在 Release 完成后才撤回临时 trigger；提前撤回会让 default branch 与显式 Release target 的 workflow 树发生差异，并触发 GitHub Release API 的 `HTTP 403: Resource not accessible by integration`。

这个约束来自已复核的发布记录：成功的 `test.4` 显式 Release target 自身只修改 marker；两次失败的 `test.5` 显式 target 自身都直接修改 workflow YAML，并在 `gh release create` 得到 `HTTP 403: Resource not accessible by integration`；同日 `build-inputs-5.6.3` 未显式指定 SHA target 时又能由同类 `contents: write` Actions token 正常创建。因此临时启用 `push` 的 workflow 修改 commit 不得直接作为显式 Release target。发布 job 保持最小权限 `contents: write + actions: read`。新测试 Release、tag 指向的 `BUILD_SOURCE_SHA` 与两个 Leanback APK digest 全部验证成功后，workflow 才删除 YAML 中指定的上一版测试 Release / tag。其他历史 Release 不在这条替换链中，也不参与当前版本的最终验收。

两个 current-main workflow 都必须先执行：

- `tests/test-xray-android-runtime-compat.py`：防止 Java 21 可编译、但旧 Android ART 运行时不存在的 API 再进入 `:xray`，并防止 current-main 构建重新退回“官方旧 Java bindings + 单独替换发布版 Go JNI”的不匹配组合；
- `tests/test-xray-core-parity.py`：守住配置生成、存储 / TOFU、Service 重试清理、Settings 核心语义，并要求 current public destination guard 与发布 `qz3` readable mirror 保持逐行为等价；
- `tests/test-xray-playback-parity.py`：守住 VOD / Live、播放器代理切换、媒体旁路和资源释放语义；
- `tests/test-xray-session-races.py`：锁住发布版 STOP / timeout / callback 的竞态顺序；
- `tests/test-xray-service-client-lifecycle.py`：直接编译真实 Service client，锁住 bind timeout、cancel/unbind、Binder death 与 stale callback / connection generation；
- `tests/test-xray-normalizer-parity.py`：把 current share-link normalizer 与 display helper 对发布版 readable reference 做纯 JVM differential parity；
- `tests/test-upstream-update-disabled.py`：防止 FongMi 上游自更新入口、直接 release endpoint 调用或 APK 安装权限重新进入当前 fork；
- `tests/test-build-hygiene.py`：防止错误 XLIFF namespace、非 positional 多参数 string、废弃 ABI API 和仍基于 Node 20 的旧 Actions major 再进入构建。
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

# FingMi-Xray 开发与维护

本文面向继续维护当前 `main` 的开发者，说明**当前工程基线、模块接线、构建依赖、上游同步方式和验证规则**。

长期架构边界见 [PROJECT.md](PROJECT.md)。`v5.6.0-xray.5` 的恢复材料见 [RECOVERY.md](RECOVERY.md)，但它现在只承担历史证据和部分 native 二进制来源说明，不再是当前工程的验收基线。

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

当前 `main` 是现行产品与后续开发的基线。**从 5.6.3 重构线起，当前 `main` 及其最新测试 / 正式构建是唯一的功能回归和发布验收基线。** `recovery/legacy-src/` 只保留 5.6.0 faithful 历史恢复；正常开发、测试和发布不再要求运行 faithful build、对齐旧 APK 行为或等待旧版本独立 cloud build 验收。

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
- 在切集、切台、换源等身份变化时结束旧会话；
- 把新的 `XrayHttpClient` 交给播放器；
- 在 Activity 销毁时关闭 session。

业务页面只决定“当前是什么播放身份”，不实现 Xray Core 细节。

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

`TvNetworkLifecycle` 负责生成前后台 / screen 网络代际；`NetworkRecoveryCoordinator` 每个需要恢复的 generation 执行一次普通网络重建：

1. 取消旧业务请求；
2. 重建 API / DNS；
3. 清理 Spider；
4. 等待网络稳定；
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

- 固定 FongMi/media player candidate；
- 当前构建使用的 FFmpeg JNI；
- 官方 libXray v26.7.28 AAR 外层容器，以及从固定历史发布 APK 恢复、彼此匹配的 API v2 gomobile Java bindings 与 v7 / arm64 Go JNI；
- 按固定输入重建的 Libass compatibility AAR。

目前 FFmpeg JNI 与 libXray API v2 的 Java/native 绑定来源仍可追溯到历史 `v5.6.0-xray.5` APK，因此 current-main workflow 会下载该历史 Release 并按固定 SHA 作为 provenance / reproducibility 输入。libXray 的 gomobile Java bindings 与 `libgojni.so` 必须视为同一个 JNI ABI 单元：不能把官方 v26.7.28 的 `classes.jar` 与历史发布版 API v2 `libgojni.so` 单独拼接，否则 native 初始化可能查找官方旧 bindings 不包含的模型类（例如 `libXray.AgeDecryptConfig`）并导致进程崩溃。当前构建由 `scripts/build/build-published-libxray-aar.py` 从经过 SHA 校验的发布 APK 恢复发布版 `libXray/**` Java bindings，保留官方 v26.7.28 AAR 中干净、未经过 App R8 混淆的通用 `go/**` gomobile runtime classes，再与同一发布版的 v7 / arm64 Go JNI 配套放回官方 AAR 外层容器。**这些旧 APK 只是二进制来源证据，不代表当前 5.6.3 需要通过 5.6.0 faithful 行为验收。** 当未来为当前架构建立新的独立 libXray 发布源后，应整套切换 Java bindings 与 native，并同步更新 pin。

`current-main-build.yml` 会下载、校验并准备这些固定依赖，再进行 Java 编译和 APK assemble。

当前 compatibility 构建脚本集中在 `scripts/build/`，历史来源提取工具集中在 `scripts/recovery/`，当前源码回归入口位于 `tests/`。修改任何二进制来源或 hash 时，必须同步修改对应验证脚本 / workflow，不能只把一个新 AAR 丢进 `app/libs`。

## 7. 构建

### GitHub Actions

仓库所有可执行 workflow 都必须保持**纯手动**。GitHub 官方 helper action 同时保持 Node 24 兼容 major（当前为 checkout v7、setup-java v6、setup-python v7、upload-artifact v7），避免 runner 强制兼容旧 Node 20 action 所产生的弃用告警：

```yaml
on:
  workflow_dispatch:
```

不保留 `push`、`pull_request`、`schedule`、`workflow_call` 等自动触发。

#### AI 协作执行准则

AI 与用户共同开发时的固定操作限制独立维护在 [AI_COLLABORATION.md](AI_COLLABORATION.md)。其中包括 CI 禁止原地轮询、Actions 状态必须从最新 runs 列表重新确认、以及会话接近平台时限时立即交接返回。


当前工程主构建：

`.github/workflows/current-main-build.yml`

它负责：

1. 准备 JDK / Android SDK；
2. 下载并校验固定媒体输入；
3. 准备并校验固定 FFmpeg JNI，并重建 Java bindings 与 Go JNI 配套的 libXray compatibility AAR；
4. 重建并导入 Libass compatibility AAR；
5. 执行 current Java → 发布版 v7 native 动态 Xray chain parity（包含 KCP golden cases 与发布版 `testXray` runtime validation）；
6. 只编译 Android TV / Leanback Java；
7. 只 assemble Android TV / Leanback 两个 ABI 的 Debug APK；
8. 上传 TV APK、构建说明和 Gradle problems report artifact；Gradle 命令使用 `--warning-mode all`，让剩余 Gradle 10 弃用项在下一次手动构建中直接显示具体来源。

测试发布器：

`.github/workflows/publish-current-main-test-release.yml`

它会从触发时的当前 `main` 重新准备固定依赖、执行源码 guard、执行 current Java → 发布版 native 动态 Xray chain parity、只编译/assemble Android TV / Leanback 两个 ABI，然后发布新的测试 Pre-release。新测试 Release 与两个 Leanback APK 都验证成功后，workflow 才删除 YAML 中指定的上一版测试 Release / tag。其他历史 Release 不在这条替换链中，也不参与当前版本的最终验收。

两个 current-main workflow 都必须先执行：

- `tests/test-xray-android-runtime-compat.py`：防止 Java 21 可编译、但旧 Android ART 运行时不存在的 API 再进入 `:xray`，并防止 current-main 构建重新退回“官方旧 Java bindings + 单独替换发布版 Go JNI”的不匹配组合；
- `tests/test-upstream-update-disabled.py`：防止 FongMi 上游自更新入口、直接 release endpoint 调用或 APK 安装权限重新进入当前 fork；
- `tests/test-build-hygiene.py`：防止错误 XLIFF namespace、非 positional 多参数 string、废弃 ABI API 和仍基于 Node 20 的旧 Actions major 再进入构建。

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
- 实际播放地址变化；
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

静态比较、单元测试、Gradle 编译、APK assemble 与真机运行是不同层级的证据，提交说明和文档必须准确写明实际验证到了哪一层。

## 10. 文档维护

- 项目架构变化：修改 `PROJECT.md`；
- 当前源码结构、构建或上游维护方式变化：修改本文；
- 对旧发布版历史事实或 native provenance 的新证据：修改 `RECOVERY.md`；
- 新增 / 删除反编译文本证据：修改 `apk-reference/README.md`；
- `ORIGINAL_README.md` 保持冻结。

Git 历史仍负责记录“哪一次提交做了什么”。但对影响当前版本行为、构建链或后续排障判断的重要故障与验证结果，应在本文“开发日志”中保留精简记录；纯过程性尝试、无长期价值的失败细节不重复堆积。


## 11. 开发日志

### 2026-09-27 — Xray 保存节点导致 `Xray service disconnected`（test.3 → test.4）

#### 现象

`v5.6.3-xray.test.3` 在 MuMu Android 12 / SDK 32 中保存 Xray 节点时，UI 显示：

`Xray service disconnected`

现场 ADB / crash 证据确认该提示不是原始错误，而是独立 `:xray` 进程已经死亡后的二次结果。

#### 根因

`libXray` 的 Java gomobile bindings 与 `libgojni.so` 被错误混搭：

- Java 侧来自官方 `libXray v26.7.28` AAR；
- Go JNI 则来自历史发布版 `v5.6.0-xray.5` 的 API v2 native；
- native 初始化时会查找发布版 API v2 模型类，例如 `libXray.AgeDecryptConfig`；
- test.3 APK 中不存在该类；
- Android CheckJNI 在 JNI 初始化过程中因悬挂的 `ClassNotFoundException` / 非法 JNI 状态触发 `SIGABRT`，杀死 `:xray` 进程；
- Binder 随后断开，UI 才显示 `Xray service disconnected`。

因此本次问题不属于 Binder / Service 生命周期本身，也不是普通 FongMi 业务问题。

#### 修复

新增：

`scripts/build/build-published-libxray-aar.py`

current-main 构建现在使用以下组合：

1. 从经过 SHA-256 校验的历史发布 APK 恢复发布版 `libXray/**` Java bindings；
2. 保留官方 v26.7.28 AAR 中干净、未经过 App R8 混淆的通用 `go/**` gomobile runtime classes；
3. 配套使用同一历史发布版的：
   - `armeabi-v7a/libgojni.so`
   - `arm64-v8a/libgojni.so`
4. 官方 v26.7.28 AAR 继续作为外层容器；
5. 构建 guard 明确要求 `AgeDecryptConfig` 等已确认的 API v2 bindings 存在，并禁止 current-main 再退回“官方旧 Java bindings + 单独替换发布版 Go JNI”的组合。

构建过程中确认：不能从最终发布 APK 反编译后重新编译 `go.Seq` 等通用 runtime，因为这些类已经经过整包 R8 混淆并依赖混淆后的应用类名；因此 `go/**` runtime 必须保留官方 AAR 的干净版本。

#### Actions 验证

最终成功的测试发布 Actions run：

`36328456284`

APK 构建源码 commit：

`ed8600bc775f5c6e65915da2ecbad933fb54d917`

该 run 已实际通过：

- fork source guards；
- Android SDK 37 准备；
- 固定依赖与 SHA-256 校验；
- 新 libXray compatibility AAR 重建；
- Libass compatibility 重建；
- Leanback Debug javac；
- Mobile Debug javac；
- Debug APK assemble；
- artifact 上传；
- Android TV 两个 ABI APK staging；
- `v5.6.3-xray.test.4` Pre-release 发布；
- 旧 `v5.6.3-xray.test.3` 删除。

最终 workflow 已恢复为纯：

`workflow_dispatch`

一次性 push trigger 与 trigger 文件均已删除。

#### 当前测试基准

测试 Release：

`v5.6.3-xray.test.4`

Android TV / Leanback APK：

- arm64-v8a  
  SHA-256：`1d6dc8046d02bdf31aca6e5ba63b87736de7e17161c45f534059a47db978f7fa`
- armeabi-v7a  
  SHA-256：`85836129e9531fc4ec4e3d8d09ee41f372563f141240a3fcd09fc71a06b42998`

`test.3` 已删除。

#### 验证边界

截至本记录：

- 构建链：已验证；
- Java 编译：已验证；
- APK assemble：已验证；
- Release 上传与替换：已验证；
- MuMu / Android TV 真机运行行为：**仍需继续验证**。

如果 test.4 仍出现 Xray 保存、测试或启动故障，应继续以 ADB 现场证据、`:xray` PID、Binder 状态、`FingMiXray native invoke begin/end`、crash buffer 与 tombstone 为准，不应回退到无证据的全局兼容性修改。


### 2026-09-28 — 重新以 v5.6.0-xray.5 v7 APK 作为 Xray 行为黄金参考

#### 结论

用户确认 GitHub Release 中的 `v5.6.0-xray.5` armeabi-v7a APK 在 Xray 行为上是完整且稳定的参考实现，包括节点导入、连接测试、START / STOP、播放代理、会话切换与网络资源释放。后续维护采用“当前模块化架构 + 旧 APK 完整 Xray 行为语义”的原则：不回退到 5.6.0 的混合架构，也不只针对 KCP 或单一协议修补；分享链接兼容、节点存储与安全、VALIDATE / TEST / START / STOP、Binder / Service 生命周期、播放会话、HTTP / SOCKS / RTSP 接入、错误去敏、超时/竞态与网络资源释放均以发布 APK 的已验证行为为黄金参考，再映射到当前 `:xray` 模块。

#### 重新取证

重新执行了 `Recovery APK analysis`，使用固定 SHA-256 的：

- `FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk`
- `FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk`

完整 v7 JADX 反编译成功并已拉回本地分析。重新生成的关键源码与 2026-09-25 的已存 artifact 哈希一致，例如：

- `p000/a04.java`：相同
- `com/fongmi/android/tv/xray/XrayService.java`：相同

本轮 Actions run：`36374827563`。该 run 的 APK 下载、SHA 校验、JADX 工具下载、APK/DEX 比较与完整 v7 JADX 均成功；旧的 targeted `dexdump` 提取步骤仍因目标匹配脚本未命中而失败，但不影响完整 JADX artifact 的取得。本轮同时修复了私有仓库 Release 资产在 recovery workflow 中用匿名 `curl` 返回 404 的问题，改为使用 `GH_TOKEN` + `gh release download`。所有 workflow 已恢复为纯 `workflow_dispatch`。

#### 与 current-main 的首轮语义对照

旧 APK 已确认的关键链路：

- `convertShareLinksToXrayJson`
- `testXray`
- `pingBatch`
- target URL：`https://www.gstatic.com/generate_204`
- timeout：10 秒
- outbound tag：`fongmi-xray-proxy`
- ping 前把目标 outbound 的 `targetStrategy` 改为 `AsIs`
- START 前先 STOP，失败时最多对 bind/listen 类错误重试 3 次
- STOP 最多尝试 2 次
- Service 销毁时先异步 STOP、等待 executor，最后杀掉私有进程
- 播放代理 HTTP 资源释放顺序包含 dispatcher executor shutdown，并异步 `cancelAll()` + `connectionPool.evictAll()`

current-main 的 `XrayConfigFactory`、`LibXrayBridge.testLatency`、`XrayService`、`XrayHttpClient` 在上述关键行为上与旧 APK 基本一致。因此当前 KCP “HY2 可测试、KCP 在 generate_204 超时”的现象，暂时没有证据指向这些公共 Java 生命周期逻辑。下一步应继续比较同一 KCP 节点在旧 APK 与 current-main 中真正送入 `pingBatch` 的最终 outbound / stream settings，优先确认 KCP transport 配置差异，再决定是否修改代码。


### 2026-09-28 — Xray 发布版行为迁移补录（完整行为，不限 KCP）

#### 维护基线

本轮明确把 `v5.6.0-xray.5` armeabi-v7a 发布 APK 作为 **Xray 全行为黄金参考**。目标不是回退到旧版混合架构，而是保留当前独立 `:xray` 模块、FongMi 5.6.3 宿主和必要的现代安全防护，同时把旧 APK 已验证的 Xray 行为逐项映射回当前模块。覆盖范围包括分享链接兼容、配置生成、传输安全、VALIDATE / TEST / START / STOP、Binder / Service 生命周期、播放代理、HTTP / SOCKS / RTSP、字幕/弹幕/EPG/封面请求归属、切源/切集/换台、失败恢复、资源释放、超时和竞态。

#### 重新反编译与证据来源

- 重新运行 Recovery APK analysis，v7 完整 JADX 成功取得；APK 下载、SHA-256 校验、DEX 比较和完整反编译均成功。
- 私有仓库 Release 资产下载从匿名 `curl` 修正为 `GH_TOKEN + gh release download`。
- recovery workflow 临时 push trigger 已撤回，恢复为手动 `workflow_dispatch`。
- 旧 APK 的 `a04`、`XrayService`、`et1`、`sz3`、`lu2`、`pz3`、`yz3` 等行为继续作为静态对照；不直接复制 R8/JADX 混淆类，而是映射到命名清晰的当前模块。

#### 已迁移/恢复的行为

1. **播放网络切换与所有权**
   - `PlayerManager.setPlaybackProxy` 重新按发布版语义串行化切换，并在代理生效前取消旧网络工作。
   - 补回 `hasXraySession` / `withHttpClient`，让播放器相邻请求在同一代理代际下创建，避免在切换窗口拿到即将销毁的 client。
   - RTSP/RTSPT 使用 Xray SOCKS socket factory，并恢复当前播放请求的 User-Agent 传递。
   - 通用 DataSource 在 Xray 会话中只允许 HTTP(S) 走代理，同时保留 file/content/asset/data/rawresource/android.resource 等本地资源，不允许其他网络 scheme 静默旁路。

2. **字幕、弹幕、封面与播放器相邻网络请求**
   - Danmaku / Subtitle API 恢复 request-id ownership，旧请求只取消自己的 `Call` / `Download`。
   - VOD 自动弹幕、手动字幕/弹幕搜索在 Xray 会话下使用当前播放 client。
   - Xray 代理切换时取消旧 Danmaku / Subtitle 请求和远端 MediaSession artwork；本地 artwork 仍允许。
   - Video/Live Activity 的 Glide artwork target 在 Xray 切换和销毁时显式 clear，避免旧请求回调覆盖新会话。

3. **VOD / Live 生命周期**
   - Activity `onStop` 根据是否后台继续播放决定保留还是释放 Xray playback session。
   - VOD 切站点、切线路、切集、换源、刷新、切 player engine 时先推进 Xray playback generation，旧回调不能污染新播放。
   - Live 换台/换线路/catch-up/refresh 的 Xray reset 边界按发布版恢复；新增待启动 Live source 的 pending-start continuation，而不是在 Xray START 前继续走旧网络解析。
   - 已解析媒体 URL 与尚未解析的 Live direct source 分开处理；`.strm` 与 YouTube HTTP(S) indirection 不在 direct-pending 阶段强制代理，待解析成真实媒体 URL 后再进入 Xray。

4. **Live metadata / logo / EPG**
   - Live EPG 与 XMLTV 网络请求按播放网络 generation 打 tag。
   - 代理切换时取消旧 generation 的 metadata 网络工作。
   - Xray 会话期间抑制绑定频道的远端 logo 直连加载；退出/失败后恢复普通加载。
   - 避免旧 EPG / logo callback 在代理切换后重新写回 UI。

5. **Xray START 失败后的播放器恢复**
   - 恢复发布版“拆掉 Xray engine，但不立即恢复 direct network 播放”的失败语义。
   - 保存当前 `PlaySpec + PlaybackSnapshot`，失败后切回无代理 engine 但不自动 resume；之后 Xray 成功启动可复用保存状态。
   - 防止代理失败瞬间把当前媒体直接暴露到普通网络。
   - Video / Live 对 ERROR 分别处理 UI、session 状态和播放快照。

6. **Settings / Binder 操作生命周期**
   - Settings 侧 VALIDATE / TEST / RESET_SECURITY 只允许单操作拥有当前 Binder generation。
   - 45 秒 operation timeout、cancel/abandon、client replacement、stale callback 丢弃和错误去敏已恢复。
   - 保存节点时只在 RESET_SECURITY 占用时阻止；删除先清保存节点，再在 `:xray` 私有进程清传输安全状态。

7. **核心配置与分享链接兼容**
   - 当前 `XrayShareLinkNormalizer` 与恢复版行为对照后，VLESS / VMess / Trojan / Shadowsocks / HY2 / Hysteria2 的主要 normalize 路径保持一致；Android 12 不安全的 Java API 只做等价替换。
   - 保留旧 APK 的 Shadowsocks legacy/SIP003 plugin 兼容、Trojan TLS 默认行为、HY2 hopping / `mport` / `ports` / obfs 校验、VMess JSON port 校验等。
   - `XrayConfigFactory` 保持发布版关键配置：单 proxy outbound、删除 `sendThrough`、`targetStrategy=ForceIP`、sockopt `domainStrategy=AsIs`、本地 SOCKS noauth、UDP 取 UI 设置、DNS/routing/private block。
   - TEST 继续按发布版深复制 config，把目标 outbound 的 `targetStrategy` 临时改成 `AsIs`，`pingBatch` 10 秒请求 `https://www.gstatic.com/generate_204`。没有为了 KCP 擅自改掉这条已验证行为。

8. **安全存储与证书 TOFU**
   - 节点仍使用 AndroidKeyStore alias `fongmi_xray_share_link_v1` + AES/GCM，字段 `link_ciphertext` / `link_iv` / `udp` 与发布版一致。
   - HY2/TLS insecure 链接先 probe 证书，再写入加密 pin；后续证书变化拒绝自动信任。
   - RESET_SECURITY 同时清 current/legacy pin 位置并删除 pin encryption key。

9. **Service / native 调用与清理**
   - VALIDATE / TEST / START 对 bind/listen 类错误最多重试 3 次；START 先 stop 旧 core。
   - START 顺序保留 `getFreePort -> create config -> testXray -> runXray -> getXrayState`。
   - STOP 最多尝试 2 次；无法可靠清理时通过 generation invalidation / 私有进程重置避免残留。
   - Service 销毁时先停止 core、关闭 executor，最终保证 `:xray` 私有进程退出。
   - OkHttp Xray resources 继续显式 shutdown dispatcher executor，并异步 `cancelAll()` + `connectionPool.evictAll()`。

#### 防回归测试

新增/扩展：

- `tests/test-xray-playback-parity.py`
  - 守住播放代理切换、字幕/弹幕 ownership、artwork、Live/VOD 生命周期、proxy failure recovery、Live metadata 等发布版行为。
- `tests/test-xray-core-parity.py`
  - 守住分享链接协议覆盖、加密存储、配置 JSON 关键字段、`pingBatch`、TOFU、Service 重试/清理和 Settings operation lifecycle。
- `tests/test-xray-android-runtime-compat.py`
  - 继续阻止 Java 21 可编译但 Android 12 ART 不支持的 API 回归。

#### 本轮 AC 记录与已修问题

- `36379153867`：Leanback 编译通过；Mobile 因 `VodPlaybackHost.resetXrayForPlaybackChange()` 新增为抽象方法失败。修复为 host default no-op，使 Xray reset 仍只由 Leanback 实现。
- `36379604138`：全量 current-main debug build 成功。
- `36382398948`：包含 proxy failure recovery 的全量 build 成功。
- `36386296283`：source guards 和 Leanback 编译通过；Mobile 因 `LivePlaybackHost.resetXrayForPlaybackChange()` 同样缺少 mobile 实现失败。随后改成 default no-op。
- `36386615848`：新增 core parity guard 后因为测试字面量要求 `pins.put(identity, observed)`，而实际发布版等价实现先 lowercase 成 `normalizedObserved` 再保存而误报。已修 guard，不改生产行为。
- `36412909651`：修正 Live host 兼容后，source guards、Leanback、Mobile、assemble 与 artifact upload 全部成功。
- 成功验证后已撤掉临时 current-main push trigger，并删除 `.github/.trigger-current-main-build`；`current-main-build.yml` 恢复为纯 `workflow_dispatch`。

#### 当前剩余事项

- KCP 的 current Java → 发布版 converter → runtime config → 发布版 `testXray` 动态链已闭环，不再列为未确认项。
- 后续继续补 arm64 整链动态 parity，并以 Android TV 真机回归收口 ART/Binder/Service/播放器真实生命周期。
- 不在缺乏新证据时修改已确认一致的公共 TEST/START 流程。


### 2026-09-28 — 构建目标收敛为 Android TV / Leanback

用户确认本项目只维护 Android TV 版本。后续本 fork 的 Xray 开发、CI、测试包与验收都以 `leanback` flavor 为目标，不再为了 Xray 维护去编译 `mobile` flavor。保留 TV 的两个 ABI 输出（armeabi-v7a / arm64-v8a）；其中 `v5.6.0-xray.5` 的 **armeabi-v7a 发布 APK** 是用户亲自长期测试并确认成熟的完整 Xray 行为黄金参考。

同时进一步固定迁移原则：

- **Xray 行为目标：100% 还原 `v5.6.0-xray.5` v7 发布 APK 的 Xray 行为**，包括但不限于分享链接兼容、协议配置、连接测试、START / STOP、Binder / Service、播放代理、切换、失败恢复、资源释放、内存/线程/socket/connection pool 清理及所有已发布边界行为。
- **架构目标：不恢复旧 APK 的混合/混淆架构。** 当前独立 `:xray` 模块、清晰命名和 FongMi 5.6.3 宿主架构继续保留；旧 APK 只作为 Xray 行为与实现细节的黄金来源。
- 如果当前重构实现与旧 v7 APK 的 Xray 行为不一致，优先恢复旧 APK 行为；只有 Android/FongMi 现接口导致无法逐字实现时，才做等价映射。
- 当前 Android 12 runtime 兼容、LinkageError 隔离、generation/stale-callback 防护等不改变老包外部行为的安全改进可以保留。
- TV 网络恢复模块与 Xray 独立，不因 Xray 还原而改动。
- `current-main-build.yml` 与 `publish-current-main-test-release.yml` 已删除 Mobile javac / assemble，只构建 Android TV / Leanback；workflow 仍保持手动 `workflow_dispatch`。


### 2026-09-28 — 恢复发布版 Xray session STOP / timeout / callback 顺序

继续逐项审计 `LegacyXraySessionController` 与当前 `XraySessionController` 时，发现此前为了重入安全加入的若干保护改变了 `v5.6.0-xray.5` v7 发布版的实际 session 语义。重新对照保存的 JADX `yz3` 后确认，这不是 legacy reference 的推测。

本次恢复发布版行为：

- STOP 先把状态切到 OFF/IDLE 并通知 listener，再登记/派发 STOP；
- dispose/close 在设置 disposed 前先执行必要的 STOP；
- 旧 STOP 的 1.5 秒 cleanup timeout 若撞上新的 STARTING，会先报告 `Previous Xray session cleanup timed out`，再取消旧 STOP；新的 session 已 RUNNING 时则不再取消；
- cleanup STOP 失败即使已出现更新的 START，也按发布版先处理 cleanup failure 并取消该 STOP；
- START failure、Binder connection failure 与 startup timeout 恢复为先向 listener 发出发布版 ERROR -> OFF/IDLE 状态，再执行 disconnect/cancel；
- `fail()` 恢复发布版固定的 ERROR 后紧接 OFF/IDLE 通知，不再用重入 guard 抑制第二个状态回调。

同时重写 `SessionRaceTest`，不再把此前与发布版相反的重入保护当成正确结果；`current-main-build.yml` 与测试发布 workflow 都把 `tests/test-xray-session-races.py` 纳入 source guards。本轮仍只构建 Android TV / Leanback；为触发本次验证，current-main workflow 临时加入 main push trigger，成功后必须撤回。

本修改只恢复 session/Binder 调用边界的已确认发布语义，没有改动 KCP config、`pingBatch` URL/timeout、TEST `targetStrategy=AsIs` 或 TV network recovery。

#### 本轮验证结果

- `36416537162`：首次 push 验证因新加 core parity guard 把换行写成字面 `\\n` 而在 source guard 失败；这是测试 guard 误报，不是生产代码编译/运行失败。
- `ea96bbbd8267cbf98fc022ca4a2ab7213807b594` 修正 guard 后，Actions run `36416710086` 完整成功：source guards、Android SDK/native 输入、Libass 重建、Leanback javac、Android TV APK assemble、artifact upload 全部通过。
- 成功后已撤回 `current-main-build.yml` 的临时 `main` push trigger，workflow 恢复为纯 `workflow_dispatch`；发布 workflow 始终保持手动触发。


### 2026-09-28 — current Java → published v7 native 整链动态 parity

KCP 收口不再只依赖 recovered Go patch 或 source-level 推断。本轮新增 `tests/test-current-native-share-chain.py` 与 current-chain JVM harness，直接执行 current 的 `XrayShareLinkNormalizer`、`XrayShareLinkSecurity`、`XrayConfigFactory`，中间 converter 与最终 `testXray` 都调用固定 SHA-256 的 `v5.6.0-xray.5` armeabi-v7a `libgojni.so`（QEMU + Android API24 Bionic harness）。

测试把 current 结果逐项对比已冻结的发布版 chain oracle，覆盖 26 组链路，其中 6 组是 KCP golden cases：SRTP+seed、wechat-video+seed、VMess wireguard+seed、none/no-seed、uTP+seed、DTLS+seed；同时覆盖 WS/gRPC/HTTPUpgrade、VMess QR、HY2 authority/mport/TOFU、Trojan TOFU、SS、Reality、IPv6 与 XHTTP/SplitHTTP。证书 probe 和 pin store 是确定性的 test boundary；converter 与 runtime validation 使用的是真实发布 native。

current-main workflow 临时加入 main push trigger 以跑本轮 TV-only 验证；成功后必须撤回。publish workflow 仍保持纯手动触发。


#### 动态 chain 首轮 harness 修复

- Actions run `36418576303` 在进入实际 native parity 前失败：`prepare-native-converter-harness.py` 使用了 Python 3.11 才提供的 `hashlib.file_digest()`，而 current-main/publish workflow 固定 Python 3.10。
- 发布版 v7 `libgojni.so` 在失败前已再次通过固定 SHA-256 校验；此失败不代表 Xray/KCP 行为差异。
- harness 的 digest 改为兼容 Python 3.10 的分块 `hashlib.sha256().update()`，保持同一校验语义并避免大文件整块读入内存。


#### 动态 chain 验证完成与交接状态

- 修复 Python 3.10 harness 后，Actions run `36418844246` 完整成功。
- 动态步骤 `Verify current Xray chain against published v7 native` 成功，日志为：`PASS: current Java chain matches 26 published v7 conversion/runtime oracles; 6 KCP golden cases validated by published testXray`。
- 同一 run 的 source guards、发布版 Xray native dependency 准备、Libass 重建、Leanback javac、两个 TV ABI assemble、artifact upload 全部成功。
- KCP 最终 converted outbound / `streamSettings` / current runtime config 已由真实发布版 v7 native 与发布版 `testXray` 动态验证，不再只是 recovered Go/source-level 推断。
- 本轮成功后已撤掉 `current-main-build.yml` 的临时 `main` push trigger；current-main 与 publish workflow 均恢复为纯 `workflow_dispatch`。


### 2026-09-28 — 补齐 arm64 current-chain 动态 parity

v7 全链动态 parity 成功后，继续把相同 26 组 current Java 链扩展到 Android TV arm64 发布 native。测试仍以 v7 发布行为为唯一黄金 oracle：arm64 的 `convertShareLinksToXrayJson` 响应必须逐项等于冻结 v7 chain oracle，current `XrayConfigFactory` 生成的 runtime config 也必须逐项得到与 v7 oracle 相同的 arm64 发布版 `testXray` 结果。这样两个 TV ABI 都受同一 Xray 行为语义约束，而不是只证明各自能编译。

`CurrentNativeChain` 只接受两个固定发布 JNI SHA-256；`test-current-native-share-chain.py` 新增显式 `--abi`，QEMU harness 分别使用 ARMv7 / arm64 Android API24 Bionic。为执行本轮验证，current-main 暂时加入 main push trigger；验证完成后必须立即撤回。publish workflow 始终保持手动触发。


### 2026-09-28 — 恢复 Settings RESET_SECURITY 的发布版 Binder/UI 顺序

继续对照实际 v7 JADX `SettingXrayActivity` 时确认：删除节点并不是简单的“清存储后发 RESET_SECURITY”。发布版顺序是先占有 RESET_SECURITY operation generation，随后重建 settings Binder client，再清本地节点存储；只有本地清理成功后才清空页面 link/UDP，最后向新 client 派发 RESET_SECURITY。若本地清理或派发同步失败，Activity 会清 operation 状态并再次替换 Binder client，因此失败时不会先把可见节点输入清空。

current 已按该顺序恢复：

- `a5f540bf5b232dfd3601f3ffdf1942e460e72b6f`：`XraySettingsController.delete(Runnable)` 在 RESET_SECURITY 专用 generation 下先 `replaceClient()`，再 `preferences.clear()`，执行 UI clear callback 后派发 remote reset；异常路径 clear active generation 并再次 replace client。Leanback `SettingXrayActivity` 不再在调用 delete 前先清 UI。
- `a076e2bf4b19dceabc874477dfc093315c3a283d`：新增 deterministic `SettingsLifecycleTest`，锁住 RESET client/store/UI/dispatch 顺序、RESET 期间 Save 被阻止、phone import abandon 不发送 remote TEST cancel、45 秒 timeout 先通知再 cancel、普通 result 先通知 listener 再替换 client。
- legacy readable reference 同步修正，避免后续再依据不完整的 controller reconstruction 把该顺序改回去。
- `current-main-build.yml` 的临时 push trigger 已在 `933cdd2c328c36a53653a59780c13865a81da267` 撤回；后续 settings 提交没有制造新的自动 Actions run。

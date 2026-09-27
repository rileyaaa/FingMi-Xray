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

- FongMi/TV 5.6.3 原样代码如果已经由上游在其 `minSdk` / desugaring 构建链中使用，不做机械式“低版本改写”；例如上游本身使用的 `Math.clamp(...)`、`java.time` 等，先以对应上游源码与发布构建为兼容依据；
- 低版本兼容审计重点放在 FingMi-Xray 新增代码、从旧 APK 恢复后重新编写的代码，以及我们改动过的上游接线；
- 如果反编译 APK 显示 `j$.*` / desugared-library 调用，恢复源码必须保留等价的 desugaring 语义，不能因为“可读性”把它改成旧 ART 不存在的直接 `java.*` 调用；
- 只有确认某个调用是我们引入、且在目标 Android 运行时会真实 linkage failure 时才改代码，避免为兼容而偏离上游行为。

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
- 官方 libXray AAR 容器与当前构建使用的 Go JNI；
- 按固定输入重建的 Libass compatibility AAR。

目前 FFmpeg JNI 与 v7 / arm64 Go JNI 的字节来源仍可追溯到历史 `v5.6.0-xray.5` APK，因此 current-main workflow 会下载该历史 Release 并按固定 SHA 提取这些 native payload。**这只是二进制 provenance / reproducibility 输入，不代表当前 5.6.3 需要通过 5.6.0 faithful 行为验收。** 当未来为当前架构建立新的独立 native 发布源后，应切换构建输入并同步更新 pin。

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

当前工程主构建：

`.github/workflows/current-main-build.yml`

它负责：

1. 准备 JDK / Android SDK；
2. 下载并校验固定媒体输入；
3. 准备并校验当前固定的 FFmpeg / libXray native；
4. 重建并导入 Libass compatibility AAR；
5. 编译 Leanback / Mobile Java；
6. assemble Leanback / Mobile Debug APK；
7. 上传 APK、构建说明和 Gradle problems report artifact；Gradle 命令使用 `--warning-mode all`，让剩余 Gradle 10 弃用项在下一次手动构建中直接显示具体来源。

测试发布器：

`.github/workflows/publish-current-main-test-release.yml`

它会从触发时的当前 `main` 重新准备固定依赖、执行源码 guard、编译 Leanback / Mobile、assemble Debug APK，然后发布新的测试 Pre-release。新测试 Release 与两个 Leanback APK 都验证成功后，workflow 才删除 YAML 中指定的上一版测试 Release / tag。其他历史 Release 不在这条替换链中，也不参与当前版本的最终验收。

两个 current-main workflow 都必须先执行：

- `tests/test-xray-android-runtime-compat.py`：防止 Java 21 可编译、但旧 Android ART 运行时不存在的 API 再进入 `:xray`；
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
./gradlew --no-daemon :app:compileMobileDebugJavaWithJavac
./gradlew --no-daemon :app:assembleLeanbackDebug :app:assembleMobileDebug
```

## 8. 跟随 FongMi/TV 上游

升级上游时只以当前 `main` 和目标 FongMi/TV 上游为开发输入，不从历史 recovery faithful tree 继续开发，也不要求新实现回退到旧发布行为。

建议流程：

1. 固定目标 FongMi/TV commit；
2. 比较当前 main 与目标上游；
3. 以上游新代码为主体合并；
4. 只重新应用 FingMi-Xray 必需的 adapter；
5. `:xray` 除非模块 API 本身需要变化，否则尽量不动；
6. 重新核对 VOD / Live identity 边界；
7. 重新核对 PlayerManager、Exo / MPV、DRM、RTSP 与媒体旁路；
8. 重新核对 TV 网络 generation / DLNA；
9. 执行当前构建 workflow；
10. 再进行 Android TV 运行回归。

如果上游改变了播放器 API，优先新增小型适配层，不把上游大块代码复制进 `:xray`。

## 9. 验证清单

当前验收对象是**当前 `main` 架构**。正常发布验证不再要求 `.github/workflows/recovery-build.yml`、5.6.0 faithful APK 重建或旧 APK parity。历史 recovery 测试只在修改历史证据、来源提取脚本或需要重新核对二进制 provenance 时运行。

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

Git 历史负责记录“哪一次提交做了什么”。长期文档只描述仍然有效的结构、规则与可复核事实，不保存逐次调试流水账。

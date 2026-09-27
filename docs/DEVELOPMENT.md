# FingMi-Xray 开发与维护文档

本文是项目后续开发、模块化迁移、上游适配和工程协作的唯一主文档。

恢复发布版源码本身的事实、证据、进度和剩余门槛统一写在 [RECOVERY.md](RECOVERY.md)。长期产品目标与边界见 [PROJECT.md](PROJECT.md)。不要把同一结论同时复制到多个文档。

## 当前开发阶段

当前仍处于 **faithful recovery 优先阶段**。

现有普通工程已经包含 `:xray` Android library，`app` 也已经依赖它，但这不代表模块化迁移完成：

- 实验性 `:xray` 中已有配置、Service、Binder、session、安全和网络基础类；
- 多处实验实现已经根据恢复层静态对齐；
- 普通 app 的播放器主链路仍没有完成正式 Xray 会话和媒体网络接线；
- faithful 基准尚未完成整套 APK 构建与设备回归；
- 因此不能以实验模块代替 `recovery/legacy-src/` 的恢复真相。

正式迁移必须等恢复门达到 [PROJECT.md](PROJECT.md) 定义的阶段顺序。

## 工程边界

### `:xray`

目标职责：

- libXray bridge；
- 分享链接归一化和 runtime config；
- 证书安全和节点持久化；
- 独立 `:xray` Service；
- AIDL / Binder；
- operation generation；
- playback session 状态机；
- SOCKS HTTP / socket 资源；
- 通用公开目的地防护；
- 节点测试控制。

模块不得直接拥有：

- FongMi `VideoActivity` / `LiveActivity`；
- 上游 `PlayerManager`；
- FongMi 首页或 Spider 生命周期；
- TV 长后台 / 待机网络恢复。

### app

目标职责：

- VOD / Live 当前播放身份；
- Xray 开关和会话触发；
- 播放器切换；
- Exo / MPV 接线；
- DRM / RTSP / subtitle / danmaku / artwork / download 等媒体旁路；
- 设置 UI、手机导入 UI；
- 上游 FongMi 与 Xray facade 的最小适配。

### catvod / app network

继续负责：

- 普通 API client；
- DNS / DoH；
- Spider；
- TV 前后台 / 待机网络代际与恢复。

这条能力是项目第二核心功能，但不迁入 Xray 模块。

## 当前普通工程状态和接线差距

截至 2026-09-26，普通工程已经具备以下模块基础：

- `settings.gradle` 已包含 `:xray`；
- `app/build.gradle` 已依赖 `:xray`；
- `xray` library Manifest 声明独立 `:xray` Service；
- 普通 Leanback app 已有 Xray 设置入口。

更精确的恢复证据不要在这里重复，统一看 [RECOVERY.md](RECOVERY.md)。

### 已经接入普通工程：TV 网络恢复

以下文件当前与 faithful 对应文件逐字节一致：

- `app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java`
- `app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java`
- `app/src/main/java/com/fongmi/android/tv/model/SiteViewModel.java`
- `app/src/main/java/com/fongmi/android/tv/network/TvNetworkLifecycle.java`
- `catvod/src/main/java/com/github/catvod/net/OkDns.java`
- `catvod/src/main/java/com/github/catvod/net/OkHttp.java`

因此第二核心能力的源码接线已经进入普通工程。剩余门槛是 Android 编译和真实 TV 长后台 / 待机回归，而不是再次重写这一组文件。

### 尚未迁入普通播放器主链：Xray playback wiring

以下普通工程文件与 faithful 明显不同，当前普通版本没有对应的 Xray 播放接线：

- `PlayerManager`
- `PlayerEngineFactory`
- `ExoMediaSourceFactory`
- `ExoPlayerSession`
- `PlaybackService`
- Leanback `VideoActivity`
- Leanback `LiveActivity`

当前普通 `PlayerManager` 还没有 faithful 的 `setXrayPort` / session client 切换；普通 `ExoMediaSourceFactory` 还没有 Xray DRM DataSource 与 RTSP SOCKS 接线。

> 实验 `:xray` 模块里的网络类已经存在，不等于普通 app 已经可以按发布版语义代理媒体播放。

正式接线仍必须等待 faithful build / 回归基线过门后，按 VOD、Live、Player、DRM、RTSP、side-network 行为逐项迁移。

## 当前实验 `:xray` 模块状态

实验模块已经不是最初的空壳，多个内部实现已经根据 faithful 恢复层静态对齐，但**尚未完成正式迁移验收**。

已做过的主要静态对齐：

- playback session 的旧 STOP cleanup timeout 不再误断已经 RUNNING 的新 START；
- STOP success 后正确断 Binder；
- START success 后保留 active operation id，使后续 Binder death 仍可通知 session；
- callback generation 与 connection generation 分离；
- 旧 ServiceConnection 失败分支做解绑与 stale 过滤；
- share-link normalizer 对齐 faithful Hysteria2 / VMess / Shadowsocks 兼容行为；
- XrayService 的 validate / test bind retry、START / STOP cancel gate、daemon thread 对齐；
- certificate store 的迁移 / reset 顺序对齐；
- insecure TLS / Hysteria2 pin 比较语义对齐；
- libXray bridge 收紧到发布版 JSONObject / error 语义；
- error sanitizer 对齐发布版敏感字段和 Unicode whitespace 语义；
- preferences 读回时重新运行 share-link normalizer；
- settings import / close 改为本地 abandon / disconnect，避免误杀远端 operation；
- SOCKS public destination interceptor、HTTP resources 和 RTSP unresolved hostname 基础构件已存在。

这些改动只说明实验模块在向 faithful 靠拢，不表示：

- AIDL 已二进制兼容；
- 普通播放器主链已经接好；
- Android 编译已经通过；
- 真机 playback / Binder race 已经通过。

## Binder 协议边界

faithful 发布版 Binder descriptor：

- `com.fongmi.android.tv.xray.IXrayService`
- `com.fongmi.android.tv.xray.IXrayCallback`

当前实验模块 descriptor：

- `com.fingmi.xray.service.IXrayService`
- `com.fingmi.xray.service.IXrayCallback`

六种方法形状相同不代表 Binder descriptor 兼容。

正式迁移时优先策略：

1. 先保持 faithful operation id、timeout、generation 和回调语义；
2. 如果保留新包名，则 Service 与 client 必须同时切换；
3. 必须单独回归 Binder death、bind timeout、stale callback、旧 STOP / 新 START race；
4. 不在同一提交中既改 descriptor 又重写状态机。

## 正式模块迁移顺序

faithful 基准通过后按小步迁移：

1. **核心无 FongMi 业务依赖能力**
   - share-link normalizer；
   - config factory；
   - libXray bridge；
   - certificate / preferences；
   - error sanitizer；
   - operation / generation。

2. **Service / Binder / session**
   - XrayService；
   - AIDL；
   - service client；
   - playback session controller；
   - settings controller。

3. **通用 Xray 网络资源**
   - SOCKS OkHttp；
   - RTSP SocketFactory；
   - public destination guard。

4. **app 适配**
   - PlayerManager / engine factory；
   - Exo session / media source；
   - PlaybackService；
   - VOD；
   - Live；
   - settings / phone import UI；
   - DRM / RTSP / subtitle / danmaku / download / artwork / metadata。

5. **同一行为基准逐项回归**
   - 每迁移一块，只用 `RECOVERY.md` 已冻结的发布版行为做判断；
   - 不因为新模块 API 更漂亮而删掉 generation、timeout、private-process reset 等边界。

6. **完成一次真实 FongMi 上游升级**
   - 更新上游；
   - 只处理明确 app adapter 冲突；
   - Xray module 原则上不随 FongMi 业务文件一起大改；
   - TV network recovery 独立检查。

## 上游更新的目标形态

最终希望每次 FongMi 更新只需要处理少量适配点：

- player session / network client；
- Video / Live playback identity；
- settings entry；
- Manifest / resources；
- TV network lifecycle patch。

Xray Core、Binder、share-link、安全、session generation、SOCKS 资源应由独立模块稳定持有。


## 5.6.3 上游升级实证（2026-09-26）

- 固定起点：FongMi/TV `1a19fee278fa2234da725d61a53bf59b69fe9127`（5.6.0）；目标：`4afc4473e22a7ed3d98ee12233e0c2a490061000`（5.6.3）。catvod 是同一 FongMi/TV 仓库内模块，采用目标 commit 的对应状态，没有另行拼接独立版本。
- 上游 114 个变更路径逐文件三方合并，9 个文本冲突（PlayerManager、PlayerEngineFactory、ExoMediaSourceFactory、ExoPlayerEngine、ExoPlayerSession、PlaybackActivity、Download、mobile ConfigDialog/LinkDialog）已按目标版 API 化解。97 个路径与目标上游字节相同，17 个路径保留本项目接线。未用旧 `recovery/legacy-src/upstream` 整批覆盖。
- 目标上游带来 Libass 双字幕播放路径、播放器重建判定、新 Download 取消流程，以及 catvod Auth/Crypto/Path/Util 四文件变化。Xray 媒体工厂同时接入新版 Libass 和当前会话 HTTP/DRM/RTSP 资源；VOD/Live 弹幕走新版 `DanmakuPlayerViewController`。catvod OkHttp/OkDns 上游未改变，本项目的重建 hook 留在原处。
- 与目标上游整树对照：`:xray` 在升级提交中修改 **0** 文件；app 相对上游修改 **31** 个既有文件、增加 **6** 个文件（含 Manifest、资源、设置及网络能力，不能全算播放 adapter）；catvod 相对上游修改 **2** 个既有文件（OkHttp/OkDns），增加 **0** 文件。升级提交本身对上游新增差异集中在 17 个既有 app 路径；其余差异是升级前已存在的能力接线。TV network recovery 主要在 app 的 HomeActivity、BaseLoader、SiteViewModel、ViewModelTaskRunner 和新增 coordinator/TvNetworkLifecycle，catvod 仅 OkHttp/OkDns hook；没有复制整份上游 catvod。
- 静态门：合并的 94 个 Java 文件经 tree-sitter 解析无语法错误，15 个 XML 解析通过；关键 HTTP/DRM/RTSP、Libass、VOD/Live 弹幕和 Download 代理调用点已核对。模块的纯 JVM session identity 与 network epoch smoke，以及 reconstructed native 定向 Go regression 在各自代码提交前通过。**尚未在 5.6.3 HEAD 上完成 Gradle/Android 编译或 TV 设备回归**；当前容器无 Android SDK，GitHub 插件未提供 `workflow_dispatch`，不得把静态门写成构建通过。
- 后续编译重点：目标版新增的 Media3 Libass API/依赖、两种 ABI、Manifest/AIDL/resources，及 TV 待机后真实网络恢复。构建必须使用手动 `workflow_dispatch`，不得改 workflow 触发条件。


### 5.6.3 编译依赖门的确定阻塞

目标上游 5.6.3 新增 `androidx.media3.exoplayer.libass.*`、`SecondaryTextTrackSelector` / `SecondaryTextOutput` 等引用。固定候选 `fongmi-media3-aar-candidate-1.11.0` 的 artifact `10859533459` 下载后 SHA-256 为 `0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee`，其 `lib-exoplayer-release.aar/classes.jar` 缺少这些类；固定 `FongMi/media@3c2cbe8a` 当前公开树也没有相应源码；Libass 历史真实源码与 AAR 已找到（见下），当前 tip 缺失不代表历史不存在。上游 FongMi/TV issue #729 明确报告了相同缺失，上游回复未提供源码。故旧候选不能支持完整 5.6.3 Android 编译；不能因为三方合并语法通过就宣称升级构建成功。

临时编译桩会牺牲新版 Libass/双字幕行为，只能作为 **compile-only** 诊断，不能作为正式产品依赖或完整 5.6.3 功能验收。优先取得可核 SHA 的相应 Media3 产物或恢复可运行的实现，再做 v7/arm64 Gradle build。现有 `recovery-build.yml` 仍编译 5.6.0 faithful 源，不是 5.6.3 构建门。当前插件可读取 Actions 和产物，却没有 `workflow_dispatch` 操作；浏览器未登录私有仓库，未触发当前 HEAD 的构建。

### 稳定接线边界

`:xray` 持有播放会话、generation、service/Binder 和代理网络资源；app 播放链保留薄接线：VOD/Live 身份变更、手动开启、媒体 URL、播放器重建、媒体/DRM/RTSP 工厂以及弹幕、字幕、直播 metadata。Home/Search/Detail/普通 Spider 不因播放 Xray 改成全局代理。TV 恢复独立于 `:xray`，用 network generation 判定旧对象，在前台/屏幕/网络切换时按序重建 app、DNS/DoH 和 Spider 资源，保留 Fast Start 状态。

## 工作规则

以下规则适用于 Chat、Work、Codex 或其他后续 AI / 开发者。

### 1. 仓库当前 `main` 是工程状态真相

聊天历史、旧会话总结、模型记忆和旧文档只能作为线索。

开始工作时：

1. 先读取最新 `main`；
2. 读取本文件和对应阶段主文档；
3. 查看最近相关提交；
4. 再决定是否需要重新阅读具体代码。

如果其他 AI 已经推进工程，不得用旧上下文覆盖新结果。

### 2. 修改后立即落库，不积压

无论改动发生在本地容器、Codex、Work、GitHub API 或其他环境：

> **确定的代码或工程改动完成后，应尽快提交 / 上传到 `main`，随后立即更新对应主文档。**

推荐原子流程：

1. 核实证据或需求；
2. 修改一个清晰问题范围；
3. 运行该范围必要的静态 / 单元检查；
4. 提交代码或工程文件；
5. 更新 `RECOVERY.md` 或 `DEVELOPMENT.md`；
6. 提交文档；
7. 再开始下一项。

不要长期保留只存在于临时容器或聊天上下文中的“已完成工作”。

目的：

- 防止会话中断后丢失状态；
- 防止新 AI 重复阅读和重新推理已经解决的问题；
- 防止不同 AI 同时工作时互相覆盖；
- 让 Git 历史和主文档能够直接接手。

### 3. 不要批量积压几十个修改后一次上传

大型批量修改会：

- 增加冲突；
- 降低证据可追踪性；
- 让会话中断恢复困难；
- 让下一位接手者难以判断每项变化的依据。

可以在同一提交中修改强相关的少量文件，但每个提交应有明确单一目的。

### 4. 文档不是流水账

主文档记录：

- 当前有效结论；
- 结论依据；
- 已验证范围；
- 未验证范围；
- 当前阻塞；
- 下一步。

主文档**不记录**：

- “先看了 A，再看了 B”；
- 没产生结论的搜索过程；
- 每几分钟一次的时间线；
- 已经被后续结论覆盖的中间猜测；
- 同一事实在多个文档里的重复副本。

Git commit history 已经承担时间线职责。

### 5. 一个事实只维护一个主要位置

- 产品目标 / 长期边界 → `PROJECT.md`
- 发布版恢复事实 / 证据 / 门槛 → `RECOVERY.md`
- 开发 / 模块迁移 / 上游适配 / 工程工作规则 → `DEVELOPMENT.md`
- 原始发布产品说明 → `ORIGINAL_README.md`
- 可复核的反编译材料 → `apk-reference/`

必要时可以链接，不要复制整段。

### 6. 恢复阶段先修 faithful，再修实验模块

如果发现发布 APK 与 `recovery/legacy-src/` 有确证偏差：

1. 先修 faithful 层；
2. 在 `RECOVERY.md` 写清证据和验证级别；
3. faithful 结论稳定后，才评估是否同步实验 `:xray`；
4. 实验模块的差异写在本文件，不反过来定义发布版行为。

### 7. 不把静态验证写成运行验证

文档必须区分：

- 源码静态比较；
- DEX 指令确认；
- JVM / Python 单元测试；
- Gradle 编译；
- APK 构建；
- Android TV 真机测试。

例如：

- “54 个精选方法签名匹配”不能写成“播放器 AAR 完全兼容”；
- “workflow 配置完成”不能写成“依赖已经恢复”；
- “JADX 步骤成功”不能写成“整个 Action run 成功”；
- “编译成功”不能写成“发布版行为一致”。

### 8. 按实际成果汇报，不设固定工作窗口

项目所有者于 2026-09-26 更新授权：不再设置固定二十分钟窗口，也不要求每工作 20–23 分钟强制收尾。此规则替代旧会话中的时间限制。

在当前会话与工具能力允许的范围内持续推进；出现确定的新发现、实际提交、测试结果或阻塞变化时简短汇报，到有实际阶段成果时总结。不声称回复结束后还会继续后台工作。

## GitHub Actions / AC 规则

项目所有者于 2026-09-26 更新授权，本节替代此前的“默认不运行”“10 次免询问额度”和 faithful build 逐次授权规则。

### 当前恢复授权

- 恢复工作需要的 GitHub Actions / AC 可以直接执行，无需逐次询问，也不设置免询问次数上限；
- 不再维护或遵守旧的 10 次额度 / 剩余额度；
- 授权包括分析、依赖准备、测试、faithful APK 编译，以及有明确原因的失败修复和重跑；
- 仍应合理复用固定发布材料、可信已有产物、缓存和本地能力，但不能为了节省 AC 无限重复静态阅读而不进入实际验证；
- 自动发布正式版本、改变产品目标不在本授权范围内。

### 必须保持手动触发

恢复、构建和分析 workflow 必须保持 `workflow_dispatch`。授权的是主动调用手动执行入口，不是改为 `push`、`pull_request`、`schedule` 或其他自动触发。

缺少 dispatch 能力时，应寻找当前环境支持的正常执行途径；确实无法执行就准确记录工具限制并继续其他可执行工作，不通过更改触发方式绕过。

### 修改、执行与验证结果分开记录

- 提交 workflow 修改不等于执行过 workflow；
- YAML 校验通过不等于实际依赖恢复成功；
- 历史 run 成功不等于当前 HEAD 已通过；
- 每次实际执行记录对应 HEAD、关键 run、输入哈希和结果，不再记录授权次数；
- 失败修复或重跑应说明实际原因，不反复无依据重试。

### Faithful APK build

整套 faithful APK 编译在恢复阶段属于明确里程碑，已经包含在上述授权内，不再另行要求项目所有者允许。

运行前应：

1. 核对当前静态门、依赖门和实际输入哈希；
2. 明确本次编译验证的范围与仍未验证的范围；
3. 运行对应的手动 workflow 或匹配环境中的本地构建；
4. 分开记录依赖生成、测试执行、APK 编译和真机回归结果。

## Git 规则

- 只维护 `main`，除非项目所有者以后明确改变策略；
- 不依赖未提交的本地 scratch 作为持久状态；
- 不提交原始发布 APK、DEX、AAR、SO 等大型二进制到普通 Git 历史；
- 大型发布材料以固定 SHA-256、来源和可重新获取方式记录；
- 与本项目恢复直接相关的反编译文本证据放入 `docs/apk-reference/`。

## 文档维护规则

新增或更新代码后：

- 恢复 / faithful 相关 → 更新 `RECOVERY.md`；
- 模块开发 / 普通 app / 重构 / 上游升级 → 更新 `DEVELOPMENT.md`；
- 产品目标发生变化 → 更新 `PROJECT.md`；
- 不因为每次小工作建立新的 `*_AUDIT_YYYY-MM-DD.md` 或 `SESSION_*.md`。

当旧专项文档内容已完整吸收进主文档后，应删除旧文件，不保留只写“已迁移”的空壳。

## 接手顺序

### 继续恢复

1. 根 `README.md`
2. `docs/PROJECT.md`
3. `docs/RECOVERY.md`
4. 最近相关提交
5. 需要处理的具体源码 / reference

### 继续重构或普通开发

1. 根 `README.md`
2. `docs/PROJECT.md`
3. `docs/DEVELOPMENT.md`
4. 如涉及发布版行为，再查 `docs/RECOVERY.md`
5. 最近相关提交和具体代码

目标是让接手者**不需要重新完整阅读整个仓库才能知道已经做过什么**；只有在要修改某个具体范围时，才深入读取对应代码。

### 真实 Libass 历史产物

已下载并验证 FongMi/media run `31571172760` / artifact `9131565941`（`9dae39e9689ee305c83f94bd11cf3bcecb9d6171`）：ZIP SHA-256 `8cc91dae9c7d6770033bfe72e505b9455136c3f85e77d9ddec1f844335afa0d8`，内部 AAR `3b2326d98e1339f3ca4d1763e3a3028de20a5dd62cc738875af51b6329fe2571`。`scripts/import-libass-aar.py` 校验并接入 app/libs，真实 Java 与 v7/arm64 `libmedia3ass.so` 均在，非禁用桩；二进制不进入 Git。对应原始源码在该 commit 的 `libraries/exoplayer_libass/`。
`javap` 证实这份早期 AAR 的 PlaybackSession 使用 String/String/String/(boolean) 构造器，缺少 5.6.3 所需 LibassConfiguration、LibassSubtitleController、SecondaryText 和 UI controller，不能把导入等同完整兼容。已查两公开 branch 和该历史 commit 的 SecondaryText 文件历史、历史 tree、Actions 产物列表，尚无真实 SecondaryText implementation；后续重建必须同时处理新版 Libass 控制层接口。

### SecondaryText 选择与输出恢复

新增 app 内 `androidx.media3.exoplayer.trackselection.SecondaryTextTrackSelector` / `text.SecondaryTextOutput`，标记 **reconstructed upstream-missing implementation**。装饰真实 Decode/DefaultTrackSelector，保留 renderer 索引和主音视频策略，最后一个 text renderer 独立消费第二条流；支持手动/自动语言、重复/不支持轨抑制、独立 active selection、preload 实例隔离、reset/release 与迟到 cue generation。不是 no-op 或 compile-only stub。
`scripts/test-secondary-text.py --candidate <固定候选ZIP> --maven <mvn>` 对真实 Media3 1.11.0 AAR 编译，通过 8 个 Robolectric SDK28 测试（0 failure/skip），覆盖实际 DefaultTrackSelector、双流 Tracks 状态及输出生命周期。这里只验证选择/输出能力；5.6.3 的新 LibassConfiguration/SubtitleController/UI controller 尚未完整接入，不能宣称完整 Android build 或 ASS 双字幕端到端通过。

官方 5.6.3 release 当前不可取得；邻近 5.6.5 发布 APK 的目标 DEX 类 `m63/k63/l63` 补充了真实证据，SHA 与复核命令在 `recovery/media-tests/published-secondary-565.json`。fallback 指令确认：保留 delegate 已选 stream；禁止两个 renderer 消费同一 TrackGroup（即使 track 不同）；active info 必须属于当前 selector。已据此修正并通过 8 测试；未将项目升级到 5.6.5，也不把邻版字节码当成 5.6.3 原始源码。

### 播放会话 operation / 通知重入竞态

真实 `XraySessionController` 的确定性 JVM 驱动先复现 4 个失败：旧 STOP failure/timeout 取消新 START，START 通知内 stop 后仍派发旧 START，STOP 通知内重启后旧 STOP 才派发。现由 operation ID 限定旧 cleanup 所有权；STOP 先派发再通知，START 通知后重查有效性；失败先清理 transport 再通知，close 先封闭生命周期，避免同步回调复活旧请求。
`scripts/test-xray-session-races.py` 通过 9 场景，额外覆盖 Binder failure/启动 timeout 的重入 retry、迟到 START、有效 timeout、close。只替换 Android 主队列/配置/Binder 边界，实际 controller 直接参与测试，无 sleep。VOD/Live 共用此 module 修复；没有新增 Activity boolean 或改 faithful frozen reference。该闭环不等于 Activity resolver、DRM、RTSP、metadata 所有异步路径已全量验证。

### 新版 Libass JNI 边界（2026-09-27）

- 邻版官方5.6.5 v7/arm64 APK/SO与DEX SHA保存在 `recovery/libass-tests/published-565-contract.json`；按ELF真实JNINativeMethod表恢复17个签名，两ABI一致。不是5.6.3 exact original source。
- `recovery/media3-libass` 开始承载 `reconstructed upstream-missing implementation`，当前仅Native绑定及Frame/Image值对象；Image ctor新增textureId，Create改为library handle，render/fontScale/frameSize/style等签名与历史AAR不同。尚未装入app，不把旧SO包装成兼容。
- `check-libass-contract.py --source --v7-so … --v8-so …` 实际编译Java并核对17签名/2构造器；`--aar`可拒绝Java/native不配套的候选产物，但不等于完整Libass API/渲染认证。
- `test-published-libass-jni.py --workdir native-harness --jni …` 使用fake JNI函数表、现有QEMU/API24真执行发布v7 JNI_OnLoad与library/track/cache/release；通过。无ART/字幕图像输出声明。
- 待恢复：Configuration/session/controller、parser/extractor、双字幕与preload ownership、native渲染/失败清理及候选AAR集成。已定位邻版 sk1(session)、libass.b(media)、c(library)、g(track)；下一步沿这些对象所有权收口。

### Libass library/track 所有权（2026-09-27）

- 从5.6.5 `libass.c/g/b` 与 `bl1` 恢复共享字体library、隔离track、timed-data SHA256/length/time去重及初始化失败回收；native静态确认library没有引用计数，必须先关闭tracks。证据与重建时加强的同步规则见 `recovery/libass-tests/ownership-evidence.json`。
- 新 `LibassNativeLibrary/LibassTrack` 集中在重建边界，真实调用新版JNI；统一owner锁防止create/process/render与parent close交叉，失败清理/重复close/重入不会返回已释放track。JVM instrumented JNI仅在测试目录，不打入产物。
- `test-libass-native-ownership.py` 8个确定性用例通过；发布v7真执行额外覆盖null library错误、null release、UTF获取失败后的资源清理路径及同library后续成功创建。两ABI签名门继续通过。
- 尚未恢复完整native渲染参数语义、MediaState/session/controller/preload集成及新版AAR；本阶段不宣称完整Libass可用或5.6.3已编译。

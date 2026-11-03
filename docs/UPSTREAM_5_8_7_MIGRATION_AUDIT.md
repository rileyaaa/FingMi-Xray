# FingMi-Xray 5.8.7 升级失败复盘、源码缺口与回退保留项

> 整理日期：2026-11-03。**这是 2026-11-02 至 2026-11-03 的升级试验复盘，不是 5.8.7 构建成功报告。**
>
> 本项目现在维持可追溯的 **FongMi/TV 5.6.3 / FingMi-Xray `v5.6.3-xray.1`**。2026-11-02 起准备的 5.8.7 升级**从未合入远端 `main`、未生成正式双 ABI APK、未发布 5.8.7 Release**。Git 历史中仍保留原试验提交，不进行强制改写；只将当前工作树回到已验证的 5.6.3 基线，同时保留独立的手动 AC 升级工作流与辅助工具。

## 一、回退范围与原版本完整性：先区分 APK 和源码

- **代码回退参照**：`a2f193b40e427ef97a49fc3638c24320ed6b52d2`（2026-10-26，正式 .1 发布完成后、简化手动构建/发布入口并停止源码 ZIP 备份后的状态）。这个提交的应用、Xray、TV recovery 运行源码与发布构建源码 `4bea3a54ece68fbb439374e7d7944ec94fe28683` 一致，差异仅在后续发布/维护基础设施。不能误把 5.8.7 生成器开发提交当成曾发布的 APK 源码。
- **现存 5.6.3 的 APK 是完整的签名安装包，不是只包含空壳或缺播放器的残包**。2026-10-26 Actions [#40252299406](https://github.com/rileyaaa/FingMi-Xray/actions/runs/40252299406) 已通过 18 AAR 播放器/native 重建、Libass、播放器启动、Xray parity、Leanback Java 编译、双 ABI APK assemble、MPEG-H/native 最终装包、Media3 DEX 链接、Manifest、签名与 16KB 对齐检查。其最终红色失败发生在**编译结束以后**：工作流 token 创建 Git tag 遭 `HTTP 403 Resource not accessible by integration`。随后用已验证的草稿资产完成受权续发；不是因构建不出 APK。
- **正式版双 ABI 对应记录**（`v5.6.3-xray.1` / `563001`）：`armeabi-v7a` 117,801,063 bytes，SHA-256 `64fdc38928f96185e924444e9c4ca33c582021e732df4b7e041daa4321615424`；`arm64-v8a` 133,283,631 bytes，SHA-256 `004cd5e003a644a7e421a859cd7a7187e98e729bea94af157127dd3d20609bd5`。GitHub Release 资产摘要与原 CI 日志一致。保留黄金参考 `v5.6.0-xray.5`，不修改两份现行正式 APK、标签、签名或版本。
- **证据界限**：上述结论证明产物为通过工程检验的完整 APK，**不等于**已做当前电视安装、所有视频格式/解码器、节点连接和长期待机的真机逐项验证；更**不等于**所依赖的每个 native/AAR 都拥有无需历史二进制输入的完整公开源码。安装包完整性与整个软件栈的公开可重建性是两个不同问题。
- **曾被误认的版本**：本轮升级目标是 **FongMi/TV 5.8.7**，不是 5.8.3；试验使用的目标源码曾固定为 `FongMi/TV@305dff233cde512e2c83f71529b7c3ecfd61fefc`。

## 二、确认的决定性阻断：5.8.7 的 Media3/播放器源码不配套

- 上游 5.8.7 应用公开源码引用大量定制 `androidx.media3.*` API，但本项目固定且可见的播放器源码 `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`（`release-1.11.0-fongmi`）**至少缺少 44 类对应的公开顶级 Java/Kotlin 源文件**。首批 javac 限制 100 条错误，最初只观察到约 30 个缺失名字；独立 Git Tree 比对后扩大到至少 44 个。类型例子包括 `DecoderMode`、`DiscMenuController`、`SubtitleOffsets`、`IsoDiscPreparation`、`LibassPlaybackSession`、`BdjRuntime`、`MpvDrmSupport`、`DanmakuPlayerViewController`。
- **不只是缺 class**：已存在的 `DefaultRenderersFactory`、`PlayerView`、`Player`、`MpvPlayer` 也缺新 TV 调用的播放器方法；例如 `setDecoderManager()`、`setEnableSurfaceControlFrameRetention()`、`setBackendPlayer()`、`getSubtitleOffsets()` 等。即使临时补 44 个空类也不能得到功能、ABI 与语义上正确的播放器。
- 已核查 `FongMi/media` 公开 `release` 分支、当时可见的 pull refs、部分第三方 fork，均未找到能够满足当前 5.8.7 契约的一整套源码；`FongMi/Release` 提供新版 APK，但不等于提供配套可编译 Media3 源码/AAR。公开 [FongMi/TV issue #764](https://github.com/FongMi/TV/issues/764) 也独立提到约 45 项媒体类型未公开；它针对当时上游状态，数量不应和本次固定提交的 44 个精确等同。
- **实际打到编译阶段的证据**：[Actions #41606382989](https://github.com/rileyaaa/FingMi-Xray/actions/runs/41606382989)，`main@07a721723b356fd31e3d108d6ca866f55730b789`、`build_without_publish=true`。候选同步、源 guard、原生输入重建、Xray/native parity、Libass 与播放器启动等步骤成功；首次实际执行 `:app:compileLeanbackReleaseJavaWithJavac` 时因上述 Media3 类型/方法不匹配失败，**没有得到双 ABI APK**。这不是 Xray 启用后某个视频“解码失败”的运行时案例，而是构建依赖缺失的**编译期**阻断。
- **已做的防重试修补**：`scripts/upstream/check_media3_source_contract.py` 将已确定的不兼容媒体 pin 与 44 个已知缺失 import 关联，提前在 SDK、native、Gradle 前 fail-closed。此脚本仅检测已证实的不兼容组合，不是自动发现完整兼容版本的万能验证器。
- **不采用的“修复”**：从新官方 APK 反编译拼接业务播放器源码、创建不带实现的空壳 class、删官方特性以强行编译、用旧版 Media3 AAR 冒充 5.8.7 播放器，均不能满足本项目的“仅维护 Xray/TV 网络恢复，其他业务跟随公开上游”的边界。

## 三、升级过程中的已踩坑、原因与解决方法

### 2026-11-02 上游 5.8.7 与通用一键升级 Actions

1. **升级代码不是原地 `ours/theirs` 覆盖**：5.6.3 到 5.8.7 公共树约有 810 个变更路径，曾整理本 fork 相对旧公共源码约 61 个偏差路径及其 `generate/upstream/rebase/project` 策略。实际候选同步报告约有 768 个计划修改、42 个保护/排除项；这只是工作树准备，不代表 768 个文件已通过 Android 编译。保留 `scripts/upstream/fork_scope.json`、`sync.py`、`prepare_release.py`，遇未登记偏差、未知 API、实质三方冲突一律拒绝。
2. **官方功能变了，旧二开接线失效**：`SiteViewModel.cancelResultRequest()` 改为 `TaskType.RESULT` 的限定取消；Spider 由旧版清理接口改成异步 `BaseLoader/SpiderLoader`，必须等待完成后再进入 TV 恢复；HTTP/DoH 重建、Glide 失败缓存清理和请求代际需按新版 API 生成薄 adapter，不能把 5.6.3 的普通业务实现覆盖到 5.8.7。
3. **Xray 不能只代理主视频 URL**：Live/VOD 页面更替、引擎切换、播放 Service owner、DRM/RTSP/字幕/弹幕/EPG/XMLTV/下载/远端 artwork 都涉及同一会话网络身份。使用上游源码上的最小接口生成器，以及 Xray-only data-source/side-request gate；代理切换时先取消旧代请求，普通直连行为不被改变。新版 `DanmakuApi/SubtitleApi` 已换成 `ApiCallback`、请求 ID 等机制，旧 5.6.3 JVM 假实现不可直接当成 5.8.7 真接口测试。
4. **不能拿预检绿色当编译成功**：[Actions #41573448653](https://github.com/rileyaaa/FingMi-Xray/actions/runs/41573448653) 的真实上游预检通过（8/8 组、候选 13/13 项），但当时 `apply_to_main=false`，**没有编译 APK、推送 main 或发布**。此后完整构建才发现编译器层面的大缺口。
5. **纯工程/工作流错误多次浪费 AC**：输入 SHA 复制有前后空格或 tab；Python 测试生成 `__pycache__` 污染“工作树必须纯净”检查；Bash/YAML 转义或续行写错在真正工作时才露出；从 `APPLY_TO_MAIN` 拆成 `BUILD_CANDIDATE` 后旧测试还检查旧标记。已增加 SHA 规范化、关闭 Python bytecode、全部 shell 块 `bash -n`、相应模式契约与隔离 Bash/JVM 回归；遵守**先做离线静态/单测，后触发一次昂贵 AC**。
6. **Git staged diff 的空白规则与官方 vendored JS 冲突**：第八、九次运行停在官方 `estree-L5DZKXBH.js` / `spider-editor.js` / `spider-format/chunk-RBBTUEK2.js` / `spider-format/dist-SPW7IUL4.js` 等资源的尾随空白。第九次 [#41596021792](https://github.com/rileyaaa/FingMi-Xray/actions/runs/41596021792) 依旧未开始 Gradle。解决方法是**仅对四个固定官方路径**用 `.gitattributes` 例外，并以选定公共上游 Git Blob 对比原始字节；不能全局关闭 `git diff --check`，更不能豁免自有 Java/Python。
7. **只显示第一个错误导致连续重跑**：将 8 组公开 API adapter、14 个候选 guard、正式模式 28 项完整 source guard 改为**尽量全部执行、收集所有独立失败后统一阻断**；失败就不重建 native、不签名、不更新 main。要区分 JVM fixture/mock 成功与真编译/真机运行。
8. **5.6.3 发布阶段的 403 是另一类坑**：旧编译日志末尾的 tag 发布权限不足发生在成功装包之后；可以利用原始 digest 和受权续发，无需因“Actions 红色”误判安装包损坏、更不能拿这一结果证明 5.8.7 能编译。

### 2026-11-02 5.8.7 官方 Exo 接线适配（候选生成器，未发布）

- 旧版 Exo/MPV/ISO、字幕、DecoderManager、播放器 UI 内部架构不能直接搬到新版；`exo_adapters.py`、`player_manager_adapter.py`、`side_request_adapters.py` 等脚本的目标是对**选中的真实官方树**按精确 anchor 生成 Xray 接线，失败就停止。
- 原有 5.6.3 播放器兼容源、历史 Libass native 回收、18 AAR 重建能在旧工程通过，但不能因此证明 5.8.7 的新 API/ABI 可复用。完整的媒体源码签名、类/方法、依赖与 native 一致性必须先解决。
- 局部虚拟机/离线夹具测试提供防回归价值；**不能替代**真实 5.8.7 javac 和最终 APK 的 DEX/资源/native 检验。

### 2026-11-02 Xray 播放器接线解耦（5.8.7 迁移第一阶段）

- 试验期间将 Xray-only scheme 守卫、直连/代理引擎身份与网络绑定策略抽成 `XrayGuardedPlaybackDataSource`、`XrayPlaybackRouting` 等代码。为保证 **5.6.3 回退时运行代码零漂移**，这些尚未正式验收的 Java 实现不留在现在的 `app/` 编译树；参考源码放在 `scripts/upstream/reference/`，供未来**候选生成阶段**按需迁入，而不是现在加载。
- 新版候选还需要替换 5.6.3 专属测试断言、重写官方恢复源 SHA 表，并完成 5.8.7 与媒体源码的所有接口检查。切勿因为保留了生成器、模板和历史测试，就把 AC 解释成“已修复所有问题，可以开正式发布”。

## 四、保留哪些 AC 资产，回退掉哪些东西

- **恢复旧版**：`app/` 的五处后期改动（两份新增 Xray 工具 Java 与三份 Player/Exo 改动）全部回到 `a2f193b` 的原始运行树；三份已有 5.6.3 专用构建/发布/失败续发 YAML 和原本生产、测试代码回到同一基准。已有 Releases/tag **一律不动**。
- **专项保留**：`.github/workflows/manual-upstream-sync.yml`；完整 `scripts/upstream/`（`baseline.json`、`fork_scope.json`、适配器、预检、模板），`scripts/build/resolve-release-tag.py`，仅升级用途的新 `tests/test-upstream-*.py` 与相关新增测试，以及四个官方 JS 例外的 `.gitattributes`、避免污染 checkout 的 `.gitignore`。因此 AC 前期开发资产没有仅剩一个找不到被调用脚本的 YAML 空壳。
- **按 5.6.3 原样恢复**：`docs/AI_COLLABORATION.md`、`docs/PROJECT.md`、`docs/RECOVERY.md`、`README.md`、`docs/ORIGINAL_README.md` 不重写历史；`docs/DEVELOPMENT.md` 只在已发布 5.6.3 记录**之后追加一段指向本复盘**。旧日志不是新版本发布证明。本复盘替代试验阶段不断叠加且过时的短报告。
- **旧版测试仅改必要一处**：`tests/test-build-hygiene.py` 允许额外的**手动** `manual-upstream-sync.yml`，同时继续拒绝 push/schedule/marker 自动触发。不得通过广泛放宽既有 5.6.3 运行 guard 来迎合尚未编译的 5.8.7 候选。
- **保留不等于可立即升级**：回退后现存 AC 仍是**冻结的试验引擎**；部分候选守卫和生成后版本专用测试需在发现完整公开媒体源码时重新核对和移植到候选树。保留原工作流与历史 Git 提交是为了减少重写，不是假装已经通过回退状态下的完整 AC/5.8.7 编译测试。

## 五、今后正确的操作门槛

- 四个 Actions YAML **只能通过 `workflow_dispatch` 手动启动**，不得恢复定时器、push marker、跨 workflow 自动链。保留的 `manual-upstream-sync.yml` 提供互斥模式：
  - `apply_to_main=false` 且 `build_without_publish=false`：默认**预览**，候选校验，不编译/不发布。
  - `apply_to_main=false` 且 `build_without_publish=true`：构建并校验双 ABI APK，只保存短期私有 Artifact，**不会推送 main/发布 Release**。
  - `apply_to_main=true` 且 `build_without_publish=false`：所有检查通过后**将候选推送 main 并正式发布**；目前**禁止**作为排障按钮使用。
  - 同时为 `true`：预期拒绝。
- 再谈 5.8.7 或后继升级之前，先确认**可追溯、许可允许、公开可获取、与选定 TV 源码真实匹配**的 Media3/player class、方法、AAR/native 构建输入；使用源码 API 预检把缺口尽量前置，避免重跑同一必败 workflow。
- 找到来源后，先在不更新 `main` 的候选中恢复并验证版本专用测试、生成器与 helper class；离线全部通过后仅执行 **`build_without_publish=true`** 的手动完整构建。必须取得且独立核验两 ABI、固定签名、版本、DEX、native、Manifest、16KB alignment 和 Xray/TV recovery 预期行为，真机测试通过以后再考虑明确授权的正式发布。
- 一直保留现行 `v5.6.3-xray.1` 和 `v5.6.0-xray.5`，不能通过清理旧 Release、重打包旧 APK 或改标签来掩盖升级失败。

**最终判断**：5.6.3 已发布 APK 是有完整播放器/native 装包与验证记录的成品；5.8.7 失败的根因是新版 TV 的**公开 Media3 播放器源码/接口未完整配套**，而非 5.6.3 已发布 APK 没有解码器。

## 六、2026-11-03 通用打包入口恢复与手动 AC 复核

回退后再次检查发现，旧的正常打包入口**并没有丢失**：`current-main-build.yml` 和 `publish-current-main-test-release.yml` 始终存在；`resume-verified-release.yml` 负责已通过装包验证却在发布阶段失败的续发。早前从历史删除的五个 `recovery-*.yml` 属于 5.6.0 研究重建/证据收集流程（其中 `recovery-build.yml` 依赖临时 native artifact），**不等于**用于现行正式 APK 的普通打包工作流，因此不盲目恢复这五个过时入口。

本轮确实找回了回退时一并失去的**通用版本打包支持**：两个构建/发布入口不再把失败报告与成功 APK artifact 名称限定在 5.6.3，正式发布读取当前 `app/build.gradle` / `scripts/upstream/baseline.json` 推出正确 Release tag，发布说明不会对将来的上游版本误写“没有升级”。续发脚本匹配通用报告名，源码/版本匹配守卫相应调整，且仍保持原固定签名、两 ABI 交付及 release replacement 显式授权。四个 Actions YAML 都继续仅支持**手动 `workflow_dispatch`**，没有新增 push、schedule 或自动串联。

这只是恢复了 CI 基础设施，不代表在本次恢复后的源码运行过新的 GitHub Actions 或真机测试；`v5.6.3-xray.1` 保持 2026-10-26 已验证的历史产物，5.8.7 依旧因公开播放器 Media3 源码缺失被阻断，不能据此推断可以完整编译或需要反编译官方 APK。

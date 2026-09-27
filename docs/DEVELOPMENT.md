# FingMi-Xray 开发与维护

本文是当前 main、模块化 Xray、5.6.3 上游适配、构建验证和工程协作的唯一主文档。

v5.6.0 发布版 faithful 事实只维护在 [RECOVERY.md](RECOVERY.md)；长期产品边界只维护在 [PROJECT.md](PROJECT.md)。

## 1. 当前工程基线

当前 main 已从固定 FongMi/TV 5.6.0 基线升级到 FongMi/TV 5.6.3：

- 5.6.0 基线 commit：1a19fee278fa2234da725d61a53bf59b69fe9127
- 5.6.3 目标 commit：4afc4473e22a7ed3d98ee12233e0c2a490061000
- 上游升级主提交：2916f06d777ca34c3e7344db891c06ad078dc674

当前 main 不是“原版 5.6.0 faithful 源码目录的直接继续开发”，而是升级后的普通工程。faithful 5.6.0 仍由 recovery/legacy-src 独立维护。

## 2. 当前架构已经接到什么程度

### :xray

当前 app 已依赖独立 :xray Android library。模块持有：

- libXray bridge；
- config / share-link / certificate；
- Service / Binder；
- generation / operation；
- XrayPlaybackSession / XraySessionController；
- SOCKS HTTP / SocketFactory；
- public destination guard；
- 设置控制。

当前模块已经进入真实普通工程，不再是最初的空壳。

### 播放链

当前 Leanback VideoActivity 和 LiveActivity 已直接创建 XrayPlaybackSession。

现有接线包括：

- VOD / Live playback identity；
- 用户手动开启 / 关闭；
- 切集、切台、换地址等 identity 变化；
- PlayerManager 的 playback proxy 切换；
- ExoPlayerSession 的 proxy 注入；
- ExoMediaSourceFactory 的媒体 / DRM / RTSP 网络适配；
- Live EPG / XML metadata 跟随当前 Xray client；
- artwork / logo 的网络身份处理。

因此旧文档中“普通播放器主链尚未接 Xray”的描述已经失效。

但这仍不等于“正式模块迁移完成”。原因是：

- 当前模块 Binder descriptor 与 v5.6.0 faithful descriptor 不同；
- 当前模块实现经历过重构和上游适配，仍需用 faithful 行为基准做真机回归；
- 当前 5.6.3 只完成 compile / assemble，没有完成 Xray / DRM / RTSP / Binder race 的 TV 运行验收。

### TV 网络恢复

TV 网络恢复继续留在 app / catvod，不迁入 :xray。

当前普通工程已经保留：

- Home 生命周期接入；
- BaseLoader / SiteViewModel 的代际失效；
- TvNetworkLifecycle / coordinator；
- OkHttp / OkDns 重建 hook；
- Leanback DLNA renderer 生命周期。

为避免 mobile flavor 引用 Leanback-only DLNARendererService，当前通过 flavor-specific TvDlnaLifecycle 隔离：

- Leanback 实际 start / stop renderer；
- Mobile 为 no-op。

这项修改只解决 flavor 编译边界，不改变 mobile 运行语义。

## 3. 5.6.3 上游合并

升级时对目标上游变更做逐文件三方合并：

- 目标上游共有 114 个相关变更路径；
- 9 个文本冲突被按 5.6.3 API 化解；
- 97 个路径最终与目标上游字节一致；
- 17 个路径保留项目适配；
- :xray 在上游升级提交中修改 0 个文件。

主要冲突集中在：

- PlayerManager；
- PlayerEngineFactory；
- ExoMediaSourceFactory；
- ExoPlayerEngine；
- ExoPlayerSession；
- PlaybackActivity；
- Download；
- mobile ConfigDialog / LinkDialog。

上游带来的播放器变化包括 Libass 双字幕、播放器重建判定和 Download 取消流程。项目适配同时保留当前会话 Xray 网络资源与 TV 网络恢复。

该次升级证明 :xray 能在较新的上游下保持相对稳定，但它还不是 PROJECT.md 所定义的最终模块化验收，因为 faithful 5.6.0 的真机基准尚未闭环。

## 4. 5.6.3 媒体兼容层

### Libass

固定 player candidate：

- artifact：10859533459
- SHA-256：0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee

该候选缺少 5.6.3 app 所需的新 Libass / SecondaryText API，因此不能直接完成 5.6.3 构建。

当前工程使用可重复重建的 Libass compatibility candidate：

- Libass candidate SHA-256：2318eb904a016d0160aed2a4b7de8501578cd0f223c65e5c61086f7a9a80f573
- extractor compatibility AAR SHA-256：feb8be30e3d431391ce4b3b165a6cbfb18313969d7ba7da2d6ccfeb96d25ee68
- media3-container 1.11.0 被固定作为缺失依赖；
- 新版 JNI 使用相邻发布版已验证的 v7 / arm64 SO；
- 源码、class、JNI、AAR 输入均有固定哈希和 contract gate。

已经重建并测试的范围包括：

- Libass native loader；
- library / track 所有权；
- primary / secondary frame；
- media / preload 状态；
- parser / extractor；
- playback session / clock；
- subtitle controller；
- PlayerView / EGL 所有权；
- GLES 组合与失败清理；
- Matroska attachment / ASS timing。

这些测试包含 JVM / Robolectric、QEMU/JNI 和 headless rendering 等多种证据，但仍不等于 Android TV 实际 EGL / GPU / 字幕显示验收。

### app 侧缺失适配

真实 Gradle 编译进一步暴露并修正：

- LibassFontFile；
- DanmakuPlayerViewController。

这两个类是 5.6.3 app 对 Media3 / FongMi 扩展 API 的适配边界，不用 compile-only stub 替代真实调用。

### MPV

5.6.3 app 使用的部分 secondary subtitle / font API 新于固定 MPV AAR。

当前 MpvPlayerEngine / MpvUtil 通过固定 AAR 已有能力做兼容映射，包括：

- MpvSubtitleOptions.Builder.setSecondarySubtitle；
- MPV config string option；
- 本地 secondary selection 状态。

这是一层兼容桥，不代表缺失的更新版 MPV 二进制已经被逐字节恢复。

### 其他编译边界

本轮 5.6.3 构建还修正了：

- QuickJS crypto 集成；
- Chaquo ABI packaging；
- Libass extractor / candidate pin；
- flavor-specific DLNA 生命周期。

这些结论已经落到当前 main，不再按每个 commit 另写时间线。

## 5. 当前 5.6.3 构建基准

GitHub Actions run 36301217767：

- 源码 commit：7e2111a2d14b04e034eae3cf83c456659586a799
- JDK：21
- Android SDK：37
- Gradle：9.7.1
- Leanback / Mobile Java 编译通过；
- Leanback / Mobile Debug assemble 通过。

产物 SHA-256：

| 产物 | SHA-256 |
| --- | --- |
| Leanback armeabi-v7a | 409415aeced5428f2ea0df0df7cfe6f807a2918494a68ba2fc61b62c9081d3a3 |
| Leanback arm64-v8a | 949e19a65f1d4006fae9f181d359afa72806337a389bb5d8167d0a0dc1ca2f8c |
| Mobile armeabi-v7a | 7daec34e1c6cbcf35cd7bbaaaf2eaa13866bd0101c4f598a842336610ed8e9f6 |
| Mobile arm64-v8a | 9be80c47032b23c872f4b8beaca9d557bde3fe05b19d6d2ea03940050f0f60e8 |

Actions artifact：

- id：10925572471
- name：fingmi-xray-5.6.3-current-main-debug
- digest：sha256:9702b6ee9230fd839e9fc025a02eebc5e4822a39b0449d292d87ecc02d4be2d0

这组结果证明的是当前 main Debug compile / assemble。它不证明：

- 正式 release signing；
- v5.6.0 faithful 行为一致；
- Android TV Xray 播放运行正确；
- Libass 真机 EGL / GPU 输出正确；
- MPV secondary subtitle 兼容映射在真机完整通过；
- TV 长后台恢复已经在真实设备验证。

## 6. 测试发布

仓库已准备 .github/workflows/publish-current-main-test-release.yml。

该 workflow：

- 只允许 workflow_dispatch；
- 固定使用 run 36301217767 和 artifact 10925572471；
- 先核成功 run、artifact digest 和 Leanback APK SHA；
- 只上传 Android TV / Leanback 的 v7 与 arm64；
- 目标 tag 为 v5.6.3-xray.test.1；
- 创建 Pre-release；
- 不替换正式 Latest v5.6.0-xray.5；
- 不重新编译 APK。

截至本文整理时，该 Pre-release 尚未实际创建。执行后应以 Releases 页面实际状态为准，并在状态变化时更新本节，而不是保留“准备发布”的旧描述。

## 7. 当前运行验证重点

当前 5.6.3 main 下一阶段重点是真机，而不是继续增加静态门。

Android TV 至少应覆盖：

- 安装 / 启动；
- 节点保存、测试、手机导入；
- VOD 手动开启 / 关闭 Xray；
- Live 手动开启 / 关闭 Xray；
- 切集、自动下一集、切频道、换源、换线路；
- 换播放器；
- HTTP / HTTPS；
- DRM；
- RTSP / RTSPT；
- subtitle / danmaku；
- Libass primary / secondary 字幕；
- MPV secondary subtitle / font；
- EPG / XML metadata；
- Xray 启动失败后的直连恢复；
- Binder / Service 异常；
- 长后台、待机、SCREEN_ON/OFF 与网络恢复；
- DLNA renderer 生命周期。

发现行为与 v5.6.0 faithful 基准冲突时，先判断是上游变化、兼容层问题还是模块化偏差，不直接用 current main 反向修改 faithful 事实。

## 8. GitHub Actions 规则

仓库所有可执行 workflow 都必须保持纯手动 workflow_dispatch。

当前 workflow：

| Workflow | 用途 |
| --- | --- |
| current-main-build.yml | 构建当前 5.6.3 main |
| publish-current-main-test-release.yml | 发布固定 5.6.3 TV 测试 Pre-release |
| recovery-apk-analysis.yml | 分析正式 APK |
| recovery-player-aars.yml | 构建固定 FongMi Media3 候选 AAR |
| recovery-restore-ffmpegjni.yml | 准备 faithful native dependencies |
| recovery-build.yml | 构建 v5.6.0 faithful TV APK |
| recovery-upstream-snapshot.yml | 获取固定 5.6.0 上游快照 |

不得保留：

- push；
- pull_request；
- schedule；
- workflow_call；
- 其他会因为代码提交或外部事件自动运行的触发器。

手动执行 workflow 已获得项目所有者授权，但“workflow 文件存在”“YAML 正确”“历史 run 成功”都不等于当前 HEAD 已实际运行。

## 9. 工程工作规则

### main 是当前工程真相

开始工作时：

1. 读取最新 main；
2. 读取与任务对应的主文档；
3. 查看最近相关 commits；
4. 再进入具体代码和测试。

旧聊天、旧总结和模型记忆只作为线索，不能覆盖仓库新状态。

### 小步提交

确定的代码修改应及时落到 main。每个提交保持单一目的，避免几十个无关变化一次堆积。

### 区分验证级别

必须明确区分：

- 源码静态比较；
- DEX / ELF 证据；
- JVM / Python / Robolectric 测试；
- Gradle Java 编译；
- APK assemble；
- Android TV 真机运行。

低级别证据不能被写成更高级别验收。

### 文档不是提交日志

Git 历史负责回答“什么时候改了什么”。

主文档只回答：

- 现在是什么状态；
- 为什么可以这么判断；
- 哪个证据可以复核；
- 哪些范围还没有验证；
- 下一步是什么。

文档职责固定为：

- PROJECT.md：长期目标与边界；
- RECOVERY.md：v5.6.0 faithful；
- DEVELOPMENT.md：当前工程与开发；
- apk-reference/：反编译证据；
- ORIGINAL_README.md：冻结的原发布说明。

同一个详细事实只在一个主文档维护，其余位置只保留必要摘要和链接。

## 10. 接手顺序

继续 v5.6.0 恢复：

1. README.md
2. docs/PROJECT.md
3. docs/RECOVERY.md
4. 最近相关 commits
5. 具体恢复源码 / evidence

继续当前 main、模块化或 5.6.3 开发：

1. README.md
2. docs/PROJECT.md
3. docs/DEVELOPMENT.md
4. 涉及发布行为时再查 docs/RECOVERY.md
5. 最近相关 commits
6. 具体源码

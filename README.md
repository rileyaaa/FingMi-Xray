# FingMi-Xray

FingMi-Xray 是基于 FongMi/TV 的 Android TV 二次开发项目。项目长期保留两项能力：按当前播放会话启用 Xray，以及电视长后台 / 待机后的网络恢复。

当前仓库同时维护两条互不替代的验证线：

- 发布版恢复线：恢复并验证已发布的 v5.6.0-xray.5；
- 当前开发线：维护已经升级到 FongMi/TV 5.6.3 的 main，并继续验证模块化 Xray、播放器和电视网络恢复。

两条线可以并行推进，但 current main 能编译并不代表 v5.6.0 faithful 恢复已经验收；同样，faithful 恢复完成也不自动证明 5.6.3 的真机运行没有回退。

## 当前状态

### v5.6.0-xray.5 发布版恢复

已经完成的核心工作包括：

- 固定两份正式 APK、FongMi/TV 5.6.0 上游和 libXray 版本；
- 保存与恢复直接相关的 APK / JADX / DEX 文本证据；
- 恢复 Xray Service、Binder、会话生命周期、播放器接线、设置、安全、手机导入和 TV 网络恢复的主要 faithful 源码；
- 恢复并校验发布版 FFmpeg JNI 和 libXray Go JNI；
- 建立固定来源、固定哈希的播放器 AAR 与 native 依赖门；
- 对发布版 libXray 的分享链接转换、API v2、证书探测、age、生命周期和多项边界行为建立可重复验证证据。

尚未完成：

- 手动生成受来源约束的云端 faithful native dependency artifact；
- 完成独立的 v5.6.0 faithful Gradle 构建；
- 完成 Android TV v7 真机回归；
- 完成 v8 构建 / ABI 最终验收。

详细状态只维护在 [docs/RECOVERY.md](docs/RECOVERY.md)。

### 当前 5.6.3 main

当前 main 已完成 FongMi/TV 5.6.3 合并，并保留 Xray 播放会话接线与 TV 网络恢复。

GitHub Actions run 36301217767 已通过：

- Leanback Debug Java 编译；
- Mobile Debug Java 编译；
- Leanback v7 / arm64 APK assemble；
- Mobile v7 / arm64 APK assemble。

这证明当前工程构建链已经闭环，但仍未完成 Android TV 真机运行验收。

仓库已准备手动测试发布工作流 Publish 5.6.3 test pre-release，用于把已验证构建的 Leanback v7 / arm64 APK 发布为 Pre-release。它不会替换当前正式 Latest v5.6.0-xray.5。

当前工程、上游适配和构建记录只维护在 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。

## 文档分工

| 文档 | 唯一职责 |
| --- | --- |
| [docs/PROJECT.md](docs/PROJECT.md) | 长期产品目标、架构边界、验收原则 |
| [docs/ORIGINAL_README.md](docs/ORIGINAL_README.md) | 冻结的 v5.6.0-xray.5 原始发布说明，不随开发改写 |
| [docs/RECOVERY.md](docs/RECOVERY.md) | v5.6.0 faithful 恢复事实、证据、依赖、构建门和回归门 |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | 当前 main、模块化、5.6.3 上游适配、工程规则和运行验证 |
| [docs/apk-reference/README.md](docs/apk-reference/README.md) | 发布 APK 反编译证据索引 |

Git 提交历史负责时间线。主文档只保留当前有效结论，不按提交顺序重复记录过程。

## GitHub Actions

仓库中的所有可执行 workflow 都只允许手动 workflow_dispatch。不会因 push、pull_request、schedule 或 workflow_call 自动触发。

需要执行恢复、构建、分析或测试发布时，由维护者在 Actions 页面明确选择对应 workflow。

## 许可证

第三方项目分别遵循其自身许可证。仓库许可证见 [LICENSE.md](LICENSE.md)。

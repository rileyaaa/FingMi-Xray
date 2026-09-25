# FingMi-Xray 项目交接

开始恢复/重构前，先读 `docs/recovery/WORKLOG.md` 的当前状态、最新进展和未解决问题；产品意图、历史修复、阶段进度分别读 `PROJECT_REQUIREMENTS.md`、`DEBUG_HISTORY.md` 和 `PROGRESS.md`。做完一轮同步更新相关文档，包括提交号、证据、验证范围和下一步。详细 APK 对照见 `docs/recovery/README_APK_BEHAVIOR_MATRIX.md`、`LEGACY_BEHAVIOR_FREEZE.md` 和 `DEEP_AUDIT_2026-09-25.md`。

项目是丢失源码后的 `v5.6.0-xray.5` 恢复；产品核心优先级：Xray 第一，部分电视长期后台/待机后网络恢复第二。先依据发布 APK、原始 `README.md` 核对 `recovery/legacy-src/` 的忠实层，再考虑把 Xray 从 FongMi 主程序拆出以便跟进上游。当前 `xray/` 模块还没有完成忠实迁移。用户要求静态恢复充分核验后再编译整套 APK；缺失播放器 AAR 可提前用 AC 编译。优先本地。两次免询问 AC 运行已用完；用户随后明确指示继续用 AC 编译 AAR，第三轮已成功。再运行 AC 应先确认目的与授权，勿靠修改工作流意外触发。只维护 `main`。

每次 Work 或 Chat 会话修改工程后，同步更新 `WORKLOG.md` 并上传到仓库 `main`；需求变化更新 `PROJECT_REQUIREMENTS.md`，排错/修复更新 `DEBUG_HISTORY.md`，阶段变化更新 `PROGRESS.md`，写清证据、实际验证范围、剩余工作及 AC 消耗。

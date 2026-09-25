# FingMi-Xray 项目交接

开始恢复/重构前，先读 `docs/recovery/WORKLOG.md` 的当前状态、最新进展和未解决问题；做完一轮后更新该日志，包括提交号、证据、验证范围和下一步。详细 APK 对照见 `docs/recovery/README_APK_BEHAVIOR_MATRIX.md`、`LEGACY_BEHAVIOR_FREEZE.md` 和 `DEEP_AUDIT_2026-09-25.md`。

项目是丢失源码后的 `v5.6.0-xray.5` 恢复；先依据发布 APK、原始 `README.md` 核对 `recovery/legacy-src/` 的忠实层，再考虑把 Xray 从 FongMi 主程序拆出以便跟进上游。当前 `xray/` 模块还没有完成忠实迁移。用户要求静态恢复充分核验后再编译；优先本地。Actions 的两次免询问机会及实际消耗记在工作日志中。只维护 `main`。

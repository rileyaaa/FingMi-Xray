# Recovery

`recovery/` 只保存已发布旧版本的恢复源码、固定历史行为证据和可重复复核材料。它是**历史归档区，不是当前版本的开发或发布验收基线**。

- `legacy-src/`：`v5.6.0-xray.5` faithful 可读恢复源码与固定上游 overlay。
- `legacy-tests/`：faithful 恢复工具和源码测试。
- `libxray/`：发布版 libXray / Go JNI 的可读行为重建。
- `native-tests/`：发布 JNI 的固定 native fixture 与 harness 输入。
- `node-dns-tests/`：固定 Xray-core DNS / IPv6 dial 行为验证。
- `v2rayn-tests/`：旧发布版分享链接兼容证据。

当前 5.6.3+ 直接参与构建的 Media3 / Libass 兼容代码已经迁到 `compat/`；当前源码回归入口位于 `tests/`。正常 current-main 发布不要求运行 faithful build 或把当前行为重新对齐到 `v5.6.0-xray.5`。

运行 workflow 时可能临时创建 `recovery/work/` 与 `recovery/evidence/`；两者都已由 `.gitignore` 排除，不属于仓库中的恢复源码或固定 fixture。

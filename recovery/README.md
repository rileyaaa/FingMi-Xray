# Recovery

`recovery/` 只保存已发布版本的恢复源码、固定历史行为证据和可重复验证材料。

- `legacy-src/`：`v5.6.0-xray.5` faithful 可读恢复源码与固定上游 overlay。
- `legacy-tests/`：faithful 恢复工具和源码测试。
- `libxray/`：发布版 libXray / Go JNI 的可读行为重建。
- `native-tests/`：发布 JNI 的固定 native fixture 与 harness 输入。
- `node-dns-tests/`：固定 Xray-core DNS / IPv6 dial 行为验证。
- `v2rayn-tests/`：分享链接兼容基准。

当前 5.6.3 直接参与构建的 Media3 / Libass 兼容代码已经迁到 `compat/`；当前源码回归入口位于 `tests/`。

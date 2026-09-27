# Tests

这里保存当前源码的独立回归测试入口和 test doubles。

- `test-*.py`：当前 compatibility、Xray native 行为和 session 回归入口。
- `xray-session/`：当前 `:xray` 会话控制的 JVM test doubles。

发布版恢复源码和固定历史行为 fixture 仍保留在 `recovery/`；当前媒体兼容实现及其专用测试位于 `compat/`。

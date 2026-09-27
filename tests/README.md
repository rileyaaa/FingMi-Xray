# Tests

这里保存当前源码的独立回归测试入口和 test doubles。**从 5.6.3 重构线起，这里的 current-main 测试、Gradle 构建与设备回归属于现行验收矩阵。**

- `test-*.py`：当前 compatibility、Xray native 行为和 session 回归入口。
- `test-xray-android-runtime-compat.py`：阻止旧 Android ART 不具备的 Java runtime API 和缺失 JNI keep rule 进入当前 Xray 路径。
- `test-upstream-update-disabled.py`：阻止 FongMi 上游自更新调用和 APK 安装权限重新进入当前 fork。
- `test-build-hygiene.py`：守住 XLIFF、format string、Android ABI API 和 GitHub Actions runtime 的构建告警卫生。
- `xray-session/`：当前 `:xray` 会话控制的 JVM test doubles。

旧发布版恢复源码和固定历史行为 fixture 仍保留在 `recovery/`，但不属于正常 current-main 发布的必跑验收项；当前媒体兼容实现及其专用测试位于 `compat/`。

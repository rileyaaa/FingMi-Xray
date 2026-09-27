# Compatibility

这里保存当前 `main` 构建仍然直接使用的兼容层源码与验证材料。

- `media3-libass/src/`：Media3 / Libass compatibility 实现。
- `media3-libass/patches/`：固定 Media3 extractor / subtitle 行为所需 patch。
- `media3-libass/tests/`：Libass compatibility 契约、JNI 与媒体状态测试 fixture。
- `media3-libass/media-tests/`：SecondaryText 等当前播放器兼容测试。

这里的内容属于当前 5.6.3+ `main` 的构建 / 验证输入，并随当前架构继续维护。当前 compatibility 行为以 current-main 测试为准，不以旧 `v5.6.0-xray.5` faithful parity 作为发布条件。

# v5.6.0-xray.5 历史发布版恢复档案

本文记录 `v5.6.0-xray.5` 的**历史证据对象、证据来源、faithful 源码结构、二进制来源和可重复恢复方法**。

> **归档定位**：从 5.6.3 重构线开始，本文件不再定义当前 FingMi-Xray 的开发、功能回归或发布验收基线。当前 `main` 及其最新测试 / 正式构建才是现行基线。这里的 5.6.0 材料只用于历史取证、解释旧发布行为，以及追溯当前仍复用的部分 native 字节来源。

它不是开发日志，也不记录当前 main 的上游升级过程。当前工程见 [DEVELOPMENT.md](DEVELOPMENT.md)，原发布时的用户说明见 [ORIGINAL_README.md](ORIGINAL_README.md)。

## 1. 历史恢复对象

恢复对象固定为：

- FingMi-Xray：`v5.6.0-xray.5`
- FongMi/TV：`5.6.0`
- faithful `versionCode`：`56005`
- libXray / Xray-core：`v26.7.28`

正式 APK：

| ABI | 文件 | SHA-256 |
| --- | --- | --- |
| armeabi-v7a | `FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk` | `cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda` |
| arm64-v8a | `FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk` | `b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d` |

固定 FongMi/TV 上游：

- commit：`1a19fee278fa2234da725d61a53bf59b69fe9127`

固定官方 libXray：

- tag：`v26.7.28`
- commit：`80263da83e96b2972455b0a94b13ee1a10e51391`
- Android ZIP SHA-256：`28b7dc9d6cc8455fcca5cbd56e387003a7bfb558128651a64899dc3a8ccff666`
- 官方 `libXray.aar` SHA-256：`4708a361a74f7e955635dbe3661cefb459bdc867423c3b1826a2c5a6ea4ac77d`

本归档中关于旧发布版的 faithful 结论都以这些固定输入为前提；这些固定输入不会自动成为当前 main 的行为或验收标准。

## 2. 证据优先级

恢复目标是“尽可能忠实地解释并重现已发布 APK”，不是把反编译代码润色成更合理的新实现。

出现冲突时按以下顺序处理：

1. 已固定 SHA-256 的正式 APK；
2. APK 中的 DEX / ELF / JNI 实际行为；
3. 冻结的原发布说明；
4. 固定的 FongMi/TV 5.6.0 上游；
5. JADX 等反编译文本；
6. 可读恢复实现和重建实验。

JADX 中出现不可能分支、R8 合并控制流或自相矛盾时，必须继续查 DEX、双 ABI 或发布 native 的实际运行结果。

可直接进 Git 的反编译证据索引见 [apk-reference/README.md](apk-reference/README.md)。

## 3. faithful 源码结构

发布版可读恢复源码集中在 `recovery/legacy-src/`：

- `upstream/`：在固定 FongMi 5.6.0 上游之上的发布版覆盖；
- `com/fongmi/android/tv/xray/`：发布版 Xray Service；
- `com/fongmi/android/tv/xray/legacy/`：可读的会话、网络、设置与安全 helper；
- `aidl/`：发布版 Binder contract；
- `recovery/legacy-tests/`：faithful 源码与恢复工具测试。

`scripts/recovery/prepare-legacy-faithful.sh` 负责从固定上游组装临时 faithful tree，避免把完整上游副本永久复制进仓库。

faithful 源码的职责是解释发布版行为；当前 `:xray` 模块则是面向后续维护的重构实现，两者不能混为一套源码。

## 4. 历史发布版行为记录

### Service 与会话

以下内容只描述 `v5.6.0-xray.5` 当时的发布行为，用于历史复核；当前模块化实现以当前 `main` 为准。

发布版使用独立 `:xray` 私有进程。

关键语义包括：

- VOD 与 Live 各自维护播放 Xray 会话；
- operation id 与 generation 用于过滤旧异步结果；
- Service bind timeout 约 5 秒；
- playback start timeout 为 30 秒；
- previous STOP cleanup timeout 为 1500 ms；
- settings test / security reset timeout 为 45 秒；
- Binder death、binding died、null binding 与 disconnect 都有明确收口；
- 旧 STOP 或旧 callback 不能破坏更新的 START；
- 无法可信清理的 Service 路径会结束私有 Xray 进程。

发布 Binder descriptor：

- `com.fongmi.android.tv.xray.IXrayService`
- `com.fongmi.android.tv.xray.IXrayCallback`

当前模块化 `:xray` 使用新的包名，因此方法形状相近不代表 Binder 二进制兼容。

### 播放网络

发布版的 Xray 是当前播放身份的网络资源，不是全局状态：

- 新集、新频道、新源、新地址和新播放器默认直连；
- 启用 Xray 的播放使用独立 SOCKS HTTP 资源；
- SOCKS hostname 以 unresolved address 交给代理侧解析；
- Xray 播放不复用普通直连 cache / preload 身份；
- RTSP / RTSPT 使用 SOCKS SocketFactory；
- DRM license 跟随当前 Xray DataSource；
- 本机、私网和保留目标受 destination guard 保护；
- 会话结束后关闭 Dispatcher、ConnectionPool、executor 与相关代理资源。

### VOD / Live 身份

VOD 的会话边界包括切集、自动下一集、换线路、换源、实际播放地址变化、真正换播放器、播放结束和离开页面。

Live 的会话边界包括切频道、换线路 / 源、直播配置变化和播放器变化。

直播解析过程中允许等待 Xray START；Xray 启动失败不能破坏原本可用的直连播放。EPG、XML metadata、logo / artwork 等旁路也需要遵守当前播放网络身份。

### 分享链接、设置与安全

主要输入格式：

- VLESS
- VMess
- Trojan
- Shadowsocks
- Hysteria2 / hy2

恢复证据覆盖的兼容边界包括：

- legacy SS；
- SIP003 `v2ray-plugin`；
- VMess JSON port；
- HY2 默认端口、multi-port、`pinSHA256`、obfs；
- IPv6 authority；
- URI / credential 编码；
- KCP、gRPC、Reality、XHTTP 等参数。

设置与安全语义包括：

- 分享链接使用 Android Keystore AES-GCM；
- preference：`xray_secure`；
- key alias：`fongmi_xray_share_link_v1`；
- 节点测试使用独立 operation，不留下 playback session；
- 删除节点时同步清理对应 security state；
- 手机导入复用 FongMi 局域网页面；
- 非默认 TLS / HY2 信任通过首次 pin 与后续变更拒绝实现；
- 错误展示前会隐藏链接、UUID、密码、token、secret、key、short id、seed 等敏感内容。

### Android TV 网络恢复

发布版同时包含与 Xray 无关的 TV 网络恢复逻辑：

- Activity 与 SCREEN_ON / SCREEN_OFF 推进网络代际；
- Home 在重新回到前台时判断是否需要恢复；
- 普通 API client、DNS / DoH 与 Spider 环境可以重建；
- 旧业务请求会被取消，避免晚到结果覆盖新页面；
- 网络稳定检查以约 500 ms 周期进行；
- 连续两次具备 Internet capability 后继续；
- 最多约 12 次检查后继续刷新；
- DLNA 生命周期随电视前后台 / screen 状态收口。

这一能力在重构后仍属于 `:app` / `:catvod`，不属于 `:xray`。

## 5. 播放器与 FFmpeg JNI

固定 Media3 player candidate 来源：

- FongMi/media commit：`3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`
- candidate ZIP SHA-256：`0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee`

与发布 APK 对照时，相关播放器 native 中唯一明确需要从发布 APK 恢复的是 `libffmpegJNI.so`。

发布版 FFmpeg JNI：

| ABI | SHA-256 |
| --- | --- |
| armeabi-v7a | `3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42` |
| arm64-v8a | `26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c` |

恢复后的 decoder AAR 固定 SHA-256：

`31a1db2570416147cc6889643d25345477977205d60a61a6df525ffa5a623a13`

恢复脚本只替换 v7 / arm64 两个 `libffmpegJNI.so`，其余 ZIP entry 保持候选 AAR 内容。

相关工具：

- `scripts/recovery/restore-published-ffmpegjni.py`
- `scripts/recovery/check-player-ffmpegjni-against-published.py`
- `scripts/recovery/check-player-java-api.py`

## 6. libXray / Go JNI

正式 APK 中的 Go JNI：

| ABI | SHA-256 |
| --- | --- |
| armeabi-v7a | `6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e` |
| arm64-v8a | `40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece` |

发布二进制与官方 `v26.7.28` 并不完全相同。发布 native 已确认包含项目所需的扩展行为，例如：

- Invoke API version 2；
- `test` / `run` 内联 `xrayJson`；
- `pingBatch` item 内联 `xrayJson`；
- TLS certificate probe；
- HY2 certificate probe；
- age subscription / key generation；
- legacy SS、HY2 multi-port / pin、ALPN / port、legacy KCP 等转换兼容。

历史恢复得到的 `libXray.aar` SHA-256：

`f531a138e82fa08848e47cf22537c69df29227b07eba7d19c2ad3740af657365`

它以官方 AAR 为容器，只替换正式 APK 中的 v7 / arm64 `libgojni.so`；Java API、x86 / x86_64 JNI 和其他 entry 保留官方内容。

相关工具：

- `scripts/recovery/fetch-libxray.sh`
- `scripts/recovery/restore-published-libxrayjni.py`
- `scripts/recovery/check-libxray-gojni.py`

## 7. native 可读重建

仓库还保存了依据正式发布 native 行为重建的可读补丁：

- `recovery/libxray/share-converter-recovery.patch`
- `recovery/libxray/native-v2-recovery.patch`
- `recovery/libxray/native-age-errors.patch`

它们用于解释、测试和继续研究发布行为，**不是找回的原始 Go 源码**。

对应证据与测试主要在：

- `recovery/native-tests/`
- `recovery/v2rayn-tests/`
- `recovery/node-dns-tests/`
- `tests/test-recovered-libxray.py`
- `tests/test-native-abi-parity.py`
- `tests/test-native-share-chain.py`
- `tests/test-v2rayn-share-chain.py`
- `tests/test-v2rayn-reference-chain.py`

发布 JNI 已建立 converter、API v2、lifecycle、TLS / HY2 probe、age、v2rayN-shaped 输入、IPv6 / DNS dial 等定向执行证据。历史 faithful 重建使用发布 JNI 字节，不用这些可读重建产物冒充原始二进制。当前 main 可以继续复用经固定 SHA 校验的 native 字节作为构建输入，但不再以 faithful APK 是否可重建作为发布验收条件。

## 8. 归档 faithful 构建工具（非当前验收链）

这一节保留的是历史重建工具。它们只在需要复核旧发布版、重新提取历史 native 来源或研究旧行为时使用；正常 current-main 开发和发布**不要求执行本节流程**。

本地入口：

`scripts/recovery/build-legacy-faithful.sh`

它负责：

1. 校验 player AAR 调用面；
2. 校验 FFmpeg JNI；
3. 校验 libXray Go JNI；
4. 从固定 FongMi 5.6.0 上游组装 faithful overlay；
5. 调用 Gradle 构建 Leanback faithful APK。

GitHub Actions 对应两段手动流程：

### 归档：Archive - prepare v5.6.0 native evidence

文件：

`.github/workflows/recovery-restore-ffmpegjni.yml`

职责：

- 固定正式 Release APK；
- 固定 player candidate；
- 从发布 APK 恢复 FFmpeg JNI；
- 获取官方 libXray；
- 从发布 APK恢复 Go JNI；
- 输出 `fingmi-faithful-native-dependencies` artifact。

### 归档：Archive - v5.6.0 faithful TV reconstruction

文件：

`.github/workflows/recovery-build.yml`

输入：

- 上一步经过验证的 native dependency artifact ID。

职责：

- 再次验证 artifact 来源；
- 导入固定 player / native 依赖；
- 组装固定 5.6.0 faithful tree；
- 执行 faithful Gradle 构建。

这些 workflow 只允许手动 `workflow_dispatch`，并视为历史归档工具。它们的成功或失败不再决定当前 5.6.3+ 架构能否发布；current-main 的构建、源码 guard、当前回归与 Android 运行测试才决定当前版本验收。

## 9. 历史证据复核原则

需要复核历史恢复材料时，必须区分：

- 反编译文本一致；
- DEX / ELF / JNI 证据；
- JVM / Python / Go 测试；
- Gradle 编译；
- APK assemble；
- Android TV 真机运行。

较低级别证据只能证明对应层级，不能替代更高层级验证。

如果未来出现新的历史 APK 证据改变既有结论，应先修改 recovery 代码和对应历史测试，再更新本文。反过来，当前重构实现也不需要为了满足旧 faithful parity 而回退；当前产品行为和发布验收以当前 `main`、当前测试与当前设备回归为准。

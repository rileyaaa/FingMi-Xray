# FingMi-Xray

FingMi-Xray 是基于 [FongMi/TV](https://github.com/FongMi/TV) 的 Android TV 二次开发项目。

项目主要面向一种很具体的播放场景：**影视接口、节目单和播放地址本身可以正常获取，但部分港澳台、海外或跨境媒体线路在当前网络环境下直连质量较差。**

FingMi-Xray 将 Xray 集成到播放器内部。遇到这类内容时，可以只为**当前正在播放的媒体会话**临时启用 Xray，而不需要给整台电视建立系统 VPN，也不要求路由器长期运行代理。

## 项目版本

当前 `main` 基于 FongMi/TV 5.6.3。**从 5.6.3 重构线开始，当前 `main` 以及由它构建出的最新 FingMi-Xray 测试版 / 正式版，是唯一的开发与验收基线。** `v5.6.0-xray.5` 只保留为历史发布证据和当前部分 native 二进制的来源记录，不再要求以 faithful 重建、旧 APK 行为对照或旧版本 cloud build 作为当前版本的最终验收条件。

主要组件版本如下：

| 组件 | 当前版本 / 基线 |
| --- | --- |
| FongMi/TV | **5.6.3**（commit `4afc4473e22a7ed3d98ee12233e0c2a490061000`） |
| FongMi/media / Media3 fork | **1.11.0**（commit `3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`） |
| Media3 container | **1.11.0** |
| libXray AAR | **v26.7.28** |
| Xray-core | **v26.7.28** |
| QuickJS wrapper | **3.2.3** |
| Chaquopy Gradle Plugin | **17.0.0** |
| Python runtime | **3.10** |
| OkHttp | **5.5.0** |
| AndroidX Media | **1.8.0** |
| AndroidX Leanback | **1.2.0** |
| AndroidX AppCompat | **1.8.0** |
| AndroidX Lifecycle Service | **2.11.0** |
| AndroidX RecyclerView | **1.4.0** |
| Room | **2.8.4** |
| Glide | **5.0.9** |
| Material Components | **1.14.0** |

当前播放器 AAR 统一来自固定的 FongMi/media 1.11.0 候选。MPV、FFmpeg 等 native 组件没有在当前工程中维护独立、可直接声明的 semver，因此不另外虚构版本号；当前构建规则见 [DEVELOPMENT.md](docs/DEVELOPMENT.md)，历史二进制来源证据见 [RECOVERY.md](docs/RECOVERY.md)。历史来源不等于当前验收基线。

### 构建环境

| 项目 | 版本 |
| --- | --- |
| Java | **21** |
| Gradle | **9.7.1** |
| Android Gradle Plugin | **9.3.1** |
| compileSdk | **37** |
| targetSdk | **37** |
| minSdk | **24** |
| Android SDK Platform（CI） | **37.0** |
| Android Build Tools（CI） | **37.0.0** |
| desugar_jdk_libs_nio | **2.1.5** |

<details>
<summary>其他 Gradle 依赖版本</summary>

| 依赖 | 版本 |
| --- | --- |
| AndroidX Annotation | 1.10.0 |
| AndroidX Biometric | 1.1.0 |
| AndroidX Palette | 1.0.0 |
| AndroidX Preference | 1.2.1 |
| AndroidX SplashScreen | 1.2.0 |
| AndroidX Startup | 1.2.0 |
| AndroidX SwipeRefreshLayout | 1.2.0 |
| AndroidX ViewPager2 | 1.1.0 |
| android-gif-drawable | 1.2.32 |
| AndroidAutoSize | 1.2.1 |
| Brotli | 0.1.2 |
| Apache Commons Compress | 1.28.0 |
| CustomActivityOnCrash | 2.4.0 |
| Flexbox | 3.0.0 |
| EventBus | 3.3.1 |
| Gson | 2.14.0 |
| Guava | 33.7.1-android |
| JNA | 5.19.1 |
| juniversalchardet | 1.0.3 |
| Logger | 2.2.0 |
| Lottie | 6.7.1 |
| MaterialDesignColors | 1.0.0 |
| NanoHTTPD | 2.3.1 |
| NewPipeExtractor | v0.26.5 |
| PermissionX | 1.8.1 |
| RTMP Client | v3.2.0.m2 |
| Sardine Android | 0.9 |
| Simple XML | 2.7.1 |
| SMBJ | 0.15.0 |
| TextDrawable | 1.0.3 |
| ZXing Android Embedded | 4.3.0 |
| ZXing Core | 3.5.4 |
| JUnit（test） | 4.13.2 |

</details>

## 核心设计

- **默认直连**：首页、搜索、详情、普通接口等仍使用 FongMi 原有网络。
- **按需开启**：只有用户在当前播放中手动开启 Xray，当前媒体连接才进入 Xray。
- **会话隔离**：切集、切频道、换源、换地址或换播放器后，新播放默认重新直连。
- **非全局代理**：不使用 Android `VpnService`，不接管其他应用或整台设备的网络。
- **独立进程**：Xray Core 运行在应用自己的 `:xray` 私有进程中，会话结束后收口相关网络与运行资源。
- **电视网络恢复**：另外保留针对部分 Android TV 长后台、待机或 Fast Start 后旧连接失效的网络恢复逻辑；这项能力与 Xray 播放代理彼此独立。
- **旧 Android 运行时兼容**：虽然源码使用 Java 21 编译，Xray 路径仍按 Android 12 / SDK 32 等旧 ART 的实际 API 能力约束，并由源码 guard 阻止 `StringBuilder.isEmpty()`、较新的 URL codec overload、`String.isBlank()` 等运行时不兼容调用重新进入关键路径。
- **不使用上游自更新**：Home 不自动检查 FongMi/Release，设置页版本号只显示信息，`Updater` 为 no-op，应用也不申请 `REQUEST_INSTALL_PACKAGES`，避免用户升级时被上游 APK 覆盖当前 Xray fork。

实际使用原则很简单：**直连正常就直接播放；直连卡顿时再尝试 Xray；开启后不适合当前线路就关闭。**

## Xray 节点

设置页支持保存和测试 Xray 分享链接，也可以在同一局域网内通过手机向电视导入较长的分享链接。

主要兼容：

- VLESS
- VMess
- Trojan
- Shadowsocks
- Hysteria2 / hy2

兼容目标以常见单节点分享格式为主。不同客户端生成的非标准链接可能存在差异。

## 重构后的结构

早期版本的 Xray 逻辑与 FongMi 播放代码耦合较深。源码恢复后，仓库重新整理了职责边界：

- `:xray`：Xray 配置、Service / Binder、会话控制、SOCKS 网络资源与安全逻辑；
- `:libxray`：Android 侧 `libXray.aar` 依赖入口；
- `:app`：FongMi 的 VOD / Live 播放身份、播放器与 UI 接线；
- `:catvod`：普通业务网络、DNS / DoH 与 Spider；
- `compat/`：当前 5.6.3 构建仍需维护的媒体兼容源码与补丁；
- `recovery/`：历史发布版恢复、反编译验证、native / 节点兼容行为证据归档；这些材料不再作为当前版本验收基线；
- `tests/`：当前源码回归测试入口与测试 fixture。

这样做的目的，是让项目自己的能力尽量集中在稳定边界内，减少后续跟随 FongMi/TV 上游升级时的侵入式修改。

## 文档

- [PROJECT.md](docs/PROJECT.md)：项目设计、职责边界与长期架构约束。
- [DEVELOPMENT.md](docs/DEVELOPMENT.md)：当前源码结构、构建方式、上游同步和开发维护说明。
- [RECOVERY.md](docs/RECOVERY.md)：`v5.6.0-xray.5` 的历史源码恢复、二进制来源与可复核证据归档；不作为当前版本验收基线。
- [apk-reference](docs/apk-reference/README.md)：正式 APK 反编译文本证据索引。
- [ORIGINAL_README.md](docs/ORIGINAL_README.md)：冻结保存的原 `v5.6.0-xray.5` 发布说明。

## 说明

本项目不提供影视资源、点播源、直播源、Spider、第三方 Jar、Xray 节点、代理订阅或代理网络服务。用户自行导入的第三方资源由相应提供方负责，请自行判断其合法性、安全性和可用性，并遵守所在地法律法规。

FongMi/TV、XTLS/libXray、Xray-core 以及其他第三方代码分别遵循其自身许可证。仓库许可证见 [LICENSE.md](LICENSE.md)。

# FingMi-Xray

FingMi-Xray 是基于 [FongMi/TV](https://github.com/FongMi/TV) 的 Android TV 二次开发项目，安装后的应用显示名称为 **FongMi-Xray**。

项目主要面向一种很具体的播放场景：**影视接口、节目单和播放地址本身可以正常获取，但部分港澳台、海外或跨境媒体线路在当前网络环境下直连质量较差。**

FingMi-Xray 将 Xray 集成到播放器内部。遇到这类内容时，可以只为**当前正在播放的媒体会话**临时启用 Xray，而不需要给整台电视建立系统 VPN，也不要求路由器长期运行代理。

## 项目版本

当前 `main` 以 FongMi/TV 5.6.3（`c616c0aa3613e87529791587a9f71b78c278c991`）为公开上游基线，只长期维护 **Xray 播放代理**与 **Android TV 网络恢复**两项自有能力。历史 `v5.6.0-xray.5` armeabi-v7a 正式 APK 是源码丢失后的 Xray 恢复基线：它经过实际使用、相对稳定，适合在缺少源码时先还原行为，但并不代表完全没有未知 Bug。当前模块化重构已经完成；后续若在这两项自有能力中确认真实问题，可以基于证据修复并登记与黄金版的有意差异，其余 FongMi 功能保留 5.6.3 稳定基线，不再自动跟随公开上游。

GitHub Releases 保留 `v5.6.0-xray.5` 黄金参考、一个[当前正式版](https://github.com/rileyaaa/FingMi-Xray/releases/latest)；今后只上传 APK，不再生成或上传项目源码备份包。正式版包含独立 `:xray`、`:tv-recovery` 模块，以及 Hysteria2 备注查询、公网 IPv6 播放地址、播放页初始化/交接和冷入口待机恢复修复，使用固定正式签名。版本命名与递增规则见 [PROJECT.md](docs/PROJECT.md#版本命名与覆盖升级)，AI 发布要求见 [AI_COLLABORATION.md](docs/AI_COLLABORATION.md#11-ai-开发与发布的版本约束)，签名恢复与构建验收见 [DEVELOPMENT.md](docs/DEVELOPMENT.md#固定签名与-release-构建校验)。旧签名安装包首次切换需要卸载；后续保持同签名与包名、递增 versionCode，可覆盖安装。

当前正式版为 `v5.6.3-xray.1` / `563001`（用户明确要求的一次性同名替换）：包含已合入的 Xray 去敏与 TV 网络恢复修复；保留默认关闭的 TLS 分片开关、退出清理、主机名崩溃及 decoder 依赖修复。此前 `.2`～`.4` 安装版的 versionCode 较高，通常不能直接覆盖降级；请先备份应用配置。分片参数与适用范围见 [开发说明](docs/DEVELOPMENT.md#settings--binder)，实际发布状态以 Releases 为准。

主要版本与构建环境如下（**以仓库配置为准**）：

| 项目 | 当前版本 / 基线 |
| --- | --- |
| FongMi/TV 公开源码 | **5.6.3**（commit `c616c0aa3613e87529791587a9f71b78c278c991`） |
| FongMi/media / Media3 fork | **1.11.0**（commit `3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`） |
| libXray AAR / Xray-core | **v26.7.28** |
| Java / Gradle / Android Gradle Plugin | **21 / 9.7.1 / 9.3.1** |
| compileSdk / targetSdk / minSdk | **37 / 37 / 24** |

其他 AndroidX、OkHttp、Glide、QuickJS、Chaquopy 等依赖版本由 [Gradle version catalog](gradle/libs.versions.toml) 管理；Gradle wrapper 以 [仓库配置](gradle/wrapper/gradle-wrapper.properties) 为准。CI 的 SDK/Build Tools 安装和完整构建步骤见 [DEVELOPMENT.md](docs/DEVELOPMENT.md#7-构建)，不在这里重复维护几十项依赖清单。

当前从固定公开 FongMi/media 源码重建 **18 个播放器 AAR**；Libass compatibility 仍有单独登记的 native 构建债，不能据此把更高版本 Release/APK 当作公开上游源码。详细构建边界见 [DEVELOPMENT.md](docs/DEVELOPMENT.md#5-当前媒体兼容层)，历史二进制来源见 [RECOVERY.md](docs/RECOVERY.md)。

当前正式 APK 的双 ABI SHA-256、构建源码与设备验收范围见 [GitHub Release](https://github.com/rileyaaa/FingMi-Xray/releases/latest)。

## 核心设计

- **稳定基线优先**：固定 FongMi/TV 5.6.3，重点维护 Xray 与 Android TV 网络恢复；普通业务、UI 与播放器默认不主动改动。
- **默认直连**：首页、搜索、详情、普通接口等仍使用 FongMi 原有网络。
- **按需开启**：只有用户在当前播放中手动开启 Xray，当前媒体连接才进入 Xray。
- **会话隔离**：切集、切频道、换线路、换源、换播放器等逻辑播放身份变化后，新播放默认重新直连；同一身份内的 parser / redirect / CDN 实际 URL 变化不重置 Xray。
- **媒体旁路一致性**：Xray active 时，DRM、RTSP / RTSPT、字幕、弹幕、EPG/XML 等与当前播放绑定的远程请求遵守同一播放网络身份；远程 artwork / logo 在无法安全复用该身份时按黄金行为阻断或抑制普通直连加载。
- **本地资源保持本地**：无 scheme 的本地路径以及 `file`、`content`、`asset`、`data`、`rawresource`、`android.resource` 等 Android 本地资源不会为了 Xray 被改成网络代理请求；其它无法完整保证播放网络身份的泛用协议会 fail-closed。
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

兼容目标沿用冻结发布说明：**以 v2rayN 导出的标准单节点分享链接作为主要兼容与测试目标**。v2rayN 只是格式来源，不是项目依赖；其它客户端生成的非标准链接可能存在差异。

## 当前结构

早期黄金版本的 Xray 逻辑与当时 FongMi 播放代码耦合较深，不利于独立维护和持续跟随上游。当前重构已经完成，仓库现按以下职责边界维护：

- `:xray`：Xray 配置、Service / Binder、会话控制、SOCKS 网络资源与安全逻辑；
- `:libxray`：Android 侧 `libXray.aar` 依赖入口；
- `:tv-recovery`：独立 TV 前后台网络代际与恢复协调核心；
- `:app`：FongMi 的 VOD / Live 播放身份、播放器与 UI 接线；
- `:catvod`：普通业务网络、DNS / DoH 与 Spider；
- `compat/`：当前 5.6.3 构建仍需维护的媒体兼容源码与补丁；
- `recovery/`：历史发布版 faithful 恢复、native 动态 fixture 与节点兼容证据；其中经固定 SHA 验证的 v7 行为证据用于约束 current Xray parity；
- `docs/apk-reference/`：正式 APK 的最小可复核 JADX / Manifest / DEX 文本证据；
- `tests/`：当前 `main` 的源码 guard、JVM lifecycle、native chain parity 与测试 fixture。
- `website/`：随固定 FongMi/TV 上游保留的静态文档站源码；本 fork 不启用 Pages 自动部署，也不维护目录 README。

这样做的目的，是让项目自己的能力尽量集中在稳定边界内，减少对现有 5.6.3 稳定播放器的侵入式修改。

## 文档

- [PROJECT.md](docs/PROJECT.md)：项目设计、职责边界与长期架构约束。
- [DEVELOPMENT.md](docs/DEVELOPMENT.md)：当前源码、构建、测试与精选维护记录。
- [AI_COLLABORATION.md](docs/AI_COLLABORATION.md)：AI 协作执行限制；用户调整开发规则时同步维护。
- [RECOVERY.md](docs/RECOVERY.md)：`v5.6.0-xray.5` 的 faithful 恢复、APK/JADX/DEX/native 证据、二进制 provenance 与 Xray 黄金行为索引。
- [ORIGINAL_README.md](docs/ORIGINAL_README.md)：**冻结**保存的原 `v5.6.0-xray.5` 发布说明；除非用户明确解除冻结，不再修改。

## 说明

本项目不提供影视资源、点播源、直播源、Spider、第三方 Jar、Xray 节点、代理订阅或代理网络服务。用户自行导入的第三方资源由相应提供方负责，请自行判断其合法性、安全性和可用性，并遵守所在地法律法规。

FongMi/TV、XTLS/libXray、Xray-core 以及其他第三方代码分别遵循其自身许可证。仓库许可证见 [LICENSE.md](LICENSE.md)。

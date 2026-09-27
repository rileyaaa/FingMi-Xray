# FingMi-Xray

FingMi-Xray 是基于 [FongMi/TV](https://github.com/FongMi/TV) 的 Android TV 二次开发项目。

项目主要面向一种很具体的播放场景：**影视接口、节目单和播放地址本身可以正常获取，但部分港澳台、海外或跨境媒体线路在当前网络环境下直连质量较差。**

FingMi-Xray 将 Xray 集成到播放器内部。遇到这类内容时，可以只为**当前正在播放的媒体会话**临时启用 Xray，而不需要给整台电视建立系统 VPN，也不要求路由器长期运行代理。

## 核心设计

- **默认直连**：首页、搜索、详情、普通接口等仍使用 FongMi 原有网络。
- **按需开启**：只有用户在当前播放中手动开启 Xray，当前媒体连接才进入 Xray。
- **会话隔离**：切集、切频道、换源、换地址或换播放器后，新播放默认重新直连。
- **非全局代理**：不使用 Android `VpnService`，不接管其他应用或整台设备的网络。
- **独立进程**：Xray Core 运行在应用自己的 `:xray` 私有进程中，会话结束后收口相关网络与运行资源。
- **电视网络恢复**：另外保留针对部分 Android TV 长后台、待机或 Fast Start 后旧连接失效的网络恢复逻辑；这项能力与 Xray 播放代理彼此独立。

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
- `recovery/`：发布版恢复、反编译验证和兼容性测试材料。

这样做的目的，是让项目自己的能力尽量集中在稳定边界内，减少后续跟随 FongMi/TV 上游升级时的侵入式修改。

## 文档

- [PROJECT.md](docs/PROJECT.md)：项目设计、职责边界与长期架构约束。
- [DEVELOPMENT.md](docs/DEVELOPMENT.md)：当前源码结构、构建方式、上游同步和开发维护说明。
- [RECOVERY.md](docs/RECOVERY.md)：`v5.6.0-xray.5` 发布版源码恢复与可复核证据。
- [apk-reference](docs/apk-reference/README.md)：正式 APK 反编译文本证据索引。
- [ORIGINAL_README.md](docs/ORIGINAL_README.md)：冻结保存的原 `v5.6.0-xray.5` 发布说明。

## 说明

本项目不提供影视资源、点播源、直播源、Spider、第三方 Jar、Xray 节点、代理订阅或代理网络服务。用户自行导入的第三方资源由相应提供方负责，请自行判断其合法性、安全性和可用性，并遵守所在地法律法规。

FongMi/TV、XTLS/libXray、Xray-core 以及其他第三方代码分别遵循其自身许可证。仓库许可证见 [LICENSE.md](LICENSE.md)。

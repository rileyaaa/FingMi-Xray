# FingMi-Xray 项目设计

本文定义 FingMi-Xray 的**产品边界、模块职责和长期架构约束**。

它不记录构建结果、恢复进度、Actions run、发布状态或调试过程。发布版恢复依据见 [RECOVERY.md](RECOVERY.md)，当前工程维护方式见 [DEVELOPMENT.md](DEVELOPMENT.md)。

## 1. 项目为什么存在

FingMi-Xray 基于 FongMi/TV。项目保留 FongMi 原有的点播、直播和播放器能力，只针对 Android TV 使用中的两个场景增加自己的逻辑：

1. 某些媒体地址可以获取，但当前网络直连播放质量差，需要临时使用 Xray；
2. 某些电视在待机、Fast Start 或长后台后继续复用失效的网络状态，需要恢复普通业务网络。

这两项能力解决的问题不同，因此在架构上必须彼此独立。

项目的长期目标不是维护一个到处散落定制代码的 FongMi 分叉，而是把项目自己的能力收敛到少量明确边界，使上游升级时可以清楚判断哪些代码属于 FongMi、哪些代码属于 FingMi-Xray。

## 2. 播放 Xray 的产品边界

Xray 是**当前播放会话的可选网络通道**，不是设备级代理。

必须保持以下约束：

- 不创建 Android 系统 VPN；
- 不使用 `VpnService` 接管设备流量；
- 不代理其他 Android 应用；
- 首页、搜索、详情、普通 API 等不因为播放启用 Xray 而自动进入代理；
- 用户必须针对当前播放手动开启；
- 新的播放身份默认直连；
- 当前播放结束、退出或身份变化后，不让旧 Xray 会话继续影响后续播放。

“播放身份变化”至少包括：

- VOD 切集、换线路、换源或实际播放地址变化；
- Live 切频道、换线路或换源；
- 真正更换播放器；
- 离开播放页面或播放生命周期结束。

代理开启与关闭允许在必要时保留当前播放位置等状态，但不能把旧网络身份带到新的媒体身份。

## 3. Android TV 网络恢复的边界

电视网络恢复处理的是**应用普通网络生命周期**，不是 Xray 代理生命周期。

部分电视在待机或长后台后，应用进程仍然存在，但旧 Socket、HTTP client、DNS / DoH 或 Spider 环境已经失效。恢复逻辑负责在新的前台网络代际中：

- 取消旧业务请求；
- 重建普通 API / DNS / DoH 运行环境；
- 清理需要失效的 Spider 状态；
- 等待系统网络重新稳定；
- 再刷新普通业务页面。

这套逻辑属于 `:app` / `:catvod`，不得为了“模块化 Xray”而移动到 `:xray`。

播放器当前允许继续工作的媒体连接，也不能被普通网络恢复逻辑无条件重置。

## 4. 模块职责

### `:xray`

`:xray` 是项目定制 Xray 能力的主要边界，负责：

- 分享链接归一化；
- Xray runtime config；
- `libXray` 调用桥；
- 独立 Xray Service；
- AIDL / Binder 通信；
- operation / generation 控制；
- 播放 Xray 会话状态机；
- SOCKS HTTP client 与 RTSP SocketFactory；
- 公开目标地址防护；
- 节点测试；
- 证书 pin 与分享链接安全存储；
- Xray 错误信息去敏。

它不应该直接拥有 FongMi 的 VOD / Live 页面、首页网络生命周期、Spider 或电视待机恢复。

### `:libxray`

`:libxray` 只提供 Android AAR 依赖入口，让 `:xray` 不需要把大型二进制直接塞进业务源码。

二进制来源、恢复和校验规则属于恢复 / 构建流程，不属于业务模块职责。

### `:app`

`:app` 负责把 FongMi 的业务状态转换成稳定的模块调用：

- 判定当前 VOD / Live 播放身份；
- 展示 Xray 控件和设置入口；
- 创建与结束 `XrayPlaybackSession`；
- 把 Xray 网络资源交给播放器；
- 处理 DRM、RTSP、字幕、弹幕、封面、EPG 等媒体旁路；
- 处理播放器切换和当前播放快照；
- 承载 Android TV 前后台与 DLNA 生命周期适配。

`:app` 不应该重新实现 Xray Core、证书 pin 或节点解析。

### `:catvod`

`:catvod` 继续负责 FongMi 普通网络能力，包括：

- 普通 HTTP client；
- DNS / DoH；
- Spider 所依赖的网络基础设施。

它可以暴露网络重建入口，但不感知某个播放会话是否启用了 Xray。

## 5. 播放网络模型

一次启用 Xray 的播放应拥有独立网络资源。

HTTP / HTTPS、DRM license 和 RTSP 等与当前媒体播放直接相关的连接，需要遵守同一个播放网络身份；不能出现主视频走 Xray、DRM 或旁路请求悄悄回到不匹配网络身份的情况。

同时要保持以下隔离：

- Xray 播放不复用普通直连预加载身份；
- 不让普通直连缓存把旧网络身份带进 Xray 会话；
- Xray SOCKS 使用独立连接资源；
- 会话结束后关闭对应 Dispatcher、连接池、executor 和 Service 状态；
- 旧异步回调不能覆盖更新的播放会话。

网络代理是媒体会话的属性，不是应用全局单例状态。

## 6. 安全边界

节点与代理能力不能降低应用原有安全边界。

项目长期保持：

- 分享链接使用 Android Keystore 保护；
- 敏感错误内容在展示前去敏；
- TLS / HY2 非默认信任场景通过证书 pin 管理；
- Xray 播放拒绝明显的本机、私网和保留目标，避免把代理通道当成内部网络访问入口；
- Binder Service 不对其他应用导出；
- Service 运行在应用私有 `:xray` 进程。

## 7. 上游升级原则

FingMi-Xray 应尽可能继续跟随 FongMi/TV，而不是复制整个上游长期独立演化。

升级时遵循：

1. 先以目标 FongMi 上游为主体；
2. `:xray` 尽量保持独立，不因普通上游变化而修改；
3. `:app` 只保留必要的播放身份、播放器和 UI 适配；
4. TV 网络恢复保持独立、少量、可审计；
5. 媒体二进制或 API 不匹配时，通过明确的 compatibility adapter 处理，不伪装成上游原生实现；
6. 发布版行为恢复与当前工程重构分开维护，不能用新实现反向篡改旧发布行为事实。

## 8. 仓库中各类材料的定位

| 路径 | 定位 |
| --- | --- |
| `app/` | 当前 FongMi/TV 应用与 FingMi-Xray 接线 |
| `xray/` | 当前模块化 Xray 实现 |
| `libxray/` | `libXray.aar` 依赖容器 |
| `catvod/` | FongMi 普通网络与 Spider 基础 |
| `recovery/legacy-src/` | `v5.6.0-xray.5` faithful 恢复源码 |
| `recovery/*-tests/` | 发布版行为、native、媒体兼容和竞态验证 |
| `docs/apk-reference/` | 可直接进 Git 的反编译文本证据 |
| `scripts/` | 构建、恢复和验证工具 |

当前工程代码与 faithful 恢复代码是两种不同用途的材料。前者用于继续开发，后者用于回答“原发布版实际上是什么行为”。

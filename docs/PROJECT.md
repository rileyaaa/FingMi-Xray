# FingMi-Xray 项目设计

本文定义 FingMi-Xray 的**产品边界、模块职责和长期架构约束**。

它不记录构建结果、Actions run、发布状态或调试过程。当前工程维护与验收规则见 [DEVELOPMENT.md](DEVELOPMENT.md)；AI 协作与文档记录边界见 [AI_COLLABORATION.md](AI_COLLABORATION.md)；[RECOVERY.md](RECOVERY.md) 保存旧发布版的恢复、二进制 provenance 与 Xray 黄金行为证据。

> 当前开发基线为 `main`；长期只维护 Xray 与 Android TV 网络恢复两项自有能力。

## 1. 项目为什么存在

FingMi-Xray 基于 FongMi/TV。项目保留 FongMi 原有的点播、直播和播放器能力，只针对 Android TV 使用中的两个场景增加自己的逻辑：

1. 某些媒体地址可以获取，但当前网络直连播放质量差，需要临时使用 Xray；
2. 某些电视在待机、Fast Start 或长后台后继续复用失效的网络状态，需要恢复普通业务网络。

这两项能力解决的问题不同，因此在架构上必须彼此独立。

项目的长期目标不是维护一个到处散落定制代码的 FongMi 分叉，而是把项目自己的能力收敛到少量明确边界，使上游升级时可以清楚判断哪些代码属于 FongMi、哪些代码属于 FingMi-Xray。

### 维护边界（最高优先级）

**业务功能层只维护两项项目自有能力：Xray 播放代理与 Android TV 网络恢复。其余 FongMi/TV 业务、UI、播放器行为、设置、媒体效果和通用工具默认跟随上游，不做主动魔改。**

允许落在上游代码中的项目改动只有三类：

1. 为 Xray 接入所必需的最小 hook / adapter；
2. 为 TV 网络恢复所必需的最小生命周期 / 网络重建 hook；
3. 为保证本 fork 能构建、发布和不被上游 APK 自更新覆盖所需的基础设施改动。

这些例外都不能扩展成新的独立业务功能。只要上游已有实现能够工作，就优先保留上游实现；同步上游时也应先恢复/采用上游版本，再重新应用上述最小差异。

低 Android 版本兼容同样遵守这个边界：**不对上游 FongMi 原样代码做全局 API “清洗”或机械替换。** 兼容审计只针对 FingMi-Xray 新增代码、TV 网络恢复代码以及两者必要的接线；如果问题来自上游，应优先跟随上游的构建/desugaring方案或上游修复，除非已经有明确的目标设备故障证据要求最小补丁。

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

- VOD 切集、换线路或换源；
- Live 切频道、换线路或换源；
- 真正更换播放器；
- 离开播放页面或播放生命周期结束。

同一逻辑播放身份内的 parser 解析结果、HTTP redirect 或 CDN 实际 URL 变化不属于播放身份变化，不应因此结束或重置 Xray；最终请求如果不满足 Xray 的 scheme / destination guard，仍然 fail-closed。

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

二进制来源与校验规则属于构建流程，不属于业务模块职责。历史 APK 可以同时承担当前部分 native 字节的 provenance 和 Xray 行为黄金证据，但不能反过来要求当前 `main` 恢复旧版混合架构。

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

HTTP / HTTPS、DRM license、RTSP / RTSPT，以及字幕、弹幕、EPG/XML 等与当前播放网络身份绑定的远程请求，需要遵守同一个播放网络身份；不能出现主视频走 Xray、DRM 或媒体旁路请求悄悄回到不匹配网络身份的情况。

同时要保持以下隔离：

- Xray 播放不复用普通直连预加载身份；
- 不让普通直连缓存把旧网络身份带进 Xray 会话；
- Xray active 时播放器使用能够注入该会话网络资源的 Exo engine；真正切换播放器属于播放身份变化，先结束旧 Xray 会话，再按普通 FongMi 规则选择新 engine；
- HTTP / HTTPS 使用当前 Xray client，RTSP / RTSPT 使用会话 SOCKS SocketFactory，DRM license 复用同一 proxied DataSource；
- 无 scheme 的本地路径以及 Android 本地资源 scheme（`file`、`asset`、`content`、`data`、`rawresource`、`android.resource`）仍保持本地读取，不被伪装成代理流量；其它无法保证网络身份的泛用 scheme 在 Xray active 时 fail-closed；
- Xray SOCKS client 从普通 player client 的配置派生，但拥有独立 Dispatcher、ConnectionPool 与 SOCKS 资源；
- 会话结束后关闭对应 Dispatcher、连接池、executor 和 Service 状态；
- 旧异步回调不能覆盖更新的播放会话。

网络代理是媒体会话的属性，不是应用全局单例状态。

## 6. 安全边界

节点与代理能力不能降低应用原有安全边界。

项目长期保持：

- 分享链接使用 Android Keystore 保护；
- 敏感错误内容在展示前去敏；
- TLS / HY2 非默认信任场景通过证书 pin 管理；
- Xray runtime config 把当前会话 DNS 解析路由到代理 outbound，并在 Core routing 层直接 blackhole localhost、私网和保留网段；
- HTTP(S) 播放请求另有 destination interceptor 再次拒绝本机、私网和保留目标，形成 Core routing + HTTP destination 的双层保护；
- Binder Service 不对其他应用导出；
- Service 运行在应用私有 `:xray` 进程。


## 7. Android 运行时与 native 故障边界

这一节只约束**项目自有代码与项目接线**，不要求把 FongMi/TV 上游源码整体改写成另一套低版本兼容实现。

当前源码可以使用 Java 21 编译，但 Android 运行时能力由设备 ART 决定。对 Xray / TV 网络恢复新增代码，不能因为编译器接受某个 JDK API，就默认目标 Android 运行时一定存在对应方法。

长期约束：

- Xray 关键路径避免直接调用旧 ART 不具备的新 JDK API；
- URL 编解码等兼容点优先使用在低 Android 版本上已有的 overload；
- `StringBuilder.isEmpty()`、`String.isBlank()`、集合 factory 等已知风险 API 由源码 guard 阻止重新进入 Xray 路径；
- `LibXrayBridge`、Service 与 client 对 Java linkage failure 做明确收口，尽量返回可诊断错误而不是只留下 Binder process death；
- `LibXrayBridge` 不在逐次 native invoke 路径输出额外 begin/end 日志；故障通过去敏后的 Service/client 错误、Binder 状态、Android logcat 与定向 parity / harness 定位；
- release 混淆必须保留 gomobile / libXray JNI 所需类名与方法名。

这些约束属于当前架构本身，不是旧发布版兼容测试的临时补丁。

## 8. 更新与发布边界

FingMi-Xray 不允许应用内从 FongMi/Release 下载并安装上游 APK。上游自更新会直接覆盖当前 fork，因此：

- Home 不做上游版本检查；
- 设置页版本信息不承担更新入口；
- `Updater` 仅保留 no-op 兼容壳；
- Manifest 不申请 `REQUEST_INSTALL_PACKAGES`；
- 测试包和正式包只由本仓库明确构建、发布并由用户主动安装。

从 5.6.3 重构线开始，**`main` 负责现行源码、架构、构建和上游同步；`v5.6.0-xray.5` v7 正式 APK 是 Xray 外部行为黄金参考。** `main` 不要求重新通过 faithful APK 重建才能发布，但涉及 Xray 行为的修改必须通过冻结证据、自动 parity 或真机证据证明没有无意偏离。

## 9. 上游升级原则

FingMi-Xray 应尽可能继续跟随 FongMi/TV，而不是复制整个上游长期独立演化。除 Xray 与 TV 网络恢复外，**“和上游一致”本身就是默认维护目标。**

升级时遵循：

1. 先以目标 FongMi 上游为主体，普通业务代码不继续维护本 fork 的平行版本；
2. `:xray` 尽量保持独立，不因普通上游变化而修改；
3. `:app` 只保留 Xray / TV 网络恢复所需的最小播放身份、播放器、UI 与生命周期 hook；
4. TV 网络恢复保持独立、少量、可审计；
5. 不主动修改与两大模块无关的播放器效果、设置、页面交互、业务模型或通用工具；
6. 媒体二进制或 API 不匹配时，只允许使用明确、最小的 compatibility adapter 让当前上游代码可构建，不把 adapter 演变成第三套业务实现；
7. 低版本兼容补丁只处理项目新增/接线代码中的已证实问题；上游原样代码默认保留上游写法；
8. 历史发布版证据与当前工程重构分开保存；v7 证据用于定义 Xray 外部行为黄金参考，但不定义 `main` 的源码组织、上游版本或混合架构；

## 10. 仓库中各类材料的定位

| 路径 | 定位 |
| --- | --- |
| `app/` | 当前 FongMi/TV 应用与 FingMi-Xray 接线 |
| `xray/` | 当前模块化 Xray 实现 |
| `libxray/` | `libXray.aar` 依赖容器 |
| `catvod/` | FongMi 普通网络与 Spider 基础 |
| `compat/media3-libass/` | 当前 5.6.3 构建使用的 Media3 / Libass compatibility 源码与补丁 |
| `recovery/legacy-src/` | `v5.6.0-xray.5` 历史 faithful 恢复源码，仅用于归档与来源复核 |
| `recovery/legacy-tests/`、`recovery/native-tests/`、`recovery/node-dns-tests/`、`recovery/v2rayn-tests/` | 发布版 faithful / native / 节点行为证据与 fixture；其中冻结 oracle 可被 current parity 测试直接使用 |
| `tests/` | 当前源码回归测试入口与测试 fixture |
| `docs/apk-reference/` | 可直接进 Git 的反编译文本证据 |
| `scripts/build/` | 当前依赖与 compatibility 构建工具 |
| `scripts/recovery/` | 历史 faithful / native 恢复与来源提取工具 |
| `website/` | 随固定 FongMi/TV 上游保留的静态文档站源码；本 fork 不启用 Pages 自动部署，也不单独维护目录 README |

当前工程代码与历史 faithful 恢复代码是两种不同用途的材料。当前 `main` 决定现行架构与实现；历史 v7 证据回答“发布版 Xray 的外部行为是什么、当前复用二进制从哪里来”。目标是把黄金行为映射到当前模块化架构，而不是把 `main` 回退成旧源码结构。

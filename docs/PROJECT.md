# FingMi-Xray 项目设计

本文定义 FingMi-Xray 的**产品边界、模块职责和长期架构约束**。

它不记录构建结果、Actions run、发布状态或调试过程。当前工程维护与验收规则见 [DEVELOPMENT.md](DEVELOPMENT.md)；AI 协作与文档记录边界见 [AI_COLLABORATION.md](AI_COLLABORATION.md)；[RECOVERY.md](RECOVERY.md) 保存旧发布版的恢复、二进制 provenance 与 Xray 黄金行为证据。

> 当前开发基线为 `main`；长期只维护 Xray 与 Android TV 网络恢复两项自有能力。

## 1. 项目为什么存在

FingMi-Xray 基于 FongMi/TV。项目保留 FongMi 原有的点播、直播和播放器能力，只针对 Android TV 使用中的两个场景增加自己的逻辑：

1. 某些媒体地址可以获取，但当前网络直连播放质量差，需要临时使用 Xray；
2. 某些电视在待机、Fast Start 或长后台后继续复用失效的网络状态，需要恢复普通业务网络。

这两项能力解决的问题不同，因此在架构上必须彼此独立。历史黄金版把 Xray 深度写在当时的 FongMi 应用结构里，在源码丢失时可以作为恢复对象，但这种一体化形态不适合长期维护，也会显著增加维护固定 FongMi 5.6.3 稳定基线的成本。

当前 `main` 已完成模块化重构：Xray 的 Core / Service / Binder / 会话 / 网络与安全能力集中到独立模块，TV 待机网络恢复独立协调，`:app` 仅保留接入 FongMi 必需的最小 hook。**长期策略是固定 5.6.3 稳定基线，只持续维护这两个模块与必要接线**；不将普通业务重新复制成第三套实现。

Xray 的历史 `v5.6.0-xray.5` v7 APK 是源码丢失后的**恢复基线和已知稳定行为参考**，不是“绝对正确规范”或“无 Bug 规范”。在什么都没有、缺少更强源码证据时先按黄金行为恢复，目的是以经过实际使用的实现为起点，避免凭空重写；恢复完成后若 Xray 自身出现可复现故障、安全问题、竞态、资源泄漏或其它有证据的缺陷，current 应在模块化架构中修复，而不是因为黄金版也存在同一行为就永久保留。此类差异必须明确登记“黄金原行为”“current 修正理由”和验证证据，而不是伪装成 parity。

### 维护边界（最高优先级）

**业务功能层只维护两项项目自有能力：Xray 播放代理与 Android TV 网络恢复。其余 FongMi/TV 业务、UI、播放器行为、设置、媒体效果和通用工具默认跟随上游，不做主动魔改。**

允许落在上游代码中的项目改动只有三类：

1. 为 Xray 接入所必需的最小 hook / adapter；
2. 为 TV 网络恢复所必需的最小生命周期 / 网络重建 hook；
3. 为保证本 fork 能构建、发布和不被上游 APK 自更新覆盖所需的基础设施改动。

这些例外都不能扩展成新的独立业务功能。只要上游已有实现能够工作，就优先保留上游实现；普通 FongMi 业务保持现有 5.6.3 源码，必要修复需独立验证。

对于有明确证据且明显影响实际使用的上游故障，用户允许最小修补，不能借此增加通用功能或预防性改写。已保留的补丁必须登记在 [DEVELOPMENT 前部](DEVELOPMENT.md#已登记的上游业务修复升级前必读)，修复时核对是否已有等价实现；具体证据与执行限制遵循 [AI_COLLABORATION 第 9 节](AI_COLLABORATION.md#9-开发与-bug-修复范围只限-xray-和-tv-待机网络恢复)。

低 Android 版本兼容同样遵守这个边界：**不对上游 FongMi 原样代码做全局 API “清洗”或机械替换。** 兼容审计只针对 FingMi-Xray 新增代码、TV 网络恢复代码以及两者必要的接线；如果问题来自上游，应优先跟随上游的构建/desugaring方案或上游修复，除非已经有明确的目标设备故障证据要求最小补丁。

## 2. 播放 Xray 的产品边界

Xray 是**当前播放会话的可选网络通道**，不是设备级代理。冻结的 [ORIGINAL_README.md](ORIGINAL_README.md) 保存旧发布版面向用户的原始承诺；若其概括性表述与后续 APK/DEX/native 证据存在粒度差异，以 [RECOVERY.md](RECOVERY.md) 的证据优先级解释历史行为，但不得借此扩大 current 产品范围。

必须保持以下约束：

- 不创建 Android 系统 VPN；
- 不使用 `VpnService` 接管设备流量；
- 不代理其他 Android 应用；
- 首页、搜索、详情、普通 API 等不因为播放启用 Xray 而自动进入代理；
- 用户默认针对当前播放手动开启；电视直播可由用户保存明确的分组/频道自动开启规则，两项留空即关闭；
- 新的播放身份默认直连，只有命中电视直播自动规则并通过地址检查的直播媒体才自动启用；
- 当前播放结束、退出或身份变化后，不让旧 Xray 会话继续影响后续播放。

“播放身份变化”至少包括：

- VOD 切集、换线路或换源；
- Live 切频道、换线路或换源；
- 真正更换播放器；
- 离开播放页面或播放生命周期结束。

同一逻辑播放身份内的 parser 解析结果、HTTP redirect 或 CDN 实际 URL 变化不属于播放身份变化，不应因此结束或重置 Xray；最终请求如果不满足 Xray 的 scheme / destination guard，仍然 fail-closed。

代理开启与关闭允许在必要时保留当前播放位置等状态，但不能把旧网络身份带到不符合规则的新媒体身份。连续命中电视直播自动规则的请求可保留同一 Core/HTTP transport，仍须推进逻辑播放身份、取消旧请求及重绑旁路资源。分组和频道规则为 OR，支持中英文逗号、换行、`*` 通配符（其余字符按字面匹配）；只对电视直播生效，回看、点播及 Mobile 保持原有行为。未命中、离页、后台、真正换播放器或配置切换按原生命周期收口；手动 OFF 对当前分组/频道有效，换台重新判定。自动 START 未完成时不得抢先直连播放，失败可手动重试；本地/不支持代理的地址保持既有边界。

节点输入兼容目标沿用原发布说明：主要以 **v2rayN 导出的标准单节点分享链接**做兼容与测试；v2rayN 只作为格式来源，不是项目依赖，也不意味着所有第三方非标准链接都必须兼容。

## 3. Android TV 网络恢复的边界

电视网络恢复处理的是**应用普通网络生命周期**，不是 Xray 代理生命周期。

部分电视在待机或长后台后，应用进程仍然存在，但旧 Socket、HTTP client、DNS / DoH 或 Spider 环境已经失效。恢复逻辑负责在新的前台网络代际中：

- 取消旧业务请求；
- 重建普通 API / DNS / DoH 运行环境；
- 清理需要失效的 Spider 状态；
- 等待系统网络重新稳定；
- 再刷新普通业务页面。

生命周期与恢复协调核心位于独立 `:tv-recovery` 模块；它通过接口调用应用提供的资源操作，不依赖 FongMi 业务类、`:app`、`:catvod` 或 `:xray`。FongMi 网络、Spider、Glide、Home 与 DLNA 接线集中在 `:app` 的 `com.fingmi.integration.recovery` 适配层，普通 HTTP/DNS 资源仍由 `:catvod` 拥有。

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

### `:tv-recovery`

`:tv-recovery` 独立拥有前后台 / SCREEN 网络代际、已完成代际和串行恢复协调。它只依赖 Android 生命周期 API，通过 `Renderer` 与 `Hooks` 接口调用宿主能力；不读取站点配置、不认识 Home、Spider、播放器或 Xray。核心行为与测试可以独立维护，相关改动只核对应用适配层的资源接口。

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

项目自有的上游适配代码使用 `com.fingmi.integration` 命名空间：恢复适配层绑定 FongMi 资源和独立恢复模块；Xray 的应用封面适配绑定 FongMi 播放器。上游页面保留必要的创建、调用与销毁入口。独立维护不意味着零接入点，修改接线时仍需验证播放器、网络资源与生命周期。

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

从 5.6.3 重构线开始，**`main` 负责现行 5.6.3 源码、架构、构建和维护；`v5.6.0-xray.5` v7 正式 APK 是 Xray 外部行为黄金参考。** `main` 不要求重新通过 faithful APK 重建才能发布，但涉及 Xray 行为的修改必须通过冻结证据、自动 parity 或真机证据证明没有无意偏离。

### 版本命名与覆盖升级

正式版本统一使用 `v<公开 FongMi 版本>-xray.<本 fork 修订号>`，Release tag 与应用设置显示的 `versionName` 必须一致。例如 `v5.6.3-xray.1` 中，`5.6.3` 对应实际采用的公开 FongMi/TV 源码版本，`xray.1` 对应本项目二开修补发布的第 1 个正式修订，涵盖 Xray 与待机网络恢复；它不表示 Xray-core 的版本。不得用更高版本的上游 APK 版本号替代公开源码基线。

同一上游基线的后续修补发布依次使用 `.2`、`.3` 等；跟随公开上游新版本时，从该上游版本的 `.1` 开始。未经用户明确要求，已经发布的修订号不得用于另一份修改后的 APK；只修改文档或审核代码而没有发布新 APK，不递增应用版本。

用户明确要求同名重编译替换时，作为单次例外保留 Release tag、应用 versionName / versionCode 与固定签名，并在 Release 记录新的源码 commit、Actions run 和 APK digest。相同 versionCode 的包不是新的升级序号，只能按设备安装器支持的同版本重装方式手动覆盖，不能依赖新版检测；后续正常发布仍按上述修订号递增，不延续该例外。

Android 安装顺序使用 `versionCode = 公开上游 versionCode × 1000 + fork 修订号`，修订号范围为 1..999，且最终数值必须严格递增、不超过 Android 最大值。上游 code 为 `563` 时，`.1` 对应 `563001`，`.2` 对应 `563002`；上游 code 为 `564` 时，首版对应 `564001`。显示版本名不能替代安装用的 versionCode。

后续覆盖升级必须保持包名 `com.fongmi.android.tv` 和固定正式签名，并递增 versionCode。不得在 AI 接手、环境重建或上游同步时重新生成签名。旧签名已遗失，首次切换需要备份配置并卸载旧安装；固定签名的位置、恢复方法和产物校验见 [DEVELOPMENT.md](DEVELOPMENT.md#固定签名与-release-构建校验)。AI 发布时的强制执行要求见 [AI_COLLABORATION.md](AI_COLLABORATION.md#11-ai-开发与发布的版本约束)。

用户指定 Android TV 应用显示名称为 **FongMi-Xray**，用于区分官方与二开版本；通过 Leanback flavor 资源覆盖实现。显示名称与安装包身份不同，改名不改变上述包名、签名和覆盖升级约束，也不重命名 GitHub 仓库或 Java namespace。

## 9. 固定稳定基线与维护原则

- 当前唯一维护分支为 `main`，固定公开 FongMi/TV 5.6.3（`c616c0aa3613e87529791587a9f71b78c278c991`）。
- 不再维护上游自动/一键升级 workflow、源码适配生成器或新版 Media3 实验构建链。
- 只对 Xray、Android TV 待机网络恢复及已证实影响使用的最小缺陷进行修补，不主动重写普通上游业务。
- 保留当前可重建的播放器 AAR、Libass/native 兼容、历史黄金 APK 取证和正式签名发布流程；在验证前不替换任何固定依赖。
- 任何涉及 Xray、Service、播放器或 Home 生命周期的修复，必须执行对应离线回归及必要的双 ABI APK 构建验证；不能以局部 JVM 成功冒充真机验证。

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
| `scripts/build/source-baseline.json` | 当前固定 FongMi/TV 5.6.3 来源基线；供发布版本检查使用 |
| `scripts/recovery/` | 历史 faithful / native 恢复与来源提取工具 |
| `website/` | 随固定 FongMi/TV 上游保留的静态文档站源码；本 fork 不启用 Pages 自动部署，也不单独维护目录 README |

当前工程代码与历史 faithful 恢复代码是两种不同用途的材料。当前 `main` 决定现行架构与实现；历史 v7 证据回答“发布版 Xray 的外部行为是什么、当前复用二进制从哪里来”。目标是把黄金行为映射到当前模块化架构，而不是把 `main` 回退成旧源码结构。

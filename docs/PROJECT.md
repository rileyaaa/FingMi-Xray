# FingMi-Xray 项目定义

本文定义 FingMi-Xray 的长期目标、产品边界和最终验收方向。它不是恢复进度日志，也不记录逐次调试过程。

原始 `v5.6.0-xray.5` 产品说明冻结于 [ORIGINAL_README.md](ORIGINAL_README.md)。发布版的恢复状态和证据统一记录在 [RECOVERY.md](RECOVERY.md)，后续工程开发与模块迁移统一记录在 [DEVELOPMENT.md](DEVELOPMENT.md)。

## 项目背景

FingMi-Xray 基于 FongMi/TV 二次开发。

已发布的 `v5.6.0-xray.5` 原始开发源码曾丢失，因此项目当前必须先恢复正式发布版行为，再以恢复完成的 faithful 基准推进模块化重构。项目不以“重新实现一个功能类似的版本”为目标，而以保留已发布版本长期调试形成的边界行为为目标。

## 两项核心能力

### 1. Xray 当前播放会话代理

这是第一优先级。

目标边界：

- 不创建 Android `VpnService`；
- 不接管整台电视或其他 App 的网络；
- 首页、搜索、详情、普通 API 等继续使用 FongMi 原有网络路径；
- 用户仅在当前 VOD 或 Live 播放会话需要时手动开启 Xray；
- 下一集、上一集、自动下一集、换线路、换源、换实际播放地址、换播放器、切直播频道、切直播源、播放结束、离开播放页面或手动关闭后，旧会话结束；
- 新播放内容默认重新使用直连，不继承上一播放会话的 Xray 状态；
- Xray Core 位于独立 `:xray` 私有进程；
- 会话结束时停止 Core、本地 SOCKS、相关连接与运行状态，并保留必要的私有进程收口能力；
- 分享链接、节点测试、设置、手机导入、证书安全和错误去敏等发布版能力必须保留；
- 播放器媒体请求、DRM、RTSP、字幕、弹幕、下载、Live metadata 等与播放身份相关的网络路径不能因重构绕开当前会话边界。

### 2. Android TV 长后台 / 待机网络恢复

这是第二优先级。

目标是改善部分 Android TV / 电视盒子在 Fast Start、长期后台或待机恢复后继续复用失效网络环境的问题，包括旧 Socket、普通 API client、DNS / DoH 和 Spider 等状态。

边界：

- 这是 app / catvod 的网络生命周期能力；
- **不属于 Xray 模块内部功能**；
- 模块化 Xray 时不能误删或迁入 Xray；
- 未来 FongMi 上游升级时应作为独立、少量、可审计的 app / catvod 适配保留。

## 恢复基准

恢复阶段的判断顺序：

1. 已固定 SHA-256 的正式发布 APK 实际行为；
2. [ORIGINAL_README.md](ORIGINAL_README.md) 的原始产品意图；
3. 固定 FongMi/TV 5.6.0 上游源码；
4. JADX、DEX 等反编译证据；
5. 当前恢复代码或实验性 `:xray` 模块。

JADX 是证据，不是最终源码。遇到明显控制流损坏、R8 合并或反编译自相矛盾时，应使用原始 DEX、上下文和双 ABI 对照消除歧义。

## ABI 策略

- **armeabi-v7a 是主要运行与恢复基线**，因为这是实际使用架构；
- arm64-v8a 用于关键逻辑、二进制和 ABI 的交叉验证；
- 最终 v7 要完成完整 Android TV 设备回归；
- v8 以成功构建、ABI / 静态核验和关键路径交叉验证为主要验收，不要求机械重复整套 v7 真机回归。

## 阶段顺序

项目阶段顺序固定如下：

### 阶段 1：Faithful recovery

- 恢复发布 APK 的可维护源码；
- 对照固定 FongMi/TV 5.6.0；
- 恢复缺失资源、Manifest、AIDL、Xray、播放器接线、TV 网络恢复和二进制依赖；
- 对反编译损坏点给出可复核证据；
- 完成静态恢复门。

### 阶段 2：Faithful build 与回归

- 在依赖来源、哈希和接口门通过后构建 faithful TV APK；
- 修正真实编译问题；
- 以 v7 为主完成关键功能设备回归；
- 不能用“编译成功”代替行为一致性验证。

### 阶段 3：模块化迁移

现有 `:xray` 模块保留为迁移目标。

迁移原则：

- `recovery/legacy-src/` 的 faithful 实现是迁移基准；
- 不以现有实验模块反向定义发布版行为；
- 将已验证能力逐块迁入 `:xray`；
- 不在同一改动中既迁移又大幅重写核心状态机；
- FongMi app 只保留必要的 VOD、Live、Player、Settings 和生命周期适配；
- TV 待机网络恢复继续留在 app / catvod。

### 阶段 4：真实 FongMi 上游升级

模块化完成后，必须实际选择一个较新的 FongMi 上游版本完成一次真实升级。

验收目的不是追求“最新版本”本身，而是证明：

- Xray 核心无需再次散落修改大量 FongMi 业务文件；
- 上游冲突集中在少量明确适配点；
- 第二优先级的 TV 网络恢复也能独立保留；
- 原有 FongMi 点播、直播和播放器能力不发生明显回退。

## 模块职责方向

最终职责大致如下：

### `:xray`

负责：

- libXray 调用；
- 分享链接归一化；
- Xray runtime config；
- 节点安全和证书 pin；
- 独立 `:xray` Service；
- Binder / operation generation；
- playback session 状态机；
- SOCKS 网络资源和通用 Xray 网络策略；
- 节点测试与持久化中适合独立的逻辑。

### app

负责：

- VOD / Live UI；
- 当前播放身份；
- 播放器切换；
- Exo / MPV 的实际接线；
- DRM、RTSP、字幕、弹幕、封面、下载等媒体场景适配；
- 设置入口和手机导入 UI；
- 将上游 FongMi 业务转换为稳定的 Xray 模块调用。

### catvod / app 网络生命周期

负责：

- 普通 API client；
- DNS / DoH；
- Spider；
- TV 前后台 / 待机网络代际恢复。

## 最终验收原则

项目不能因为某一项“看起来完成”就提前宣布结束。最终至少需要满足：

- faithful 源码和发布版主要行为对照完成；
- 恢复所需二进制来源可复现并有固定校验；
- faithful v7 APK 可重现构建；
- v7 关键设备回归完成；
- v8 构建 / ABI / 关键静态验证完成；
- Xray 正式迁入独立模块并经过同一行为基准回归；
- TV 网络恢复未因模块化丢失；
- 完成一次较新 FongMi 上游真实升级；
- 仓库文档能够让新的开发者或 AI 不依赖聊天历史继续工作。

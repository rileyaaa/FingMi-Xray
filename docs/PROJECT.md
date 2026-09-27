# FingMi-Xray 项目定义

本文只定义长期产品目标、架构边界和最终验收原则，不记录当前进度、构建编号或调试时间线。

发布版原始产品说明见 [ORIGINAL_README.md](ORIGINAL_README.md)；v5.6.0 恢复状态见 [RECOVERY.md](RECOVERY.md)；当前工程与后续开发见 [DEVELOPMENT.md](DEVELOPMENT.md)。

## 项目目标

FingMi-Xray 基于 FongMi/TV 二次开发。项目的目标不是维护一个长期分叉、到处散落 Xray 修改的 FongMi 副本，而是在保留原有播放能力的前提下，把项目特有逻辑收敛为少量稳定边界，使后续上游升级可以被审计和回归。

项目长期保留两项核心能力。

### 当前播放会话 Xray

Xray 只服务用户手动开启的当前媒体播放会话：

- 不创建 Android 系统 VPN；
- 不接管整台设备或其他应用的网络；
- 首页、搜索、详情、普通 API 等继续使用 FongMi 原有网络；
- 新集、新频道、新源、新地址、新播放器默认重新直连；
- 退出播放、播放结束或手动关闭后结束当前 Xray 会话；
- Xray Core 运行在独立 :xray 私有进程；
- 会话结束时必须收口 Core、SOCKS、连接池、线程和 Binder 状态；
- DRM、RTSP、字幕、弹幕、封面、下载、直播 metadata 等与播放身份有关的旁路请求不能绕开当前会话边界；
- 分享链接、节点测试、设置、手机导入、证书 pin、错误去敏等发布版能力必须保留。

### Android TV 网络恢复

部分电视在 Fast Start、待机或长后台恢复后会继续复用失效的 Socket、HTTP client、DNS / DoH 或 Spider 状态。

该能力的边界是：

- 属于 app / catvod 的网络生命周期；
- 不属于 Xray 模块；
- 不能因为 Xray 模块化而被迁入或删除；
- 未来上游升级时应保持为少量、独立、可审计的适配。

## 架构职责

### :xray

长期负责：

- libXray bridge；
- 分享链接归一化和 runtime config；
- 节点安全、证书 pin 与适合模块持有的持久化；
- 独立 Service、AIDL / Binder；
- operation id、generation 与会话状态机；
- SOCKS HTTP / socket 资源；
- 通用公开目的地防护；
- 节点测试控制。

:xray 不直接拥有 FongMi Activity、首页 / Spider 生命周期或 TV 待机网络恢复。

### app

负责：

- VOD / Live 当前播放身份；
- Xray 开关和播放器接线；
- PlayerManager、Exo / MPV 适配；
- DRM、RTSP、字幕、弹幕、封面、下载等媒体场景；
- 设置和手机导入 UI；
- 将上游 FongMi 业务转换为稳定的 Xray 模块调用。

### catvod / app 网络生命周期

负责：

- 普通 API client；
- DNS / DoH；
- Spider；
- 电视前后台、屏幕和网络变化后的网络代际恢复。

## 可信依据

发布版行为发生冲突时，按以下顺序判断：

1. 已固定 SHA-256 的正式发布 APK；
2. 冻结的原始发布说明；
3. 对应版本的固定 FongMi/TV 上游源码；
4. JADX、DEX、ELF / JNI 等可复核证据；
5. 当前恢复代码或实验实现。

反编译结果只能作为证据。出现不可能条件、R8 合并控制流或 JADX 自相矛盾时，必须继续核 DEX、双 ABI 或其他更强证据。

## ABI 原则

- armeabi-v7a 是发布版恢复和完整真机回归的主基准；
- arm64-v8a 用于关键路径、二进制和 ABI 交叉验证；
- v7 最终必须完成完整 Android TV 设备回归；
- v8 至少要完成构建、ABI 和关键逻辑核验，不要求机械重复全部 v7 场景。

## 验证关系

项目存在恢复、模块化和上游升级等不同工作面。开发实验可以提前进行，但最终验收关系不能倒置：

1. v5.6.0 faithful 基准必须能够独立构建并完成设备回归；
2. 模块化实现必须用同一发布版行为基准回归，不能以“新 API 更合理”替代发布行为；
3. 上游升级后的工程必须重新验证 Xray 播放、播放器、TV 网络恢复和上游原有功能；
4. 编译成功、静态比较、JVM 测试、APK assemble 和真机运行属于不同证据级别，不能互相冒充。

已经发生的上游升级或实验性模块接线，不自动代表前一项已验收。

## 最终验收

项目长期目标至少包括：

- faithful 源码和主要发布行为完成对照；
- 非 Git 二进制依赖来源可复现并有固定校验；
- v7 faithful APK 可重现构建；
- v7 关键 Android TV 真机回归完成；
- v8 构建 / ABI / 关键逻辑核验完成；
- Xray 正式模块化并通过同一行为基准；
- TV 网络恢复在模块化和上游升级后仍有效；
- 至少完成一次真实 FongMi 上游升级验证；
- 文档和仓库状态足以让新的维护者不依赖历史聊天继续工作。

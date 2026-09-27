# FingMi-Xray

FingMi-Xray 是基于 FongMi/TV 的 Android TV 二次开发项目。

当前仓库正处于 **源码恢复与后续重构阶段**。已发布的 `v5.6.0-xray.5` 原始开发源码曾丢失，因此当前工作不是直接在现有代码上继续堆功能，而是先以正式发布 APK、固定 FongMi/TV 5.6.0 上游源码和原始产品规格为依据，恢复一套可维护、可验证的 faithful 基准，再完成模块化重构。

## 项目核心

项目长期保留两项能力，优先级如下：

1. **Xray 当前播放会话代理**
   - 不创建 Android 系统 VPN；
   - 不代理整台设备；
   - 只在用户手动开启后服务当前点播或直播播放会话；
   - 切集、切台、换源、换地址、换播放器、结束播放或离开播放页面后，不自动继承上一会话的 Xray 状态；
   - Xray Core 运行于独立 `:xray` 进程，并在会话结束时收口网络与 native / Go Runtime 资源。

2. **Android TV 长后台 / 待机后的网络恢复**
   - 处理部分电视 Fast Start、长后台或待机恢复后继续复用失效 Socket、DNS / DoH 或网络环境的问题；
   - 这是 app / catvod 的网络生命周期能力，**不属于 Xray 模块本身**。

发布版的完整产品说明已冻结在：

- [docs/ORIGINAL_README.md](docs/ORIGINAL_README.md)

该文件是 `v5.6.0-xray.5` 的原始产品规格依据，不再跟随后续重构修改。

## 当前阶段

当前工作按下面顺序推进：

1. **Faithful recovery**
   - 以正式发布 APK 的实际行为为最高运行时证据；
   - 以 FongMi/TV 5.6.0 固定源码作为可读基线；
   - 修正 JADX / R8 反编译损坏；
   - 恢复 Xray、播放器接线、设置、安全、Binder / Service 生命周期和 TV 网络恢复；
   - 恢复并验证缺失的播放器、FFmpeg JNI 与 libXray 二进制依赖。

2. **Faithful build 与设备回归**
   - 先完成静态和依赖门；
   - 再构建可复现的 TV faithful APK；
   - armeabi-v7a 是主要运行基线，要求完整设备回归；
   - arm64-v8a 用于编译、ABI 和关键逻辑交叉验证。

3. **模块化重构**
   - 当前 `:xray` 模块是迁移目标，但不是发布版行为的真相来源；
   - 以恢复完成的 faithful 实现为基准逐块迁移；
   - FongMi app 只保留必要的 VOD、Live、Player、Settings 和生命周期适配点；
   - TV 待机网络恢复继续留在 app / catvod。

4. **真实上游升级验证**
   - 模块化完成后，实际升级一次较新的 FongMi 上游；
   - 用真实升级验证 Xray 不再需要重新散落修改大量上游业务文件。

## 当前状态

截至当前恢复阶段：

- v7 / v8 正式 APK 身份及 SHA-256 已固定；
- v7 为实际使用和主要恢复基准，v8 用于交叉验证；
- Xray / Binder / Service / 分享链接 / 证书安全 / 播放网络 / TV 待机恢复的大量行为已经完成静态 APK / DEX 对照；
- 当前普通 app 已依赖实验性 `:xray` 模块，但播放器侧 Xray 会话与媒体网络接线仍未完成正式迁移；
- faithful 构建所需的播放器 AAR、FFmpeg JNI、libXray Go JNI 等已经建立严格的来源与哈希校验流程；
- 当前 5.6.3 `main` 已在 GitHub Actions 完成 Leanback / Mobile 双 flavor Debug javac 与 APK assemble，并同时产出 v7 / arm64 APK；这证明当前工程构建链已经闭环，但不等于原 `v5.6.0-xray.5` faithful 基准或设备行为已经验收；
- **仍不能宣称 faithful recovery 已完成或 Android TV 真机回归已完成**；
- 正式模块迁移和较新 FongMi 上游升级仍在后续阶段。

准确进度和剩余门槛以恢复文档为准，不以历史聊天中的经验百分比作为验收标准。

## 文档

项目的人维护文档统一放在 `docs/`：

- `docs/ORIGINAL_README.md`  
  冻结的 `v5.6.0-xray.5` 原始产品规格。

- `docs/PROJECT.md`  
  项目长期目标、产品边界、最终架构方向和验收原则。

- `docs/RECOVERY.md`  
  源码丢失后的恢复基准、当前恢复状态、APK / DEX 证据、已确认偏差、依赖恢复、构建与设备验证门槛。恢复阶段的唯一主文档。

- `docs/DEVELOPMENT.md`  
  后续开发、模块化迁移、上游适配、工程工作规则和当前开发状态。恢复完成后主要维护此文档。

- `docs/apk-reference/`  
  与本项目恢复直接相关的 v7 / v8 反编译源码、Manifest、哈希和差异摘要。类映射与恢复结论统一维护在 `docs/RECOVERY.md`。这里不保存原始 APK、DEX、AAR、SO 等大型二进制。

开始恢复工作前先读 `docs/RECOVERY.md`；开始重构或开发工作前先读 `docs/DEVELOPMENT.md`。

## 证据优先级

发生冲突时按以下顺序判断：

1. 已固定 SHA-256 的正式发布 APK 实际行为；
2. `docs/ORIGINAL_README.md` 的原始产品意图；
3. 固定 FongMi/TV 5.6.0 上游源码；
4. JADX / DEX 等反编译证据；
5. 当前恢复代码或实验性模块。

JADX 输出只是证据，不应在明显控制流损坏时直接作为最终语义。

## 构建说明

当前仓库仍处于恢复阶段。2026-09-27 的 current-main build 已成功完成 5.6.3 Leanback / Mobile Debug compile + assemble，但这只证明当前工程可构建；原 `v5.6.0-xray.5` faithful 基准、正式签名与真机回归仍按 `RECOVERY.md` 的门槛执行。构建结论必须绑定具体 commit / run / hash，不能只凭工作流存在或历史红灯/绿灯推断恢复完成。

具体依赖门、构建状态和允许执行的流程请查看：

- `docs/RECOVERY.md`
- `docs/DEVELOPMENT.md`

## License

FongMi/TV、XTLS/libXray、Xray-core 以及项目使用的其他第三方开源代码分别遵循各自许可证。项目许可证见 [LICENSE.md](LICENSE.md)。

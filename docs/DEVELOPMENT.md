# FingMi-Xray 开发与维护文档

本文是项目后续开发、模块化迁移、上游适配和工程协作的唯一主文档。

恢复发布版源码本身的事实、证据、进度和剩余门槛统一写在 [RECOVERY.md](RECOVERY.md)。长期产品目标与边界见 [PROJECT.md](PROJECT.md)。不要把同一结论同时复制到多个文档。

## 当前开发阶段

当前仍处于 **faithful recovery 优先阶段**。

现有普通工程已经包含 `:xray` Android library，`app` 也已经依赖它，但这不代表模块化迁移完成：

- 实验性 `:xray` 中已有配置、Service、Binder、session、安全和网络基础类；
- 多处实验实现已经根据恢复层静态对齐；
- 普通 app 的播放器主链路仍没有完成正式 Xray 会话和媒体网络接线；
- faithful 基准尚未完成整套 APK 构建与设备回归；
- 因此不能以实验模块代替 `recovery/legacy-src/` 的恢复真相。

正式迁移必须等恢复门达到 [PROJECT.md](PROJECT.md) 定义的阶段顺序。

## 工程边界

### `:xray`

目标职责：

- libXray bridge；
- 分享链接归一化和 runtime config；
- 证书安全和节点持久化；
- 独立 `:xray` Service；
- AIDL / Binder；
- operation generation；
- playback session 状态机；
- SOCKS HTTP / socket 资源；
- 通用公开目的地防护；
- 节点测试控制。

模块不得直接拥有：

- FongMi `VideoActivity` / `LiveActivity`；
- 上游 `PlayerManager`；
- FongMi 首页或 Spider 生命周期；
- TV 长后台 / 待机网络恢复。

### app

目标职责：

- VOD / Live 当前播放身份；
- Xray 开关和会话触发；
- 播放器切换；
- Exo / MPV 接线；
- DRM / RTSP / subtitle / danmaku / artwork / download 等媒体旁路；
- 设置 UI、手机导入 UI；
- 上游 FongMi 与 Xray facade 的最小适配。

### catvod / app network

继续负责：

- 普通 API client；
- DNS / DoH；
- Spider；
- TV 前后台 / 待机网络代际与恢复。

这条能力是项目第二核心功能，但不迁入 Xray 模块。

## 当前普通工程状态

截至 2026-09-26 的已知状态：

- `settings.gradle` 已包含 `:xray`；
- `app/build.gradle` 已 `implementation project(':xray')`；
- `xray` library Manifest 声明独立 `:xray` Service；
- 普通 Leanback app 有 Xray 设置入口；
- 实验模块的分享链接、证书、Service、Binder、session 和网络基础类已经接受多轮 faithful 静态对齐；
- 普通 `PlayerManager`、播放器 factory/session、`PlaybackService`、`VideoActivity` 和 `LiveActivity` 的完整 Xray 播放接线尚未正式迁移；
- 普通 app 的 TV 网络恢复链已经有一部分 faithful 接线，但仍需 Android 编译和设备验证。

更精确的恢复状态和证据不要在这里重复，统一看 [RECOVERY.md](RECOVERY.md)。

## 工作规则

以下规则适用于 Chat、Work、Codex 或其他后续 AI / 开发者。

### 1. 仓库当前 `main` 是工程状态真相

聊天历史、旧会话总结、模型记忆和旧文档只能作为线索。

开始工作时：

1. 先读取最新 `main`；
2. 读取本文件和对应阶段主文档；
3. 查看最近相关提交；
4. 再决定是否需要重新阅读具体代码。

如果其他 AI 已经推进工程，不得用旧上下文覆盖新结果。

### 2. 修改后立即落库，不积压

无论改动发生在本地容器、Codex、Work、GitHub API 或其他环境：

> **确定的代码或工程改动完成后，应尽快提交 / 上传到 `main`，随后立即更新对应主文档。**

推荐原子流程：

1. 核实证据或需求；
2. 修改一个清晰问题范围；
3. 运行该范围必要的静态 / 单元检查；
4. 提交代码或工程文件；
5. 更新 `RECOVERY.md` 或 `DEVELOPMENT.md`；
6. 提交文档；
7. 再开始下一项。

不要长期保留只存在于临时容器或聊天上下文中的“已完成工作”。

目的：

- 防止会话中断后丢失状态；
- 防止新 AI 重复阅读和重新推理已经解决的问题；
- 防止不同 AI 同时工作时互相覆盖；
- 让 Git 历史和主文档能够直接接手。

### 3. 不要批量积压几十个修改后一次上传

大型批量修改会：

- 增加冲突；
- 降低证据可追踪性；
- 让会话中断恢复困难；
- 让下一位接手者难以判断每项变化的依据。

可以在同一提交中修改强相关的少量文件，但每个提交应有明确单一目的。

### 4. 文档不是流水账

主文档记录：

- 当前有效结论；
- 结论依据；
- 已验证范围；
- 未验证范围；
- 当前阻塞；
- 下一步。

主文档**不记录**：

- “先看了 A，再看了 B”；
- 没产生结论的搜索过程；
- 每几分钟一次的时间线；
- 已经被后续结论覆盖的中间猜测；
- 同一事实在多个文档里的重复副本。

Git commit history 已经承担时间线职责。

### 5. 一个事实只维护一个主要位置

- 产品目标 / 长期边界 → `PROJECT.md`
- 发布版恢复事实 / 证据 / 门槛 → `RECOVERY.md`
- 开发 / 模块迁移 / 上游适配 / 工程工作规则 → `DEVELOPMENT.md`
- 原始发布产品说明 → `ORIGINAL_README.md`
- 可复核的反编译材料 → `apk-reference/`

必要时可以链接，不要复制整段。

### 6. 恢复阶段先修 faithful，再修实验模块

如果发现发布 APK 与 `recovery/legacy-src/` 有确证偏差：

1. 先修 faithful 层；
2. 在 `RECOVERY.md` 写清证据和验证级别；
3. faithful 结论稳定后，才评估是否同步实验 `:xray`；
4. 实验模块的差异写在本文件，不反过来定义发布版行为。

### 7. 不把静态验证写成运行验证

文档必须区分：

- 源码静态比较；
- DEX 指令确认；
- JVM / Python 单元测试；
- Gradle 编译；
- APK 构建；
- Android TV 真机测试。

例如：

- “54 个精选方法签名匹配”不能写成“播放器 AAR 完全兼容”；
- “workflow 配置完成”不能写成“依赖已经恢复”；
- “JADX 步骤成功”不能写成“整个 Action run 成功”；
- “编译成功”不能写成“发布版行为一致”。

## GitHub Actions / AC 规则

### 默认不运行

除非项目所有者明确授权，**不得启动新的 GitHub Actions / AC run**。

即使 workflow 已存在、看起来只需要几分钟，也不能把“配置好”视为“允许执行”。

### 必须保持手动触发

恢复、构建和分析 workflow 默认保持：

`workflow_dispatch`

不应为了方便临时加入 `push`、`pull_request`、`schedule` 等自动触发。

如果确有必要改变触发方式，应先取得项目所有者明确同意。

### 修改 workflow 与执行 workflow 是两个权限

可以在静态审查范围内修 workflow，但：

- 提交 workflow 修改 ≠ 获准运行；
- workflow YAML 校验通过 ≠ 实际依赖恢复成功；
- 历史 run 成功 ≠ 当前新 run 可以免授权启动。

### 优先本地和已保存证据

能够使用以下方式完成的工作，不使用 AC：

- 仓库已保存的 APK reference；
- GitHub 静态读取；
- 本地 Java / Python / shell 检查；
- 已保存的固定哈希、反编译材料和脚本；
- 已存在且可信的构建产物。

### Faithful APK build

整套 faithful APK 编译在恢复阶段属于明确里程碑。

运行前应：

1. 确认当前静态门和依赖门状态；
2. 说明本次编译能验证什么；
3. 取得项目所有者明确允许；
4. 只运行对应的手动 workflow 或本地构建。

## Git 规则

- 只维护 `main`，除非项目所有者以后明确改变策略；
- 不依赖未提交的本地 scratch 作为持久状态；
- 不提交原始发布 APK、DEX、AAR、SO 等大型二进制到普通 Git 历史；
- 大型发布材料以固定 SHA-256、来源和可重新获取方式记录；
- 与本项目恢复直接相关的反编译文本证据放入 `docs/apk-reference/`。

## 文档维护规则

新增或更新代码后：

- 恢复 / faithful 相关 → 更新 `RECOVERY.md`；
- 模块开发 / 普通 app / 重构 / 上游升级 → 更新 `DEVELOPMENT.md`；
- 产品目标发生变化 → 更新 `PROJECT.md`；
- 不因为每次小工作建立新的 `*_AUDIT_YYYY-MM-DD.md` 或 `SESSION_*.md`。

当旧专项文档内容已完整吸收进主文档后，应删除旧文件，不保留只写“已迁移”的空壳。

## 接手顺序

### 继续恢复

1. 根 `README.md`
2. `docs/PROJECT.md`
3. `docs/RECOVERY.md`
4. 最近相关提交
5. 需要处理的具体源码 / reference

### 继续重构或普通开发

1. 根 `README.md`
2. `docs/PROJECT.md`
3. `docs/DEVELOPMENT.md`
4. 如涉及发布版行为，再查 `docs/RECOVERY.md`
5. 最近相关提交和具体代码

目标是让接手者**不需要重新完整阅读整个仓库才能知道已经做过什么**；只有在要修改某个具体范围时，才深入读取对应代码。

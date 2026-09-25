# FingMi-Xray 恢复与重构交接日志

**换会话从这里读起。** 按时间追加有证据的进展，同时更新「当前状态」和「下一步」。这里记录的是工程状态，不把静态检查当作编译或设备验证。

快速导航：产品需求 `PROJECT_REQUIREMENTS.md`；阶段进度 `PROGRESS.md`；调试与修复 `DEBUG_HISTORY.md`；APK 行为对照 `README_APK_BEHAVIOR_MATRIX.md`。本日志记录每轮实际动作和可接手的任务。

## 项目目标与边界

- 仓库：`rileyaaa/FingMi-Xray`，只维护 `main`；恢复丢失的 `v5.6.0-xray.5` 源码，再把 Xray 从 FongMi 5.6.0 的改动中拆成独立模块和少量适配点，便于日后跟进上游。
- 行为证据顺序：已发布 APK（首选 armeabi-v7a；arm64-v8a 交叉核对）→ 最初的 `README.md` 产品意图 → 当前恢复代码。README 包含手动开启且只作用于当前媒体播放、VOD/直播各自会话、切集/台/源/地址/播放器时重置、独立 `:xray` 进程、节点导入/测试、电视待机网络恢复等要求。
- 待机网络/DNS/DoH 恢复属于 app 自身，不应误迁入 Xray 模块。`recovery/legacy-src/` 是发布版行为基准；现在的 `xray/` 和正常 `app/` 尚未完成迁移，不能替代基准。
- 用户希望先做彻底的静态恢复核对，再尝试编译；可在本地具备环境和依赖时编译。2026-09-25 用户另给 **两次无需再问的机会**；记录为最多两次必要的 AC/Actions 尝试额度，仍应先说明验证目标、确认源码与依赖就绪，且每实际启动一次才扣一次。此前要求节省 Actions 额度。未消耗：**2/2**。

## 当前状态（2026-09-25）

- 发布 APK：v7 SHA-256 `cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda`；v8 SHA-256 `b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d`。固定上游 FongMi/TV commit `1a19fee278fa2234da725d61a53bf59b69fe9127`，libXray `v26.7.28`。
- 静态恢复：`recovery/legacy-src/upstream/` 覆盖 51 文件（其中 `app/src` 46 文件）；另有 24 个 Xray Java 和 2 个 AIDL。`docs/recovery/README_APK_BEHAVIOR_MATRIX.md`、`LEGACY_BEHAVIOR_FREEZE.md`、`DEEP_AUDIT_2026-09-25.md` 记录逐项证据。v7 完整 JADX 已取回，对重要类与 v8 逐项对照；修复了数据源 `open` 失败后 `close` 清理顺序。
- 用 `FINGMI_LEGACY_SOURCE_ONLY=1` 可只组装上游加恢复覆盖层；已核对覆盖文件逐字节一致，未运行 Gradle。静态导入和 Xray 资源名检查通过；**方法签名、生成的 view binding、完整 Gradle 依赖、运行行为未核完**，不能称已彻底还原。
- 本地目前只有 Java 17 JRE，无 Android SDK、Gradle 缓存。FongMi 将自制播放器 `lib-*.aar` 排除在 Git 外；所附 5 个 `*-release.aar` 未提供 `androidx.media3.mpvplayer` 等所需类；libXray AAR 也尚未完整下载。仅启动 Actions 不能解决缺失的播放器 AAR。
- 历史 Actions 的 v7 完整 JADX 工件 `10847466987`；v7/v8 DEX 工件 `10847337361`；历史 v8 JADX `10825963688`。此前红灯原因是反编译后处理，不等同于 JADX 失败。工件 ID 仅作溯源；本地 scratch 随会话可能丢失。

## 2026-09-25 本次进展

已推送至 `main`：`3ac6223d74c0f5577c46f8f3b3ae22834d499224`（交接日志、恢复文档和本地 AAR 组装入口）。

1. 重查发布版 `nq0` → `C1872zo` → `uc0` 的 DRM 路径：Xray 会话为 DRM license HTTP 单独设置 `DataSource.Factory`。Media3 官方 `DefaultDrmSessionManagerProvider.setDrmHttpDataSourceFactory` 参数正是 `DataSource.Factory`，因此恢复代码这里没有先前怀疑的参数类型错误；没有做无依据的 DRM 改写。发布版的 `nq0.mo615e` 空实现也与恢复层保持一致。
2. 对照发布版 `or2`、`jz3` 与恢复的 `LegacyXraySchemeGuardDataSource`：允许的 8 种 scheme、空白 scheme、失败时 cleanup 顺序均已覆盖；此轮未发现新的实证偏差。
3. `prepare-legacy-faithful.sh` 现在把仓库本地 `app/libs/lib-*.aar`（如果开发者提供）复制到临时组装树。此前仅覆盖 Git 内文件，这些被上游 `.gitignore` 忽略的播放器依赖不会进入忠实编译目录。
4. 本日志承接每次会话的工作。旧的 `SESSION_2026-09-25.md` 只有一句概要；后续应将新增结论、阻塞、实际 AC 消耗和提交号持续写在此处。
5. `bash -n scripts/prepare-legacy-faithful.sh` 和 `git diff --check` 通过。准备以本地临时 AAR 验证完整组装时，shell 到 `github.com` 的 DNS 被环境限制，`git fetch` 在复制阶段之前失败；临时探针已清理。因此本轮没有宣称组装脚本通过端到端验证，也未运行编译或 Actions。
6. 增加仓库根目录 `AGENTS.md`，指向此日志和行为矩阵，让新会话先取到准确状态。复查 `pz3` 与 `LegacyXrayHttpResources` 的 SOCKS 未解析地址、连接池、独立 dispatcher 和网络拦截器初始化，未发现新的实证偏差。

## 2026-09-25 续接（子源重申目标）

已推送至远端 `main`：`4bb3550aa5ca56a9817e87e851bac221137baa94`（需求、修复史、进度、离线组装和播放器依赖早停）。工作区的本地提交由另一写入通道生成，提交 SHA 与远端不同，但逐字节内容产生的 Git tree `5102fc7b46e16978279bbe3d56748c719a560444` 已核对一致；接续工作以远端 `main` 为基线。

- 用户明确要持续保存需求、完整上下文、开发调试、bug 修复、阶段进度，并更新到项目 Markdown；重申源码丢失后的忠实恢复与 Xray 独立重构，优先本地编译，缺环境可借 AC，仍希望在足够核对后再编译。
- 已新增 `PROJECT_REQUIREMENTS.md`、`DEBUG_HISTORY.md` 和 `PROGRESS.md`，按原始 README、前两个会话可查证的决策、Git 历史及当前源码记录；勿将历史经验百分比当成验收结论。
- 发现工作区还保留固定上游 `1a19fee...` 的 Git 对象。组装脚本支持 `FINGMI_LEGACY_UPSTREAM_GIT_DIR` 离线 archive 固定提交；实测 source-only 组装，逐字节核对 51 个覆盖文件、24 个 Java、2 个 AIDL，以及一份临时模拟的本地 `lib-*.aar`，均通过。临时 AAR 已清理，**没有下载正式播放器/libXray AAR、没有运行 Gradle、没有触发 Actions**。两次免询问机会仍为 **2/2**。
- 官方 FongMi README 说明播放器配套 `lib-*.aar` 不纳入 Git。Actions 并不会自带这些二进制；先找与固定 5.6.0 配套的正确来源，或确定可复现构建方法，再安排有意义的编译。
- 新增 `scripts/check-faithful-player-aars.py`，`build-legacy-faithful.sh` 在下载 libXray / 拉上游 / 运行 Gradle 前执行。实测现有 5 个 AAR 的内嵌 `classes.jar` 都不含 `MpvPlayer`、`DecodeTrackSelector`、`MediaSourceFactorySupplier`；预检以退出码 1 报具体缺类，构建入口也确实提前退出。通过预检仅代表代表性类存在，并非全部 ABI/方法签名兼容。

## 下一步

1. 持续对照 APK 核验剩余 API 方法签名、资源绑定、媒体播放会话和节点兼容；发现偏差时先修 faithful 层并附字节码定位。阶段进度见 `PROGRESS.md`。
2. 查明与 FongMi 5.6.0 匹配的播放器 AAR 来源和准确版本，核验所需类，勿用未知第三方二进制碰运气；准备好 libXray、JDK/SDK、Gradle 后先本地 faithful 编译。
3. 基准可编译且行为验证后，将 Xray 核心收束至独立模块，app 仅保留 VOD/直播/播放器与设置的适配点，做同一份行为矩阵回归。

## 每次交接应更新

追加日期、`main` 提交号、变更和证据、实际编译/设备验证结果（或明确未做）、未解决问题、接下来最可执行的任务，以及剩余免询问 AC 次数。产品需求改动同步更新 `PROJECT_REQUIREMENTS.md`，修复写 `DEBUG_HISTORY.md`，阶段变化更新 `PROGRESS.md`。不要把本地 scratch 路径当作持久位置。

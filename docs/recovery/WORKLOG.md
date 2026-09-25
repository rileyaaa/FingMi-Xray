# FingMi-Xray 恢复与重构交接日志

**换会话从这里读起。** 按时间追加有证据的进展，同时更新「当前状态」和「下一步」。这里记录的是工程状态，不把静态检查当作编译或设备验证。

快速导航：产品需求 `PROJECT_REQUIREMENTS.md`；阶段进度 `PROGRESS.md`；调试与修复 `DEBUG_HISTORY.md`；APK 行为对照 `README_APK_BEHAVIOR_MATRIX.md`。本日志记录每轮实际动作和可接手的任务。

## 项目目标与边界

- 仓库：`rileyaaa/FingMi-Xray`，只维护 `main`；恢复丢失的 `v5.6.0-xray.5` 源码，再把 Xray 从 FongMi 5.6.0 的改动中拆成独立模块和少量适配点，便于日后跟进上游。
- 行为证据顺序：已发布 APK（首选 armeabi-v7a；arm64-v8a 交叉核对）→ 最初的 `README.md` 产品意图 → 当前恢复代码。README 包含手动开启且只作用于当前媒体播放、VOD/直播各自会话、切集/台/源/地址/播放器时重置、独立 `:xray` 进程、节点导入/测试、电视待机网络恢复等要求。
- 待机网络/DNS/DoH 恢复属于 app 自身，不应误迁入 Xray 模块。`recovery/legacy-src/` 是发布版行为基准；现在的 `xray/` 和正常 `app/` 尚未完成迁移，不能替代基准。
- 用户希望先做彻底的静态恢复核对，再尝试编译整套 APK；依赖 AAR 可先用 AC 编译并拉回核验，本地具备环境时优先本地编译。2026-09-25 用户另给 **两次无需再问的 AC 机会**，均已实际运行；截至本日志最新记录剩余 **0/2**；第三轮在随后明确指示下运行成功。此前要求节省 Actions 额度，未来运行仍须明确用途。

## 当前状态（2026-09-25）

- 发布 APK：v7 SHA-256 `cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda`；v8 SHA-256 `b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d`。固定上游 FongMi/TV commit `1a19fee278fa2234da725d61a53bf59b69fe9127`，libXray `v26.7.28`。
- 静态恢复：`recovery/legacy-src/upstream/` 覆盖 51 文件（其中 `app/src` 46 文件）；另有 24 个 Xray Java 和 2 个 AIDL。`docs/recovery/README_APK_BEHAVIOR_MATRIX.md`、`LEGACY_BEHAVIOR_FREEZE.md`、`DEEP_AUDIT_2026-09-25.md` 记录逐项证据。v7 完整 JADX 已取回，对重要类与 v8 逐项对照；修复了数据源 `open` 失败后 `close` 清理顺序。
- 用 `FINGMI_LEGACY_SOURCE_ONLY=1` 可只组装上游加恢复覆盖层；已核对覆盖文件逐字节一致，未运行 Gradle。静态导入和 Xray 资源名检查通过；**方法签名、生成的 view binding、完整 Gradle 依赖、运行行为未核完**，不能称已彻底还原。
- 本地目前只有 Java 17 JRE，无 Android SDK、Gradle 缓存。FongMi 将自制播放器 `lib-*.aar` 排除在 Git 外；原有 5 个 `*-release.aar` 未提供所需 Media3/mpv 类。AC 第三轮已取回 16 个官方源码构建的候选 AAR，外层 ZIP 已持久保存并可用仓库脚本验证/导入 `app/libs/`；`libXray.aar` 尚未完整下载；候选 AAR 的 12 类/50 项精选 Java 方法签名已核；每个 ABI 的 11 件候选播放器 `.so` 中十件与已校验发布 APK 的历史清单同 SHA，仅 `libffmpegJNI.so` 不同。手动 JNI 修复工作流已备而未运行；libXray AAR、完整 Java ABI 和忠实 APK 编译仍待核验。
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

## 2026-09-25 续接（核心优先级与 AC 编译 AAR）

- 子源确认前一轮的 Markdown 已在远端项目，要求 Work/Chat 任何修改均持续写项目记录。明确核心目标优先级：**Xray 功能第一；部分电视长期后台/待机网络恢复第二**。已写入 `PROJECT_REQUIREMENTS.md`。
- 子源明确 AC 用来**编译播放器 AAR**，编译后拉回项目；因此先做独立的播放器依赖构建，不把 AAR 的编译混同于整套 APK faithful 完成。
- 在 FongMi 官方 `media` 仓库发现 `release-1.11.0-fongmi` 分支的三个所需类源码；固定候选提交 `3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`（2026-08-12），而已固定 FongMi/TV 5.6.0 上游提交日期为 2026-08-07。新工作流 `.github/workflows/recovery-player-aars.yml` 从固定源码编译 Media3/mpv AAR、保存 SHA-256 清单与产物，属于**待核验版本兼容的候选**。FongMi 当前官方 README 仍说明 `lib-*.aar` 未纳入 Git；其 `MpvLibrary` 还加载 `mpv`/`player` 原生库。AC 实际运行、工件 ID、错误、剩余免询问次数要在运行后记录；未开始前仍为 **2/2**。
- 已实际运行第一轮 AC：`36123159162`，对应远端 `main` 提交 `e18c30397e7d48b8db8275dc89299c923a8d633e`；源码 checkout 与 JDK21 成功，`android-actions/setup-android@v3` 在安装旧 SDK `tools` 包时失败（`Failed to find package 'tools'`），**没有执行 Gradle，没有生成 AAR**。运行虽失败但已使用一次免询问机会，剩余 **1/2**。修复：使用 runner 现有 SDK cmdline-tools 安装 platform36，移除该 setup action；下一轮再验证实际编译。
- v7 发布 APK 的 `mr0` 内可见 `AndroidXMedia3/1.11.0`，与官方候选分支的 Media3 `1.11.0` 基本版本相符；**这不足以证明 2026-08-12 的源码完全兼容 2026-08-07 发布版的定制 ABI**，拉回 AAR 后仍需接口与原生库核验。
- 第二轮 AC `36123459832` 对应远端 `main` 提交 `1b2ba0227a2b30b2da134bd5e5891ad60fd0121d`。**两次免询问机会均已实际启动，剩余 0/2**；勿未经授权开启第三轮。
- 第二轮最终结果：`36123459832` 的 `Compile upstream player libraries` **BUILD SUCCESSFUL in 4m 15s（484 个任务）**；随后清单脚本只查 `libraries/*/build/outputs/aar/`，但上游使用 `buildout/outputs/aar/`，故找不到编出的 AAR，工件未包含 AAR，工作流总体为 failure。真实问题是**后处理找错路径**，不是源码编译失败。工作流已改查 `buildout` 并移除 push 触发，防止自动花掉第三次；后续如需重跑，需要新的用户授权。
- 工件路径修复已额外按上游 `build.gradle.kts` 明确传入 `-PexternalBuildDir=buildout`，固定到仓库根目录 `buildout/lib-*/outputs/aar/`；同时支持模块本地输出路径、检查同名 AAR 冲突。此修正只做静态核对，尚未在 AC 复跑。项目根目录 `AGENTS.md` 指向本日志；**以后每次 Work 或 Chat 改动工程都同步更新 `WORKLOG.md`，涉及需求、排错或阶段变化时同步对应 Markdown，并上传到仓库 `main`**。
- 用 PyYAML 解析工作流确认仅 `workflow_dispatch`；在本地临时目录伪造一个符合 `buildout/lib-mpvplayer/outputs/aar/` 的 AAR，执行工作流原样清单脚本，验证能收集 AAR、列出三种目标类并写 SHA-256 清单。这只验证收集脚本，不等于真实候选 AAR 的类和 ABI 核验。
- 已将上述修复和项目记录推送到远端 `main` 提交 `59e699627bf1880317134749c6844958296bee07`，其 Git tree 与本地 `d70396c5ddc4609a08e90594bc8dcd0681f1ba79` 一致。用户随后再次明确 AC 用于编译 AAR 并要求继续工作，本轮据此授权再次运行修正的 AAR 工作流。暂时重新开启仅工作流文件路径的 push 触发，运行结束立即移除并把实际工件、验证范围与错误更新在本日志中；**本次授权只用于 AAR 收集，不代表整套 APK 已恢复完成**。
- 第三轮 AC 已启动，运行号 `36124817040`，输入提交 `2bc84cdbf82f2f5ce1b29c2f81522c5daed00891`；等待编译、收集和实际工件核验。独立静态检查发现待机网络恢复链路 `BaseLoader.clear(Runnable)` 缺少 `App` 导入，已补 `com.fongmi.android.tv.App`，证据和编译验证边界见 `DEBUG_HISTORY.md`。
- 第三轮 AC `36124817040` **全部步骤成功**，取回工件 `10859533459`：16 个由固定 `FongMi/media@3c2cbe8...` 编译的 AAR，外层 ZIP SHA-256 `0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee`；每个 AAR 与清单 SHA-256 一致，三个此前缺失的代表类在真实 `classes.jar` 中存在。候选 AAR 已导入本地项目 `app/libs/`，连同现有 5 个 AAR 的预检通过（21 个文件）。因上游忽略 `app/libs/lib-*.aar`，项目 Git 只提交验证清单及 `scripts/import-player-aar-candidate.py`，完整原始 ZIP 另保存为可跨会话取回的 `/FongMi-Xray/FingMi-media3-player-AARs-1.11.0-candidate.zip`；在新会话取得该 ZIP 后运行 `python3 scripts/import-player-aar-candidate.py /path/to/ZIP` 即可安全复原本地 `app/libs/`。Actions 原工件 2026-10-09 到期。AAR 虽已编出，仍需核其全部 Java 方法/原生 ABI 和 APK 静态恢复，**没有编译整套 APK、没有设备回归**。本轮恢复阶段 AC 实际运行三次；最初的两次免询问机会已耗尽，本次来自用户随后明确的继续编译指示。
- 清理用于本轮的工作流 `push` 触发，保留 `workflow_dispatch`；后续仅在有明确需求时手动构建。未来所有 Work/Chat 会话均按根目录 `AGENTS.md` 持续更新工程和 Markdown，并上传 `main`。
- 以保存的真实工件实测 `scripts/import-player-aar-candidate.py` 和类预检；又用固定 FongMi/TV Git 对象离线执行 source-only faithful 组装，逐字节核对本地 21 个 AAR 全部进入临时组装树。**没有运行 Gradle**；源码缺失的完整方法/资源核验、`libXray.aar` 与真正 APK 编译仍在后续。
- 从已有 v7 JADX 完整工件的 `resources/lib/armeabi-v7a/` 发现 `libmpv.so`、`libplayer.so` 及其 FFmpeg 依赖，`readelf -d` 验证 `libplayer` 依赖 `libmpv`、`libavcodec`、`libswscale` 等。新增 `scripts/extract-v7-player-native.py`，可接受原发布 APK（先核总 SHA-256）或已有 JADX ZIP（逐个核 10 个原生库 SHA-256），只向显式 `--to` 目录导出这十个 v7 播放器原生库；已用现存 JADX 工件实测全部通过。未把提取的二进制文件提交至 Git，也未运行 app 编译。

## 下一步

1. 持续对照 APK 核验剩余 API 方法签名、资源绑定、媒体播放会话和节点兼容；发现偏差时先修 faithful 层并附字节码定位。阶段进度见 `PROGRESS.md`。
2. 从保存的候选包用 `scripts/import-player-aar-candidate.py` 还原本地依赖；v7 十个原生库和 38 项精选 Java 签名已核，下一步扩大到完整 Java/资源联合核查；准备好 libXray、JDK/SDK、Gradle 后在静态恢复核对充分的基础上编译 faithful APK。
3. 基准可编译且行为验证后，将 Xray 核心收束至独立模块，app 仅保留 VOD/直播/播放器与设置的适配点，做同一份行为矩阵回归。

## 每次交接应更新

追加日期、`main` 提交号、变更和证据、实际编译/设备验证结果（或明确未做）、未解决问题、接下来最可执行的任务，以及剩余免询问 AC 次数。产品需求改动同步更新 `PROJECT_REQUIREMENTS.md`，修复写 `DEBUG_HISTORY.md`，阶段变化更新 `PROGRESS.md`。不要把本地 scratch 路径当作持久位置。

## 2026-09-25 续接（候选 AAR 静态 ABI 实证）

- 用户问是否停止并要求继续：上一轮最终回复后确实没有后台持续任务，本轮重新开始工作。会话本地 scratch 已清空，未把临时文件当作仓库丢失；远端 `main` 原 SHA `303f121bf64d730f0784c592df6689562e497426` 可读。上轮持久保存的 44,336,768 字节 AAR 候选包已重新取回并以原 ZIP SHA-256 验证。固定 FongMi/TV Git 对象和 JADX ZIP 本轮未恢复，本轮也未执行 Gradle。
- 新增 `scripts/check-player-native-against-v7.py`，从现有 `extract-v7-player-native.py` 读取已核的发布版十个原生库 SHA-256；对候选 `lib-mpvplayer-release.aar` 与 `lib-decoder-ffmpeg-release.aar` 内 `jni/armeabi-v7a/` 逐文件对照，**10/10 完全同 SHA-256**，其中 `libmpv.so`、`libplayer.so`、FFmpeg 七件和 `libc++_shared.so`。额外 `.so` 尚未据此证明。脚本实测通过。
- 新增 `scripts/check-player-java-api.py`，解析 AAR 的真实 `classes.jar` Java class 方法表，对固定 FongMi/TV 5.6.0 使用的八个播放器类核 38 项公开方法的精确 JVM 描述符；**38/38 匹配**，坏 class 头负例也被拒。详情和限制见 `PLAYER_AAR_ABI_2026-09-25.md`。这只是选取接口和 v7 十个原生库，不等于完整兼容、faithful APK 已编译或设备通过。
- 本轮无新的 AC/Actions 运行；最初免询问额度剩余 0/2，第三轮已按用户随后明确指示完成。下一步继续 Xray 优先的忠实恢复、待机网络恢复复查，补齐 libXray 与构建条件后再考虑 faithful APK 编译；独立模块重构仍未开始正式迁移。

## 2026-09-25 续接（Xray 与待机网络的原始 DEX 再核）

- 用户要求继续推进约一小时，并在北京时间约 20:50 暂停供其检查额度；工作期间持续把记录写入项目。本节为本轮第一处可交接检查点。没有开启新的 AC/Actions；最初两次免询问机会仍为 0/2。
- 重新取回已保存的发布版 v7 完整 JADX 工件 `10847466987` 和 v7/v8 原始 DEX 工件 `10847337361`。`l61` 首页网络检查在重新排队后，原始 DEX 以 `goto` 直接返回；`yd0` 旧 OkHttp 客户端依次 cancelAll、evictAll、shutdown。恢复实现与两者一致，不依据易误读的 JADX 伪代码制造改动。Xray `vz3` 的 stop/start 超时分别为 1500/30000 ms；初核 `yz3` 会话和 XrayService 独立进程销毁路径与恢复层关键点一致。逐项 DEX 定位、结论和未覆盖边界见 `XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`。
- 接续任务：深入查 Binder 掉线/回调及会话竞态，优先有原始字节码证据的偏差；其次扩大候选 AAR Java/资源检查。本轮目前仍无 libXray AAR、APK 编译或设备验证，不能宣称恢复完成。
- 继续逐条核 `hz3`、`ez3`、`dz3`、`uz3`：绑定超时、死亡/断线事件、旧回调代际检查、Binder 1–6 操作分发与恢复层静态一致。新建 `scripts/inspect-published-dex.py` 直接定位 v7/v8 原始 DEX 指令，对 `XrayService.b` 两次 `outbounds` 数量判断分别证实 null 和 length≠1 均跳错误分支，排除 JADX 错误的 `!= null ||` 伪代码；细节写入 `XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`。工具已通过 Python 语法检查并在双 ABI 工件实际运行；它不是完整反汇编器。无代码语义改动、无 AC 或 APK 编译。
- 补核第二目标：发布版 `gn3`、`HomeActivity.m1976O0`、`l61` 和 Spider 清理 Runnable 与恢复的 `TvNetworkLifecycle`、Home、`OkHttp`/`OkDns`、`BaseLoader` 对上：只卸载普通 API 客户端，不卸载播放器客户端；Spider 清理完成才轮询；连续两次互联网能力或最多 12 次、每次 500ms 后继续刷新。仍欠电视长待机实测。具体见 `XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`。
- 取得发布版 v8 历史 JADX 工件 `10825963688`（本次 ZIP SHA-256 `8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b`），其 arm64-v8a 中十个核心播放器 `.so` 与保存的候选 AAR 逐文件 SHA-256 **10/10 相同**。新增 `check-player-native-against-v8.py` 并实测通过；内存篡改其中 `libplayer.so` 的负例被拒。v8 此项以历史 JADX 工件为来源，尚待固定 SHA 的原始 v8 APK 独立复核；详情更新 `PLAYER_AAR_ABI_2026-09-25.md` 与 `PROGRESS.md`。无新 AC/整套 APK 编译。
- 结合原始 README 与恢复层 23 个 legacy Java 文件的 import，新增 `XRAY_MODULE_BOUNDARY_2026-09-25.md`：20 个无直接 FongMi app 类依赖的核心候选 + 原 service/AIDL 计划移入独立 Android library；3 个播放器/直播场景类留 app 适配，Home/OkDns/OkHttp/Spider 待机恢复仍留 app/catvod。明确必须先完成 faithful 编译与行为回归，再迁移；本轮仅设计边界，`xray/` 实验模块尚未替换基准。
- 对照原始 v7 DEX `XrayService.e` 与 `onDestroy`，直接定位 compareAndSet 代际门、失效、killProcess，以及销毁时 stop→shutdown→等待 3 秒→kill 的指令序列，记录在 `XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`。注意这仍是静态证明。对比实验性 `xray/` 与 faithful 的 AIDL：六个方法形状相同，但 Binder descriptor 包名 `com.fingmi.xray.service` 与发布版 `com.fongmi.android.tv.xray` 不同，已将迁移约束写入 `XRAY_MODULE_BOUNDARY_2026-09-25.md`。
- 当前执行环境复查仍只有 OpenJDK 17，无 `gradle`/`sdkmanager`/Android SDK；不为确认已知环境缺口盲跑 APK 编译。原两次免询问 Actions 已用尽，后续 AC 仍需明确授权；此轮未使用。
- 扩大候选原生核验后发现**实证阻塞**：`lib-decoder-ffmpeg-release.aar` 的第十一件 `libffmpegJNI.so` 在 v7/v8 两 ABI 均与历史发布版 JADX 原生库 SHA-256 不同；而 `FfmpegLibrary.class` 确实引用该 JNI。`readelf -Ws` 显示公开导出集合 v7 783/v8 781 各自相同，但 `.text` 和 `.rodata` 哈希也不同，不能称候选 JNI 等价。新增 `check-player-ffmpegjni-against-published.py`，真实候选执行退出 1；不掩盖为仅十件通过。详细 hash、来源限制和修正路径见 `PLAYER_AAR_ABI_2026-09-25.md`。这使 faithful APK 的二进制门槛仍未过，未开启 AC/编译。
- 继续原始 DEX 对照：Xray Hysteria2/TLS 证书探测在指纹格式不符时抛错，后续新值小写化但旧存储 pin 按 ASCII 原样做恒时比较；以及 STOP 失败消息送达主进程与无法送达时分别由主进程/服务取消精确操作，见 `XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`。这些匹配恢复层，未引入推测性改动。
- 将第十一件 JNI 严格核验接入 `scripts/build-legacy-faithful.sh` 的已存在播放器类预检之后、上游源码准备/Gradle 之前。`bash -n` 通过，针对真实候选 JNI 的独立脚本按预期返回 1；未在当前缺 SDK/Gradle 的机器运行整套构建入口。尝试从固定 tag 的原始 arm64 APK 做只读 HTTP HEAD，当前 shell 到 github.com 10 秒超时，故 v8 仍只有历史 JADX 工件的来源链，不谎称独立原 APK 复核。详细约束见 `PLAYER_AAR_ABI_2026-09-25.md`。
- 新增 `scripts/restore-published-ffmpegjni.py` 作为未来从**原始**双 ABI 发布 APK 修复 decoder AAR 的安全入口：分别核 APK 总 SHA/原 JNI SHA 和候选 ZIP SHA，只重包两 ABI 对应 JNI，核其他 AAR ZIP 条目逐字节不变，并拒绝覆盖已有目标。Python 语法检查通过；把历史 JADX ZIP 错当 APK 输入的负例正确拒绝且未输出文件。当前没有可用原 APK（shell 到 github.com 超时），故尚未实测成功替换，未修改本地 `app/libs` 或运行 faithful APK 编译。说明与后续命令见 `PLAYER_AAR_ABI_2026-09-25.md`。
- 给 `restore-published-ffmpegjni.py` 增加纯 Python 假 APK/AAR 正向回归 `recovery/legacy-tests/test_restore_ffmpegjni.py`。首次实测发现 `ZipFile.writestr` 会修改原始 `ZipInfo` 的 CRC/size，导致重包后用同一 ZipInfo 读源文件时触发 `Bad CRC-32`；已改写入 `copy(info)`，并惰性读取未替换 entry。回归随后 1/1 通过（两 JNI 替换且 classes.jar 不变）。这仍不是原 APK 或 Gradle 验证。现在到用户约定暂停时间前继续归档状态，不新跑 AC。

## 2026-09-25 一小时工作检查点（北京时间约 20:50 暂停）

- 本轮截至检查点的远端 `main` 为 `c5db33bccee5b1186fb4e6c86eb97cfc95ac8b9b`；依次提交原 DEX 的 Xray/待机网络证据、双 ABI 原生库对照、模块边界设计、FFmpeg JNI 阻塞及安全重包/回归脚本。以下检查点自身提交号以远端 `main` 最新值为准。
- **最重要的待处理阻塞**：候选 AAR 的 `libffmpegJNI.so` 两个 ABI 都与发布版不同；`build-legacy-faithful.sh` 的早停门会拒绝它。脚本 `restore-published-ffmpegjni.py` 已有假包成功路径与错误来源负例，但没有原始 v7/v8 APK，尚未在真实包上运行。不能跳过它宣称 faithful APK 已编译。
- 下一轮从本文件和 `PLAYER_AAR_ABI_2026-09-25.md`、`XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`、`XRAY_MODULE_BOUNDARY_2026-09-25.md` 接手。先获取两份原始发布 APK，并以固定总 SHA 核验；在此之前**不要**对历史 JADX ZIP 当原 APK 重包。取得后运行重包脚本到全新路径，确认新 AAR 的 FFmpeg JNI 双 ABI SHA、其他条目不变，再决定如何导入本地 `app/libs`。之后仍需 libXray AAR、完整 Java/资源检查、faithful APK 编译及电视设备回归；过门后才开始正式模块迁移。
- 一小时内未启动新的 AC/Actions；最初两个免询问机会仍为 0/2。当前执行环境仅有 JDK 17，无 Android SDK/Gradle，因此没有声称本地 Android 编译。按用户约定暂停，等其检查额度后再续。


## 2026-09-25 续接（发布版 JNI 的导入闭环准备）

- 子源要求继续工作，并按每轮约一小时暂停供其核额度。本轮先确认远端 `main` 原有检查点 `e3e026aefb6e7059a1e3a966b054efa109bbaa58`。原始发布 APK 的 GitHub Release 两个资产分别为 v7 `534791937`（129,871,795 字节）、v8 `534791583`（145,354,377 字节）；当前 shell 对原 Release URL 不可用，现有下载通道未取得原 APK。没有把历史 JADX ZIP 当 APK，也没有运行 AC 或 faithful APK 编译。
- `scripts/import-player-aar-candidate.py` 新增可选 `--restored-decoder /path/to/new-lib-decoder-ffmpeg-release.aar`。导入前仍严格核固定候选 ZIP/清单和 16 个原始 AAR；若提供替换的 decoder AAR，检查 ZIP entry 顺序/数量无变化、两个 JNI 的 SHA-256 等于发布版记录、其余每个条目的内容与候选逐字节相同。所有验证结束后才写本地 `app/libs/`。默认不提供参数的导入行为维持原样，默认候选仍会被构建前 JNI 门拒绝。此参数不能代替从固定 SHA 原始 APK 执行 `restore-published-ffmpegjni.py` 的来源核验。
- 新增 `recovery/legacy-tests/test_import_restored_decoder.py`：纯 Python 假包正例通过，非 JNI Java 字节码篡改、错误 JNI、额外条目均被拒。原有 `test_restore_ffmpegjni.py` 再跑 1/1 通过，导入核验测试 1/1 通过；Python 语法检查通过。**这不是对真实发布 APK 或真实候选 AAR 的端到端重包/导入验证。**
- 下一步仍优先取原始 v7/v8 APK，核固定总 SHA，再执行真实重包、校验/导入。其后补 libXray AAR、完整接口/资源检查与 faithful APK 编译。独立 Xray 模块正式迁移仍须经过基准编译和关键行为回归。
- 本轮另从历史双 ABI APK 清单工件 `10847337361` 遍历候选 16 件 AAR 的所有 `jni/{ABI}/*.so`：每个 ABI 各 11 件，10 件匹配、1 件 `libffmpegJNI.so` 不匹配、无额外未对照的候选播放器 `.so`。清单生成前的工作流已核发布 APK 总 SHA，但本轮仍未取得独立原 APK；该结果未解除 JNI 阻塞。详情见 `PLAYER_AAR_ABI_2026-09-25.md`。
- 使用真实的 44,336,768 字节候选 ZIP 再核总 SHA `0ed42581...` 与 16 件 AAR；把未经修复的候选 decoder 当 `--restored-decoder` 传入新导入器，预期被 v8 JNI 哈希拒绝（退出码 2），导入前停止。这是真实候选的负向验证，正向真实替换仍需原 APK。
- 静态 ViewBinding 名称核对：从恢复覆盖层六个 TV Activity (`Push/Home/Video/SettingXray/Live/Setting`) 提取 `mBinding.*` 共 77 个实际引用字段，对应布局优先选恢复覆盖 XML、没有覆盖时选固定仓库已有 XML；将 Android ID 的 snake_case 映射成 ViewBinding camelCase 后，六个布局均无缺名字段（3/6/24/7/9/28）。此检查仅证实字段名和 ID，尚未运行 Android ViewBinding 生成、Java 字段类型或资源合并验证。

## 2026-09-25 续接（本轮获准写入 main）

- 子源北京时间 21:22 明确授权将上轮已准备的改动推送 `main`，并从该时刻重新计一小时工作。上轮自动审批曾拒绝推进默认分支，收到这次明确授权后，远端 `main` 已快进至 `8bf5bc228dedf3f390512ac5a8d4ce282b63acf1`，含安全导入器、假包正反例、完整候选原生条目清点和 77 个 ViewBinding 名称静态核对；远端 ref 已验证。
- 继续以恢复层播放接线及固定上游 `ExoUtil` 为依据，扩大候选 AAR Java 接口检查：从 8 类/38 项扩至 12 类/50 项精确 JVM 描述符。真实固定候选 ZIP 上脚本通过；新增预加载和 FongMi 定制渲染入口。仍为精选签名，无 Android SDK/Gradle 编译和设备验收，双 ABI 的 FFmpeg JNI 差异未解决。
- 已准备仅 `workflow_dispatch` 的 `.github/workflows/recovery-restore-ffmpegjni.yml`，不含 push/schedule：Actions runner 下载发布 v7/v8 原 APK和已核的播放器候选工件，逐份 SHA-256 检查后调用现有重包脚本；再通过 JNI 门，仅上传新 decoder AAR、固定官方 libXray AAR 与哈希清单，不上传约 275 MB 原 APK。该流程还**未运行**，因此不声称已有真实修复包；本轮没有新增 AC 消耗。YAML 静态解析确认只允许手动触发、只授予 contents/actions read、五步含两件 AAR 非空门；真实 Actions 下载与产物仍待获准运行后验证。
- 对候选 `DefaultPreloadManager.class` 额外解析 class 文件 `super_class`，确认为 `BasePreloadManager`；这与新增六个继承调用签名相互印证，仍不等于整套 Java 编译。
- 已合并 libXray 下载到同一条待手动触发的准备工作流：调用项目既有 `fetch-libxray.sh` 核官方 v26.7.28 ZIP 的固定 SHA，提取 AAR、核非空并记录 AAR SHA；节省未来单独一次下载依赖的 Actions 运行。YAML 静态核查为五步且无自动触发；**尚未真正下载或编译**，任何失败不得记作依赖齐备。
- 同一手动工作流在官方 libXray ZIP 哈希校验后还静态核 `libXray.LibXray.invoke(String):String` 的 class 描述符，以及两 ABI 的 `libgojni.so` 条目；避免取回“包名相似但主入口或 v7 native 缺失”的 AAR。该新门仅检查存在和签名，**未证实原生内容与发布 APK 同字节，工作流仍未运行**。官方 v26.7.28 GitHub Release 所报 `libxray-android.zip` SHA 与 `fetch-libxray.sh` 固定值相同。
- 对照已按发布版恢复的 `LegacyXraySessionController`/`LegacyXrayServiceClient` 和尚未接入的实验性 `xray/`，发现三处可证实漂移并局部修正实验模块：旧 STOP 超时时新 START 已 RUNNING 应跳过 cancel/disconnect；当前 STOP 成功应断开 Binder；START 成功结果后仍要保留 active operation ID，以便 Binder 后续死亡能报告给会话并清理状态。另对齐当前连接失败时的旧 cleanup timeout 清除。改动只在实验性 `xray/` 模块，faithful 基准未动；以源码控制流静态对照，未编译/设备回归，**不能把这记成正式模块迁移完成**。详细风险见 `DEBUG_HISTORY.md` 与 `XRAY_MODULE_BOUNDARY_2026-09-25.md`。

- 本轮继续比较实验性 `xray/` 的分享链接归一化器与双 ABI DEX 已校正的恢复类，发现 Hysteria2 参数/编码/默认端口顺序及 VMess fragment 处理漂移。将实验类代码对齐恢复类，仅替换包和类名；规范化后逐字节一致。`XRAY_MODULE_BOUNDARY_2026-09-25.md` 留存限制；仍未编译、运行或正式迁移。未开启新的 Actions。
- 继续静态对照实验模块 `XrayService`：修正 VALIDATE/TEST 端口分配及配置创建的重试作用域，START/STOP 无法投递时用带精确 ID 的 cancel 门防止旧操作直接杀死新会话，线程 daemon 设置同发布恢复层。`XrayShareLinkSecurity` 修复旧存储 pin 的大小写比较、WebSocket SNI 后备键的精确匹配、IPv6 地址筛选；其他传输安全查询重写仍有差异，已记模块边界。未编译、未跑设备。
- 核 `XrayConfigFactory` 与发布版恢复类：单出口、私网黑洞、DNS 服务器、SOCKS 入站规则的常量和顺序静态吻合；补齐证书安全处理后的第二次归一化。传输安全类原有较多查询重写偏差，现以已核 DEX 的恢复类实现为基准，适配模块包/类及 bridge 的 JSONArray 参数；规范化适配后的源码逐字节一致。仍有实验配置额外的端口早停与 AIDL descriptor 等门槛。无新 Actions、Java 编译或电视设备回归。
- 对照证书存储发现实验类原先静默吞掉迁移异常、重置时双存储与密钥清理顺序不同；已将 `XrayCertificatePins` 适配为恢复层 `LegacyXrayCertificateStore` 同实现，`XrayService.resetSecurityInternal` 改按原版调用 `resetAll(this)` 并重建依赖。仅静态核对；原始 APK 字节码的结论及后续模块测试门槛见模块边界文档。无新 AC。
- 比较 `LibXrayBridge` 与恢复的 `LegacyLibXrayApi`：实验桥原先宽容接受字符串或空对象，且在 `invoke`/ping 阶段 trim/去敏错误；发布版要求 JSONObject，并以 `Character.isWhitespace` 按代码点判断空错。已定点修正，保留在外层回调去敏以免改变绑定失败判断。只做源代码静态对照，仍无真实 libXray AAR 或 Android 构建。
- 核服务回调的错误去敏与代际门：实验代际门算法与恢复层相同；实验去敏器此前漏掉 JSON 引号敏感值处理及 1024 字符上限。现用恢复层去敏实现适配模块类名，并保留旧的 Throwable 兼容入口；服务异常调用 `fromException`。仅源码静态检查，未运行模块。

# 静态恢复、调试与修复记录

查问题时先读 `WORKLOG.md` 的最新状态，再读此文件的对应问题。这里记录已证实的修复与当前风险；每条需要有发布版证据、对应代码或提交，并明确验证级别。所有条目截至 2026-09-25，尚未完成 faithful 编译和设备验证。

| 问题 / 风险 | APK / 调试证据及处理 | 提交或代码位置 | 验证级别 |
| --- | --- | --- | --- |
| Xray 媒体复用直连 Exo 缓存，可能绕开会话代理 | APK `nq0` 在 port>0 时使用直连上游和 scheme guard；恢复层绕开普通磁盘缓存。 | `7b7261c`、`ExoMediaSourceFactory` | APK 静态对照 |
| DRM license 请求走普通网络 | `nq0` 为 Xray 会话安装单独的 DRM DataSource；恢复层用同一个代理和 scheme guard。`DefaultDrmSessionManagerProvider` 的 `DataSource.Factory` 类型已核对，先前的类型疑问被排除。 | `764773b`、`ExoMediaSourceFactory` | APK + Media3 API 静态对照 |
| Xray 数据源错误回退 / 失败后不清理 | APK `or2` 和 `jz3` 仅允许 8 种 scheme 与空白 scheme；`open` 在委托前置 `opened=true`，保证委托抛错后 `close` 仍关闭资源。 | `797a7f3`、`0c82399`、`ff58feb`、`LegacyXraySchemeGuardDataSource` | v7/v8 APK 静态对照 |
| RTSP 经 SOCKS 丢域名或空白 User-Agent | APK使用 unresolved hostname 的 socket factory，检查 Unicode whitespace 后才设置 UA。 | `fd2ea8c`、`LegacyXrayProxySocketFactory`、`ExoMediaSourceFactory` | APK 静态对照 |
| Hysteria2 端口跳跃条件被 JADX 反转 | v7/v8 原始 DEX 验证：authority 端口包含 `,` **或** `-` 才重写；其他条件也以 DEX 核实。 | `bb4572f`、`e61e0ed`、`49fbd4f`、`LegacyXrayShareLinkNormalizer` | 双 ABI DEX 核对 |
| 节点安全 / 显示存在细节漂移 | ALPN JSON 解析、证书 pin 原样大小写、错误信息空白兜底分别对照发布版修复。 | `eb2eb7a`、`3d79878`、`74a4ef4` | APK 静态对照 |
| 侧网络流量与播放身份不一致 | DRM、字幕、弹幕、下载及当前播放器请求与会话代理切换同步；防止旧的请求对象跨会话。 | `764773b`、`c7684b4`、`1be4e65`、`3fe6bcb`、`eaba37c` | APK 静态对照，设备待验 |
| 播放切换、封面及 DLNA 生命周期 | VOD/Live 结束旧会话、Glide 封面保护、待机网络与 DLNA 代际按 APK 整理。 | `c5fd977`、`318e4dc`、`01daff6`、`b4319f7` | APK 静态对照，设备待验 |
| 清理线程和连接池行为 | 发布版 `pz3` 使用独立 SOCKS OkHttp/dispatcher/pool；恢复层核对异步 cancel/evict 与 daemon 清理线程。 | `bfab3c8`、`LegacyXrayHttpResources` | APK 静态对照 |
| 恢复组装依赖网络，且漏带忽略的播放器 AAR | 固定上游 Git 对象可离线 archive；`app/libs/lib-*.aar` 必须从本地传入临时工作目录。离线完整组装 51 覆盖文件、24 Java、2 AIDL 和临时 AAR 均逐字节一致。 | `scripts/prepare-legacy-faithful.sh`；2026-09-25 本轮 | 实际离线组装通过；无编译 |
| 缺播放器二进制时浪费构建时间/Actions | 扫描现有 5 个 AAR 的 `classes.jar`，均无 `MpvPlayer`、`DecodeTrackSelector`、`MediaSourceFactorySupplier`。构建入口增加缺类预检，实测在下载依赖/Gradle 之前退出；预检不能保证完整 ABI 一致。 | `scripts/check-faithful-player-aars.py`、`build-legacy-faithful.sh`；2026-09-25 本轮 | 预检和早停已执行；未编译 |

## AC / 构建排错说明

- 过去 v7 JADX 的 Actions 显示红灯，失败发生在反编译后的结果筛选；JADX 的完整输出已保存为工件 `10847466987`。因此历史红灯不表示没有取到源码。v7/v8 DEX 工件为 `10847337361`，历史 v8 JADX 为 `10825963688`。
- `6e3daad` 的标题含 “faithful build artifact”，代表构建工作流和产物上传步骤相关改动，**不能从提交标题推断 APK 已编译成功**。目前未拿到一份通过完整依赖和设备回归的 faithful APK。
- 上游官方说明 `lib-*.aar` 播放器依赖不入 Git；已有 5 个 `*-release.aar` 不提供所需 Media3/mpv 类。AC 可以提供 SDK/JDK 环境，但若未解决二进制依赖，直接再次构建只会重现缺依赖，不能凭空生成兼容的 AAR。
- 后续查到 **FongMi/media** 的 `release-1.11.0-fongmi` 分支确实包含 `MpvPlayer`、`DecodeTrackSelector` 和 `MediaSourceFactorySupplier` 源码；已固定目前分支提交 `3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`（2026-08-12），距离 FongMi/TV 5.6.0 固定源码提交（2026-08-07）约五天。`recovery-player-aars.yml` 用 AC 编译这些候选 AAR。它们是否与 **2026-08-07 发布版 ABI** 完全兼容尚未证明，且 `MpvLibrary` 另需 `mpv`、`player` 原生库；不能只看三个类存在就宣布依赖解决。
- 第一轮 AC `36123159162`（2026-09-25）在 `android-actions/setup-android@v3` 中执行 `sdkmanager tools` 失败：`Failed to find package 'tools'`；Gradle 阶段被跳过，上传的工件 `10858679185` 仅有空清单，没有任何 AAR。已删除该 action 的调用，改用 runner 已安装的 SDK cmdline-tools；本次消耗一次机会。发布 APK `mr0` 的版本字符串为 `AndroidXMedia3/1.11.0`，与待编译分支基本版本吻合。
- 第二轮 AC `36123459832` 已进入 Media3 Gradle 编译阶段，编译结果见下一条；两次免询问机会已耗尽。v7 JADX 工件仍包含 10 个原始播放器/FFmpeg 原生库，`extract-v7-player-native.py` 对各文件的 SHA-256 实证核验通过；这为后续 v7 运行依赖提供可复现的提取路径，尚未完成 Java AAR 与原生库的 ABI 验证。
- 第二轮 `36123459832` 的真实结果：固定 FongMi/media 源码 **484 个 Gradle 任务全部通过，BUILD SUCCESSFUL in 4m 15s**。工作流红灯来自工件脚本误用 `libraries/*/build/outputs/aar`，上游实际可按 `-PexternalBuildDir=buildout` 明确输出到仓库根 `buildout/lib-*/outputs/aar/`。上传的只有空清单，AAR 没有被拉回。已更正检索路径、显式固定输出目录，同时关掉 push 自动触发；修正尚待运行验证，第三次运行须另行授权。
- 在本地合成 `buildout/lib-mpvplayer/outputs/aar/lib-mpvplayer-release.aar`（含 `classes.jar` 的三个占位类），直接跑修正的清单脚本，确认路径扫描、复制、哈希和三类检测成功；实际 Gradle 输出与真实方法签名仍须从下一轮 AAR 工件核实。
- 静态检查待机恢复链路时发现 `BaseLoader.clear(Runnable)` 新增了 `App.post(onComplete)`，却没有 `com.fongmi.android.tv.App` 导入；同包没有 `App` 定义，会造成 Java 未解析符号。已补导入。依据源码包名与现存其他引用校核；尚未运行 Android 编译。
- 第三轮 `36124817040` 成功，工件 `10859533459` 中 16 个 AAR 逐项 SHA-256 与构建清单一致；`lib-mpvplayer-release.aar`、`lib-exoplayer-release.aar` 中检出三种代表类；导入项目本地忽略的 `app/libs/` 后预检 21 个 AAR 通过。外层 ZIP SHA-256 `0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee`，已另外持久保存；新增导入脚本验证总 hash、清单和所有文件 hash，避免新会话误拿错 AAR。方法签名、完整 ABI 和整套 APK 构建仍未验证。
- 用真实工件执行导入脚本、预检和 `FINGMI_LEGACY_SOURCE_ONLY=1` 的离线组装，核对 21 个 AAR 在 `app/libs/` 与组装工作树中 SHA-256 逐个一致。组装成功不等同于 Android 编译。
- 本地有固定上游的 Git 对象时，可用 `FINGMI_LEGACY_UPSTREAM_GIT_DIR=/path/to/pinned/object-store FINGMI_LEGACY_SOURCE_ONLY=1 FINGMI_LEGACY_WORK_DIR=/tmp/faithful-review bash scripts/prepare-legacy-faithful.sh`。此模式不下载 libXray、不执行 Gradle。

- 2026-09-25 候选 AAR ABI 续查：从持久保存的真实工件重新核 SHA-256，并用 `check-player-native-against-v7.py` 读取既有发布版 APK 证据，对 10 个 v7 播放器 `.so` 全部核得字节完全相同；用 `check-player-java-api.py` 对固定 TV 5.6.0 使用的八个播放器类核 38 个公开方法精确 JVM 描述符全部通过。此结果消除了十份原生库的具体版本疑虑，但只覆盖精选 Java 接口，完整 API/运行逻辑、libXray 和 APK 编译/设备仍待查；未新跑 AC。细节见 `PLAYER_AAR_ABI_2026-09-25.md`。

## 后续调试记录格式

每次写：日期；症状/触发条件；发布 APK、原 README 或运行日志证据；根因；改动文件和 `main` 提交；已执行的静态/编译/设备检查；尚未验证的风险。不要把反编译工具的推断记成确认的运行行为。

- 2026-09-25 原始 DEX 纠偏记录：v7 `Ll61;->run` 在 post 下一轮检查之后有 `goto` 直达 `return-void`，避免把 JADX 展示的 fallthrough 误判为首页提前加载；v7 `Lyd0;->run` 可直接核到 `cancelAll`→`evictAll`→`shutdown`。当前 faithful 恢复代码与这两点吻合，无需改写；Xray `vz3` 的 1500/30000 ms 亦与现有会话控制器一致。详见 `XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`，验证级别仍是静态 DEX 对照，非编译/设备验证。
- 2026-09-25 双 ABI 配置条件复核：发布版 `XrayService.b` 的 v7/v8 原始 DEX 中 `0x6a9`/`0x712` 检查空数组，`0x6b0`/`0x719` 检查数量不为 1，均跳异常分支。恢复的 `LegacyXrayRuntimeConfigFactory` 两处 `outbounds == null || length != 1` 正确；JADX 这里出现错误的 `!= null ||` 与空分支。已新增 `scripts/inspect-published-dex.py` 使可复核，证据见 `XRAY_NETWORK_DEX_AUDIT_2026-09-25.md`。静态双 ABI 实证，无设备验证。
- 2026-09-25 播放器原生依赖跨 ABI 排错：之前仅 v7 核对，现取回历史 v8 JADX 工件 `10825963688`，对十件 arm64-v8a `.so` 核得候选 AAR 逐字节同 SHA-256，篡改负例拒绝。脚本 `check-player-native-against-v8.py` 与 `PLAYER_AAR_ABI_2026-09-25.md` 保存清单和命令；v8 工件尚非独立验证总 SHA 的原 APK，完整 Java ABI 与设备仍未测。
- 2026-09-25 **新确认的二进制阻塞**：第十一件 FFmpeg JNI 的 v7 候选/发布 SHA 分别为 `93cc400a...`/`3af1fcaa...`，v8 为 `10f8fc54...`/`26594d57...`；导出符号集合相同不代表 `.text`/`.rodata` 一致。候选 `FfmpegLibrary.class` 引用 `ffmpegJNI`。新负向门 `check-player-ffmpegjni-against-published.py` 对真实候选退出 1。修复尚未进行；应先从发布 APK 严格取原二进制、定位正确的 Gradle 替换方式并复验，不能直接宣布 faithful 构建。完整值见 `PLAYER_AAR_ABI_2026-09-25.md`。
- 2026-09-25 FFmpeg JNI 重包脚本自测修复：合成 APK/AAR 的正向测试首次失败 `Bad CRC-32`；根因是 `ZipFile.writestr(info, ...)` 修改原 ZIP `ZipInfo`，之后 `source.read()` 使用已变动 CRC。改用 `copy(info)` 并避免 `dict.get` 默认参数的急切读取后，`test_restore_ffmpegjni.py` 1/1 通过。仅假包算法测试，真实固定哈希 APK 尚未到手。

- 2026-09-25 decoder AAR 导入阶段的完整性风险：直接覆盖 `app/libs/lib-decoder-ffmpeg-release.aar` 可能把不相关的 Java 或 native 代码一并改掉。导入器现支持可选的双 ABI 发布 JNI 替换包，逐条目核其余内容不变且两 JNI 等于记录哈希，校验全部 16 个原始 AAR 后才写入。假包测试覆盖成功、Java 篡改、错误 JNI、额外条目；未取得原 APK，真实来源链与 Android 编译仍待验证。
- 2026-09-25 实验模块会话/Binder 漂移（不影响尚未替换的 faithful 基准）：`XraySessionController.onCleanupTimeout()` 原先即使新 START 已 RUNNING 仍取消旧 STOP，`XrayServiceClient.cancel()` 会断开正在使用的 Binder；`onResult(STOP success)` 缺少断连分支；`XrayServiceClient.deliverResult()` 在 START 成功后清除 `activeOperationId`，之后服务进程死亡时 `failLocked()` 无 operation ID 可报告，界面可能继续认为 RUNNING。按已核发布版恢复层的相应控制流修正以上三处，并清理当前连接失败的旧 cleanup timer。仅做源码静态对照，Android 编译、设备、模块完整行为未验；原 AIDL descriptor 仍与发布版不同，不能直接替换。

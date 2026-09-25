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
- 本地有固定上游的 Git 对象时，可用 `FINGMI_LEGACY_UPSTREAM_GIT_DIR=/path/to/pinned/object-store FINGMI_LEGACY_SOURCE_ONLY=1 FINGMI_LEGACY_WORK_DIR=/tmp/faithful-review bash scripts/prepare-legacy-faithful.sh`。此模式不下载 libXray、不执行 Gradle。

## 后续调试记录格式

每次写：日期；症状/触发条件；发布 APK、原 README 或运行日志证据；根因；改动文件和 `main` 提交；已执行的静态/编译/设备检查；尚未验证的风险。不要把反编译工具的推断记成确认的运行行为。

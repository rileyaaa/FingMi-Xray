# v5.6.0-xray.5 APK 证据索引

本目录只保存 `v5.6.0-xray.5` 正式 APK 中**适合直接进入 Git、并且对发布版恢复有长期价值的文本证据**。

这里不是维护源码，也不记录恢复进度。faithful 实现与恢复方法见 [../RECOVERY.md](../RECOVERY.md)。

## 1. 固定 APK 身份

| ABI | 文件 | SHA-256 |
| --- | --- | --- |
| armeabi-v7a | `FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk` | `cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda` |
| arm64-v8a | `FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk` | `b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d` |

使用本目录证据前，应先确认分析对象与上述 SHA-256 一致。

原始 APK、完整 `classes*.dex`、AAR、SO 和完整 JADX 输出不进入普通 Git 历史；需要重新生成时使用手动 `recovery-apk-analysis.yml` 和对应脚本。

## 2. 目录内容

### `shared/sources/`

从两份 APK 的完整 JADX 输出中筛选出的恢复相关 Java 文本，主要覆盖：

- Xray Service / Binder / session；
- 分享链接、runtime config、证书与错误去敏；
- PlayerManager / Exo / SOCKS / destination guard；
- VOD / Live / Settings / Push；
- libXray Java bridge 数据类；
- TV 待机网络恢复相关 R8 类。

selected source 共 64 个：

- v7 / arm64 逐字节相同：63；
- ABI 间有差异：1；
- 缺失：0。

唯一 selected-source 差异为 `p000/ip0.java`，因此分别保存在：

- `v7/ip0.java`
- `v8/ip0.java`

该类是 R8 生成的 EventBus subscriber index；注册内容相同，差异仅在生成代码顺序。

### `shared/AndroidManifest.xml`

两份 APK 对照后的 Manifest 文本。selected 对照中两 ABI 的 Manifest 一致。

### `shared/dex-sha256.txt`

记录两份 APK 中 DEX 文件的 SHA-256，用于判断分析输入和 ABI 差异。

### `shared/apk-diff.txt`

正式 APK ZIP entry 级差异摘要。

### `shared/source-parity.txt`

selected source 的 v7 / arm64 对照结果。

### `native-share-symbols.json`

正式 libXray Go JNI 中与 share conversion / Invoke 等恢复工作有关的 symbol、源码行信息和地址索引。

native 的动态行为 fixture 不放在本目录，见：

- `../../recovery/native-tests/`
- `../../recovery/v2rayn-tests/`
- `../../recovery/node-dns-tests/`
- `../../recovery/libxray/`

## 3. 常用 R8 / JADX 映射

反编译类名是发布 APK 的导航标记，不是长期源码 API。

| JADX / R8 名 | 主要责任 | faithful 可读实现 |
| --- | --- | --- |
| `yz3` | playback session / generation / timeout | `LegacyXraySessionController` |
| `hz3` | Service bind / Binder death | `LegacyXrayServiceClient` |
| `rz3` | operation result | `LegacyXrayOperationResult` |
| `lz3` | operation id | `LegacyXrayOperationIds` |
| `pz3` | SOCKS OkHttp resources | `LegacyXrayHttpResources` |
| `oz3` | RTSP SOCKS SocketFactory | `LegacyXrayProxySocketFactory` |
| `qz3` | public destination guard | `LegacyPublicPlaybackDestinationInterceptor` |
| `lu2` | encrypted share-link store | `LegacyXrayConfigStore` |
| `a04` | share-link normalizer | `LegacyXrayShareLinkNormalizer` |
| `kz3` | error redaction | `LegacyXrayErrorSanitizer` |
| `uz3` | IXrayService Binder | `XrayService` |
| `th2` | PlayerManager / proxy transition | faithful `PlayerManager` |
| `nq0` | Exo MediaSource factory | faithful `ExoMediaSourceFactory` |
| `or2` | Xray scheme guard DataSource | `LegacyXraySchemeGuardDataSource` |

具体发布语义以 [../RECOVERY.md](../RECOVERY.md) 和对应测试为准。

## 4. 使用方法

1. 先核 APK SHA-256。
2. 查发布 Java 结构时，优先从本目录 selected source 定位。
3. JADX 控制流明显不可信时，不要自行“修合理”，继续查 DEX、双 ABI 或 native 实际行为。
4. R8 短类名只用于对应发布 APK，不应出现在新模块 API 设计中。
5. 不直接复制未经核对的 JADX 作为维护源码。
6. 大型二进制和完整反编译输出不提交到 Git。
7. 新增证据时只保存能长期帮助复核的最小文本材料；调试日志和一次性中间文件留在 artifact / 本地工作目录。

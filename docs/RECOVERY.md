# v5.6.0-xray.5 历史发布版恢复档案

本文记录 `v5.6.0-xray.5` 的**历史证据对象、证据来源、faithful 源码结构、二进制来源和可重复恢复方法**。

> **定位**：当前 `main` 决定现行源码、模块架构与上游版本。本文件固定 `v5.6.0-xray.5` 的历史事实、native provenance 和 Xray 黄金行为证据。`main` 不回退到旧 faithful 架构，但 Xray 外部行为应在已取证范围内与 v7 黄金参考等价。

它不是开发日志，也不记录当前开发分支的上游升级过程。当前工程见 [DEVELOPMENT.md](DEVELOPMENT.md)，AI 协作与非流水账文档维护规则见 [AI_COLLABORATION.md](AI_COLLABORATION.md)，原发布时的用户说明见 [ORIGINAL_README.md](ORIGINAL_README.md)。

## 1. 历史恢复对象

恢复对象固定为：

- FingMi-Xray：`v5.6.0-xray.5`
- FongMi/TV：`5.6.0`
- faithful `versionCode`：`56005`
- libXray / Xray-core：`v26.7.28`

正式 APK：

| ABI | 文件 | SHA-256 |
| --- | --- | --- |
| armeabi-v7a | `FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk` | `cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda` |
| arm64-v8a | `FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk` | `b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d` |

固定 FongMi/TV 上游：

- commit：`1a19fee278fa2234da725d61a53bf59b69fe9127`

固定官方 libXray：

- tag：`v26.7.28`
- commit：`80263da83e96b2972455b0a94b13ee1a10e51391`
- Android ZIP SHA-256：`28b7dc9d6cc8455fcca5cbd56e387003a7bfb558128651a64899dc3a8ccff666`
- 官方 `libXray.aar` SHA-256：`4708a361a74f7e955635dbe3661cefb459bdc867423c3b1826a2c5a6ea4ac77d`

本归档中的 faithful 结论都以这些固定输入为前提。v7 正式 APK 的 Xray 行为可作为 current parity 的黄金 oracle；旧版 FongMi 架构、混淆结构和 faithful APK 重建流程本身不是 `main` 的发布要求。

## 2. 证据优先级

恢复目标是“尽可能忠实地解释并重现已发布 APK”，不是把反编译代码润色成更合理的新实现。

出现冲突时按以下顺序处理：

1. 已固定 SHA-256 的正式 APK；
2. APK 中的 DEX / ELF / JNI 实际行为；
3. 冻结的原发布说明；
4. 固定的 FongMi/TV 5.6.0 上游；
5. JADX 等反编译文本；
6. 可读恢复实现和重建实验。

JADX 中出现不可能分支、R8 合并控制流或自相矛盾时，必须继续查 DEX、双 ABI 或发布 native 的实际运行结果。

可直接进入 Git 的反编译证据保存在 `docs/apk-reference/`，其目录结构、映射和使用规则统一记录在本文后续“APK 文本证据索引”章节。

## 3. recovery 与 faithful 材料结构

`recovery/` 是发布旧版本的历史取证区，不是 `main` 的源码树：

- `legacy-src/`：`v5.6.0-xray.5` faithful 可读恢复源码；其中 `upstream/` 是固定 FongMi 5.6.0 overlay，`com/fongmi/android/tv/xray/` 与 `legacy/` 保存 Service、会话、网络、设置和安全 helper，`aidl/` 保存发布 Binder contract；
- `legacy-tests/`：faithful 恢复工具和源码测试；
- `libxray/`：发布版 libXray / Go JNI 的可读行为重建补丁；
- `native-tests/`：发布 JNI 的固定 native fixture、QEMU/Bionic harness 输入与 chain oracle；
- `node-dns-tests/`：固定 Xray-core DNS / IPv6 dial 行为证据；
- `v2rayn-tests/`：旧发布版分享链接兼容 fixture。

`scripts/recovery/prepare-legacy-faithful.sh` 从固定上游组装临时 faithful tree，避免把完整上游副本永久复制进仓库。`recovery/work/` 与 `recovery/evidence/` 是 workflow / 本地临时目录，由 `.gitignore` 排除，不属于固定证据。

当前直接参与构建的 Media3 / Libass compatibility 已迁到 `compat/`；当前 `main` 的源码回归入口在 `tests/`。faithful 源码负责解释发布行为，当前 `:xray` 负责可维护实现，两者不能混成一套源码。

## 4. APK 文本证据索引

`docs/apk-reference/` 只保存适合进入 Git、且对长期复核有价值的最小文本证据；原始 APK、完整 DEX、AAR、SO 和完整 JADX 输出不进入普通 Git 历史，需要时由手动 recovery workflow 重新生成。

主要材料：

- `shared/sources/`：当前 Git 中保存 63 个 v7 / arm64 逐字节一致的 selected Java source；第 64 个逻辑 selected source `p000/ip0.java` 是唯一双 ABI 差异项，因此分别保存在 `docs/apk-reference/v7/ip0.java` 与 `docs/apk-reference/v8/ip0.java`。两份 `ip0` 的 EventBus 注册内容相同，只是 R8 生成的 `HashMap.put` 顺序不同。历史 `shared/source-parity.txt` 曾在 generation note 中列出 `HomeActivity.java`，但当前 Git 证据树并未保留该文件，后续不得把它当成“已提交 selected JADX”引用；
- `shared/AndroidManifest.xml`：两 ABI 一致的 Manifest 文本；
- `shared/dex-sha256.txt`：APK 内 DEX SHA-256；
- `shared/apk-diff.txt`：两正式 APK ZIP entry 级差异；
- `shared/source-parity.txt`：selected source 的双 ABI 对照；
- `native-share-symbols.json`：发布 libXray Go JNI 中 share conversion / Invoke 相关 symbol、源码行和地址索引。

2026-10-02 又独立执行了一次固定输入的完整取证：只触发一次 `recovery-apk-analysis.yml`（run `36910320478`），重新得到 v7 完整 JADX（artifact `11186391673`，10,017 个文件）以及 v7/v8 DEX + targeted dexdump（artifact `11186181891`）。这次不是只复用旧 selected source，而是从 fresh full-JADX 重新反向枚举 Xray 直接引用、旧 `PlayerManager(th2)` 的 current-client/proxy caller，以及 generated Binder/timeout glue。同步三份仅格式不同的网络 helper 后，当前 Git 中 63 个 `shared/sources/` Java 文件全部与 fresh v7 JADX Git blob 精确一致；`ip0.java` 仍作为唯一双 ABI 文本差异分别保存。

常用 R8 / JADX 导航：

| R8 / JADX | 责任 | readable reference |
| --- | --- | --- |
| `yz3` | playback session / generation / timeout | `LegacyXraySessionController` |
| `hz3` | Service bind / Binder death | `LegacyXrayServiceClient` |
| `rz3` | operation result | `LegacyXrayOperationResult` |
| `lz3` | operation id | `LegacyXrayOperationIds` |
| `pz3` | SOCKS OkHttp resources | `LegacyXrayHttpResources` |
| `oz3` | RTSP SOCKS SocketFactory | `LegacyXrayProxySocketFactory` |
| `qz3` | public destination guard | `LegacyPublicPlaybackDestinationInterceptor` |
| `lu2` | encrypted share-link store | `LegacyXrayConfigStore` |
| `a04` | share-link normalize / display helper | `LegacyXrayShareLinkNormalizer` / `LegacyXrayDisplay` |
| `kz3` | error redaction | `LegacyXrayErrorSanitizer` |
| `uz3` | IXrayService Binder | recovered `XrayService` |
| `th2` | PlayerManager / proxy transition | faithful `PlayerManager` |
| `nq0` | Exo MediaSource factory | faithful `ExoMediaSourceFactory` |
| `or2` | Xray scheme guard DataSource | `LegacyXraySchemeGuardDataSource` |

使用证据时：

1. 先核正式 APK SHA-256；
2. 查 Java 结构优先从 selected source 定位；
3. JADX 控制流明显不可信时，不自行“修合理”，继续查 DEX、双 ABI或发布 native 的实际行为；
4. R8 短类名只作为发布 APK 导航，不进入 current API 设计；
5. 不直接复制未经核对的 JADX 作为维护源码；
6. 只把长期可复核的最小文本材料提交到 Git；调试日志和一次性中间文件留在 artifact / 工作目录。

## 5. 历史发布版行为记录

### Service 与会话

以下内容描述 `v5.6.0-xray.5` 的已取证发布行为。`main` 保留模块化实现，但涉及同一 Xray 外部语义时以这些证据作为 parity 参考。

发布版使用独立 `:xray` 私有进程。

关键语义包括：

- VOD 与 Live 各自维护播放 Xray 会话；
- operation id 与 generation 用于过滤旧异步结果；
- Service bind timeout 约 5 秒；
- playback start timeout 为 30 秒；
- previous STOP cleanup timeout 为 1500 ms；
- settings test / security reset timeout 为 45 秒；
- Binder death、binding died、null binding 与 disconnect 都有明确收口；
- 旧 STOP 或旧 callback 不能破坏更新的 START；
- 无法可信清理的 Service 路径会结束私有 Xray 进程。

发布 Binder descriptor：

- `com.fongmi.android.tv.xray.IXrayService`
- `com.fongmi.android.tv.xray.IXrayCallback`

当前模块化 `:xray` 使用新的包名，因此方法形状相近不代表 Binder 二进制兼容。

### 播放网络

发布版的 Xray 是当前播放身份的网络资源，不是全局状态：

- 新集、新频道、换线路 / 换源、真正更换播放器等**逻辑播放身份变化**后默认直连；同一身份内 parser 解析结果、HTTP redirect 或 CDN 实际 URL 变化不重置 Xray；
- 启用 Xray 的播放使用独立 SOCKS HTTP 资源；
- SOCKS hostname 以 unresolved address 交给代理侧解析；
- Xray 播放不复用普通直连 cache / preload 身份；
- RTSP / RTSPT 使用 SOCKS SocketFactory；
- DRM license 跟随当前 Xray DataSource；
- 本机、私网和保留目标受 destination guard 保护；
- 会话结束后关闭 Dispatcher、ConnectionPool、executor 与相关代理资源。

### VOD / Live 身份

VOD 的会话边界包括切集、自动下一集、换线路、换源、真正换播放器、播放结束和离开页面；parser 结果、HTTP redirect 或 CDN URL 在同一逻辑身份内变化时只更新 resolved media URL，不结束会话。

Live 的会话边界包括切频道、换线路 / 源、直播配置变化和播放器变化；同一频道身份内的实际媒体 URL 解析变化同样不单独构成会话边界。

直播解析过程中允许等待 Xray START；Xray 启动失败不能破坏原本可用的直连播放。EPG、XML metadata、logo / artwork 等旁路也需要遵守当前播放网络身份。

### 分享链接、设置与安全

主要输入格式：

- VLESS
- VMess
- Trojan
- Shadowsocks
- Hysteria2 / hy2

恢复证据覆盖的兼容边界包括：

- legacy SS；
- SIP003 `v2ray-plugin`；
- VMess JSON port；
- HY2 默认端口、multi-port、`pinSHA256`、obfs；
- IPv6 authority；
- URI / credential 编码；
- KCP、gRPC、Reality、XHTTP 等参数。

设置与安全语义包括：

- 分享链接使用 Android Keystore AES-GCM；
- preference：`xray_secure`；
- key alias：`fongmi_xray_share_link_v1`；
- 节点测试使用独立 operation，不留下 playback session；
- 删除节点时同步清理对应 security state；
- 手机导入复用 FongMi 局域网页面；
- 非默认 TLS / HY2 信任通过首次 pin 与后续变更拒绝实现；
- 错误展示前会隐藏链接、UUID、密码、token、secret、key、short id、seed 等敏感内容。

### 当前模块与 v7 证据映射账本

当前 `:xray` 的类名和旧 APK 混合架构不同，不能用“有没有同名类”判断是否还原。2026-10-02 完整重建并统一到 `main` 后的映射如下：

| current | v7 / readable evidence | 说明 |
| --- | --- | --- |
| `XrayConfigFactory` | `LegacyXrayRuntimeConfigFactory` + 发布 native converter | JSON 生成语义由 differential/native parity 锁定 |
| `XrayDisplay` | `LegacyXrayDisplay` | 去包名/类名后行为镜像 |
| `XrayPreferences` | `LegacyXrayConfigStore` | secure prefs / Keystore 逻辑源码镜像 guard |
| `XrayShareLinkNormalizer` | `LegacyXrayShareLinkNormalizer` + `a04` + v7 native cases | VLESS/VMess/Trojan/SS/HY2/KCP 等 differential/native parity |
| `LibXrayBridge` | `LegacyLibXrayApi` + `LegacyXrayProbeApi` + `s11` | 正常调用面一致；current 只额外收口 `LinkageError` |
| `PublicPlaybackDestinationInterceptor` | `LegacyPublicPlaybackDestinationInterceptor` | 公开/私网 destination policy 镜像 |
| `XrayHttpClient` | `LegacyXrayHttpResources` + `th2/pz3/yd0` | 独立 Dispatcher/Pool/SOCKS 与 cleanup 顺序一致 |
| `XrayProxySocketFactory` | `LegacyXrayProxySocketFactory` | RTSP unresolved SOCKS 语义镜像 |
| `XrayCertificatePins` | `LegacyXrayCertificateStore` + `j81` | pin store / alias / migration 源码镜像 guard |
| `XrayShareLinkSecurity` | `LegacyXrayTransportSecurity` | TLS/HY2 TOFU、identity、pin change differential |
| `XrayGenerationGate` | `LegacyXrayGenerationGate` | generation 算法一致；current 仅收紧可见性 |
| `XrayOperation` | `LegacyXrayOperation` | operation 1~5 保持一致 |
| `XrayService` | `recovery/legacy-src/.../xray/XrayService.java` + `sz3/tz3/uz3` | VALIDATE/TEST/START/STOP/RESET_SECURITY、cleanup/process reset |
| `PlaybackIdentityGate` | 旧 VOD/Live Activity、Controller、`th2` 调用链 | 新架构抽出的逻辑身份状态机，没有旧同名类 |
| `XrayOperationIds` | `LegacyXrayOperationIds` | operation id 递增语义镜像 |
| `XrayPlaybackAddress` | `LegacyXrayPlaybackAddress` | public HTTP(S)/RTSP/RTSPT 与 Live direct-source 边界一致 |
| `XrayPlaybackSession` | 旧 Activity + PlayerManager + session controller 融合行为 | 新架构独立会话对象；换身份、resolved URL、preserve/error cleanup 由 playback/race guard 锁定 |
| `XrayResult` | `LegacyXrayOperationResult` | callback result carrier |
| `XrayServiceClient` | `LegacyXrayServiceClient` + `ez3/hz3` | bind/death/null/disconnect/5s timeout |
| `XraySessionController` | `LegacyXraySessionController` + `yz3` | 1.5s cleanup、30s startup、stale callback/race |
| `XraySessionListener` | `LegacyXraySessionListener` | 仅状态/方法命名模块化，状态值保持一致 |
| `XraySettingsController` | `LegacyXraySettingsController` + 设置页 DEX | 45s timeout、delete/reset 顺序、phone-import abandon |
| `XrayErrorSanitizer` | `LegacyXrayErrorSanitizer` | 文本去敏主体镜像；current 额外支持 Throwable/LinkageError 收口 |

另外两段旧 helper 因为属于 FongMi 播放器接口而留在 `:app`：`XrayArtworkBitmapLoader` 对应 `LegacyXrayBitmapLoader/rf2`，`ExoMediaSourceFactory.GuardedPlaybackDataSource` 对应 `LegacyXraySchemeGuardDataSource/or2`。两者的 local-scheme / Unicode whitespace 判定已重新按 v7 对齐：无 scheme 的本地路径以及 `file`、`asset`、`content`、`data`、`rawresource`、`android.resource` 继续走本地资源；HTTP(S) 使用当前 Xray DataSource；其它无法保证网络身份的泛用 scheme 在 Xray active 时拒绝。

旧 `PlayerEngine` 曾暴露 Xray getter，但 5.6.3 新播放器架构不再需要污染该上游接口；`main` 的 blob guard 要求 `PlayerEngine.java` 与 `FongMi/TV@c616c0aa3613e87529791587a9f71b78c278c991` 完全一致，原 getter 语义迁入 `PlayerManager`、`ExoPlayerEngine.proxy()` 与 `PlayerEngineFactory(proxy)`。因此“PlayerEngine 不含 Xray”是架构迁移结果，不是漏迁。

这张账本只说明**已取证的行为映射**，不是声称已经拿到旧 APK 的原始未混淆源码。任何未来发现的新 full-JADX / DEX caller 都应先补到本表及 parity guard，再修改当前实现。

本次 fresh full-JADX / DEX 复核重新确认的外围 caller 包括：Live EPG/XML、VOD 自动弹幕、弹幕搜索与播放器重建后的 client 重绑、字幕搜索/详情/下载、远程 MediaSession artwork、VOD/Live artwork/logo、preload/cache、外部播放器、手机导入，以及 VOD/Live 的 proxy install/remove 与逻辑播放身份变化。旧外部播放器本身也只接收原始 URL/headers，并不获得应用内部 SOCKS；当前实现保持同一边界。fresh AIDL 事务 1~6 也与当前 `validate / test / start / stop / resetSecurity / cancel` 顺序一致，callback 参数形状一致。此次没有发现新的、尚未映射到当前 `main` 的 Xray runtime path。

### Android TV 网络恢复

发布版同时包含与 Xray 无关的 TV 网络恢复逻辑：

- Activity 与 SCREEN_ON / SCREEN_OFF 推进网络代际；
- Home 在重新回到前台时判断是否需要恢复；
- 普通 API client、DNS / DoH 与 Spider 环境可以重建；
- 旧业务请求会被取消，避免晚到结果覆盖新页面；
- 网络稳定检查以约 500 ms 周期进行；
- 连续两次具备 Internet capability 后继续；
- 最多约 12 次检查后继续刷新；
- DLNA 生命周期随电视前后台 / screen 状态收口。

这一能力在重构后仍属于 `:app` / `:catvod`，不属于 `:xray`。

## 6. 播放器与 FFmpeg JNI

固定 Media3 player candidate 来源：

- FongMi/media commit：`3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`
- 历史 recovery artifact 曾得到 candidate ZIP SHA-256 `0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee`；它只作为当时取证记录，不再是当前构建或 recovery workflow 的长期存储依赖。
- 现行流程统一由 `scripts/build/build-player-aar-candidate.sh` 从上述固定 commit 重建 17 个 AAR（包含 `lib-decoder-mpegh`），并由 `scripts/build/player_candidate.py` 校验文件集合、每个 AAR 的 manifest SHA 与关键播放器 class。外层 ZIP 本身不再作为长期 pin。

历史 faithful recovery 曾确认发布 APK 中的 `libffmpegJNI.so` 与固定公开 media candidate 不同，并建立了对应恢复工具。这项能力**只保留为旧 APK / faithful recovery 证据**；`main` 与当前 publish workflow 已不再注入发布版 FFmpeg JNI，而是直接使用固定公开 FongMi/media 现场重建出的 decoder AAR。

历史发布版 FFmpeg JNI 证据：

| ABI | SHA-256 |
| --- | --- |
| armeabi-v7a | `3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42` |
| arm64-v8a | `26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c` |

faithful recovery 生成的 decoder AAR SHA-256 为 `31a1db2570416147cc6889643d25345477977205d60a61a6df525ffa5a623a13`。恢复脚本只替换 v7 / arm64 两个 `libffmpegJNI.so`，其余 ZIP entry 保持候选 AAR 内容；不要把这套 recovery 逻辑重新接回 `main`。

相关工具：

- `scripts/recovery/restore-published-ffmpegjni.py`
- `scripts/recovery/check-player-ffmpegjni-against-published.py`
- `scripts/recovery/check-player-java-api.py`

## 7. libXray / Go JNI

正式 APK 中的 Go JNI：

| ABI | SHA-256 |
| --- | --- |
| armeabi-v7a | `6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e` |
| arm64-v8a | `40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece` |

发布二进制与官方 `v26.7.28` 并不完全相同。发布 native 已确认包含项目所需的扩展行为，例如：

- Invoke API version 2；
- `test` / `run` 内联 `xrayJson`；
- `pingBatch` item 内联 `xrayJson`；
- TLS certificate probe；
- HY2 certificate probe；
- age subscription / key generation；
- legacy SS、HY2 multi-port / pin、ALPN / port、legacy KCP 等转换兼容。

历史恢复得到的 `libXray.aar` SHA-256：

`f531a138e82fa08848e47cf22537c69df29227b07eba7d19c2ad3740af657365`

它以官方 AAR 为容器，只替换正式 APK 中的 v7 / arm64 `libgojni.so`；Java API、x86 / x86_64 JNI 和其他 entry 保留官方内容。`main` 的重建路径进一步把发布 APK 中匹配 JNI 的 `libXray/**` generated bindings 一并恢复，同时保留官方 AAR 的通用 `go/**` runtime。官方 v26.7.28 `go.mod` 固定 `golang.org/x/mobile v0.0.0-20260709172247-6129f5bee9d5`，与发布 JNI BuildID 指向的 x/mobile commit 相同，因此当前没有发现通用 gomobile runtime 跨 ABI 世代混用的证据。

相关工具：

- `scripts/recovery/fetch-libxray.sh`
- `scripts/recovery/restore-published-libxrayjni.py`
- `scripts/recovery/check-libxray-gojni.py`

## 8. native 可读重建

仓库还保存了依据正式发布 native 行为重建的可读补丁：

- `recovery/libxray/share-converter-recovery.patch`
- `recovery/libxray/native-v2-recovery.patch`
- `recovery/libxray/native-age-errors.patch`

它们用于解释、测试和继续研究发布行为，**不是找回的原始 Go 源码**。

对应证据与测试主要在：

- `recovery/native-tests/`
- `recovery/v2rayn-tests/`
- `recovery/node-dns-tests/`
- `tests/test-recovered-libxray.py`
- `tests/test-native-abi-parity.py`
- `tests/test-native-share-chain.py`
- `tests/test-v2rayn-share-chain.py`
- `tests/test-v2rayn-reference-chain.py`

发布 JNI 已建立 converter、API v2、lifecycle、TLS / HY2 probe、age、v2rayN-shaped 输入、IPv6 / DNS dial 等定向执行证据。faithful 重建使用发布 JNI 字节，不用可读重建补丁冒充原始 Go 源码。`main` 继续复用固定 SHA 的 native 字节，并用双 ABI current-chain 动态 parity 将当前 Java 配置链与 v7 黄金 oracle 对齐；faithful APK 能否重新 assemble 仍不是当前 `main` 发布条件。

## 9. 归档 faithful 构建工具（非 `main` 构建链）

这一节保留的是历史重建工具。它们只在需要复核旧发布版、重新提取历史 native 来源或研究旧行为时使用；正常 `main` 开发和发布**不要求执行本节流程**。

本地入口：

`scripts/recovery/build-legacy-faithful.sh`

它负责：

1. 校验 player AAR 调用面；
2. 校验 FFmpeg JNI；
3. 校验 libXray Go JNI；
4. 从固定 FongMi 5.6.0 上游组装 faithful overlay；
5. 调用 Gradle 构建 Leanback faithful APK。

GitHub Actions 对应两段手动流程：

### 归档：Archive - prepare v5.6.0 native evidence

文件：

`.github/workflows/recovery-restore-ffmpegjni.yml`

职责：

- 固定正式 Release APK；
- 从固定 FongMi/media commit 现场重建并验证 player candidate；
- 从发布 APK 恢复 FFmpeg JNI；
- 获取官方 libXray；
- 从发布 APK恢复 Go JNI；
- 输出 `fingmi-faithful-native-dependencies` artifact。

### 归档：Archive - v5.6.0 faithful TV reconstruction

文件：

`.github/workflows/recovery-build.yml`

输入：

- 上一步经过验证的 native dependency artifact ID。

职责：

- 再次验证短期 native dependency artifact 的来源；
- 从固定 FongMi/media commit 重建 player candidate，再导入该 candidate 与已验证 native 依赖；
- 组装固定 5.6.0 faithful tree；
- 执行 faithful Gradle 构建。

这些 workflow 只允许手动 `workflow_dispatch`，并视为历史归档工具。它们的成功或失败不再决定当前 5.6.3+ 架构能否发布；`main` 的构建、源码 guard、当前回归与 Android 运行测试才决定当前版本验收。

## 10. 历史证据与当前 parity 原则

需要复核历史恢复材料时，必须区分：

- 反编译文本一致；
- DEX / ELF / JNI 证据；
- JVM / Python / Go 测试；
- Gradle 编译；
- APK assemble；
- Android TV 真机运行。

较低级别证据只能证明对应层级，不能替代更高层级验证。

2026-10-02 fresh audit 的结论强度因此定义为：在固定 v7 APK 可反编译/可枚举的 Java、DEX、Binder、播放器外围调用链范围内，未发现当前 `main` 缺失的已知 Xray 功能或网络旁路；native Xray Core 则继续使用发布 APK 中固定 SHA 的 `libgojni.so` 字节与匹配 generated Java bindings，并已有双 ABI current-chain 动态 parity。这个结论是“已取证外部行为与调用链完整映射”，不是“恢复了原始源码逐字节 1:1”。

如果未来出现新的 APK / DEX / native 证据改变既有结论，应先修正 recovery reference / fixture，再更新当前 parity 测试与本文。当前重构实现不需要回退旧 faithful 架构，但凡已经确认属于 v7 Xray 外部行为的语义，应在当前模块中恢复或做等价映射。最终仍需用当前测试、构建和 Android TV 设备回归确认真实运行。

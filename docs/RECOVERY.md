# FingMi-Xray 源码恢复文档

本文是 `v5.6.0-xray.5` 源码丢失后的 **唯一恢复主文档**。

这里记录：

- 恢复依据；
- faithful 源码现状；
- 已确认的发布版行为；
- APK / JADX / DEX 证据；
- 已解决的反编译歧义；
- 播放器与 libXray 二进制恢复；
- 当前构建门；
- 设备回归门；
- 恢复完成前还必须做什么。

不在这里记录逐次搜索、分钟级工作过程或已经被后续结论覆盖的猜测。Git 历史承担时间线职责。

长期项目目标见 [PROJECT.md](PROJECT.md)，普通工程、模块迁移和工作规则见 [DEVELOPMENT.md](DEVELOPMENT.md)，原始产品规格见 [ORIGINAL_README.md](ORIGINAL_README.md)。

---

## 1. 恢复目标

已发布的 `v5.6.0-xray.5` 原始开发源码曾丢失。

恢复阶段的目标不是重新实现“功能差不多”的版本，而是：

1. 以正式发布 APK 的真实行为为最高运行时依据；
2. 以固定 FongMi/TV 5.6.0 源码恢复可读上游结构；
3. 将发布 APK 中的 Xray、播放器、设置、安全、Binder、资源和 TV 网络恢复改动恢复成可维护源码；
4. 保留过去多轮调试形成的竞态、超时、失败回退、资源清理和兼容边界；
5. 恢复缺失的非 Git 播放器 AAR、FFmpeg JNI 和 libXray 依赖；
6. 得到一套可重现构建、可在设备回归的 faithful 基准；
7. faithful 基准通过后，才正式进入模块化迁移。

`recovery/legacy-src/` 是当前 faithful 基准。普通工程中的 `:xray` 是后续迁移目标，不是发布版行为真相。

---

## 2. 可信基线

### 发布版本

- FingMi-Xray：`v5.6.0-xray.5`
- FongMi/TV：`5.6.0`
- versionCode：`56005`（faithful 发布身份）
- libXray / Xray-core：`v26.7.28`

### 发布 APK

主要运行基线：

- ABI：`armeabi-v7a`
- SHA-256：`cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda`
- Release asset：`FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk`

交叉验证基线：

- ABI：`arm64-v8a`
- SHA-256：`b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d`
- Release asset：`FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk`

v7 是实际使用版本；v8 用于交叉验证。

### 固定上游

FongMi/TV：

- commit：`1a19fee278fa2234da725d61a53bf59b69fe9127`
- version：`5.6.0`
- versionCode：`560`

libXray：

- tag：`v26.7.28`
- tag commit：`80263da83e96b2972455b0a94b13ee1a10e51391`
- 官方 Android ZIP SHA-256：`28b7dc9d6cc8455fcca5cbd56e387003a7bfb558128651a64899dc3a8ccff666`

---

## 3. 证据优先级

发生冲突时按以下顺序处理：

1. 固定 SHA-256 的正式发布 APK 实际逻辑；
2. [ORIGINAL_README.md](ORIGINAL_README.md) 的原始产品意图；
3. 固定 FongMi/TV 5.6.0 上游源码；
4. JADX / DEX 等反编译证据；
5. 当前恢复源码或实验性模块。

JADX 只是证据。出现以下情况时必须继续核原始 DEX或其他强证据：

- 自相矛盾的条件；
- 不可能成立的 null 分支；
- 明显死循环；
- R8 合并后的控制流错位；
- 与后续基本块无法同时成立的伪代码。

当前已知的 decompiler-repaired 条件已经用 DEX 收口，**faithful 源码中当前无残留 `DEX_VERIFY` 项**。

---

## 4. Faithful 源码形态

恢复源码主要位于：

- `recovery/legacy-src/upstream/`  
  固定 FongMi 5.6.0 结构上的覆盖文件；
- `recovery/legacy-src/com/fongmi/android/tv/xray/`  
  发布版 Xray Service；
- `recovery/legacy-src/com/fongmi/android/tv/xray/legacy/`  
  可读的 faithful helper / controller；
- `recovery/legacy-src/aidl/`  
  发布版 Binder contract；
- `recovery/legacy-tests/`  
  纯 Java / Python 恢复门测试。

当前恢复规模：

- 51 个上游覆盖文件；
- 24 个 Xray Java；
- 2 个 AIDL；
- Leanback Manifest、布局、strings、网页导入 assets 等资源覆盖。

`scripts/prepare-legacy-faithful.sh` 使用固定 FongMi commit 组装 temporary faithful tree，不使用任意上游工作目录作为基准。Source-only 组装已经验证过覆盖文件可以按固定上游重建；这不等于 Gradle 编译成功。

---

## 5. 发布版行为冻结

以下内容已经有 APK / DEX / 资源证据并由 faithful 源码承载。状态均指 **静态恢复已覆盖**，不代表设备回归已经完成。

### 5.1 核心边界

- 不创建 Android 系统 VPN；
- Xray 仅服务当前手动开启的媒体播放会话；
- 普通首页、搜索、详情和普通 API 继续走原网络；
- Xray Core 位于独立 `:xray` 私有进程；
- VOD 和 Live 各有独立 playback session owner；
- 新集、新频道、新源、新地址、新播放器不自动继承旧 Xray 状态。

### 5.2 Service / Binder / 进程生命周期

发布版使用 operation id / generation 防止旧异步结果污染新操作。

已恢复：

- Binder validate / test / start / stop / reset-security / cancel；
- Service bind timeout：约 5 秒；
- playback start timeout：30 秒；
- previous STOP cleanup timeout：1500 ms；
- settings test / security reset timeout：45 秒；
- Binder death、binding died、null binding、service disconnected；
- stale callback generation 过滤；
- stop Core 重试；
- STOP 失败消息已送达主进程时由主进程对精确 operation id cancel；
- STOP 失败消息无法送达时由 Service 自行 cancel / kill；
- cleanup 不可信、native 工作取消或 Service destroy 时允许结束私有 `:xray` 进程；
- Service destroy 路径包含 stop、executor shutdown、最多约 3 秒收口和 private process kill。

不要在后续重构中把这些逻辑简化成单个全局 boolean。

### 5.3 播放网络

已恢复：

- Xray playback session 强制使用 Exo；
- SOCKS 使用 unresolved hostname，避免代理前本地解析媒体域名；
- HTTP(S) 播放使用独立 Xray OkHttp、Dispatcher、ConnectionPool；
- Xray session 不复用普通直连磁盘 cache 上游；
- public-destination guard 阻止 localhost、私网、保留 IPv4 / IPv6 地址绕进代理；
- Xray 媒体地址支持 HTTP、HTTPS、RTSP、RTSPT；
- RTSP 使用自定义 SOCKS SocketFactory；
- RTSP User-Agent 仅在存在非 Unicode whitespace 字符时设置；
- DRM license 使用与当前 Xray session 相同的 proxy-aware DataSource；
- Xray session 禁止下一集 preload；
- side-network 请求不能跨 session 错用旧 client。

资源清理：

- Xray session 的 Dispatcher cancelAll；
- ConnectionPool evictAll；
- Dispatcher executor shutdown；
- cleanup executor 为 daemon thread；
- Core worker thread 为 daemon thread。

### 5.4 VOD

已恢复的发布版行为：

- 播放菜单手动开启 Xray；
- 只有已有可播放 session 且播放器进入 READY 后才允许开启；
- 下一集、上一集、自动下一集结束旧 Xray；
- 切线路、换源、刷新实际播放地址结束旧 Xray；
- 真正更换播放器时结束旧 Xray；
- 播放结束结束旧 Xray；
- 离开播放页面 / onStop 收口；
- Xray port 切换允许保留当前播放快照做直连 ↔ 代理转换；
- Xray 切换期间封面 / artwork 不使用错误网络身份。

### 5.5 Live

已恢复的发布版行为：

- Xray 与“切换源”位于同级菜单；
- 切频道、切直播线路 / 源、换整套直播配置、换播放器后不继承旧 Xray；
- 已有频道正在播放时开启 Xray，切 proxy port 时保留当前播放；
- 频道仍在解析时开启 Xray，启动成功后按 pending request 继续解析；
- Xray 启动失败时不能破坏原本正常直播放；
- EPG / XML / metadata 与当前播放 session 使用一致网络；
- Xray 切换时取消旧 metadata，但不误杀当前 URL resolver；
- 当前 logo / channel logo / artwork 避免跨网络身份混用；
- onStop / onDestroy 收口 session。

### 5.6 分享链接、设置与安全

支持的主要分享链接：

- VLESS；
- VMess；
- Trojan；
- Shadowsocks；
- Hysteria2 / hy2。

faithful normalizer 包含：

- legacy Shadowsocks base64；
- SIP003 `v2ray-plugin` 转换；
- VMess JSON port 验证；
- Hysteria2 default `:443`；
- authority port hopping；
- `mport`；
- `pinSHA256`；
- obfs / password；
- URI / IPv6 / port 边界；
- Trojan / SS credential `+` 等现实兼容修补。

固定官方 `libXray v26.7.28` 的分享链接转换源码已经直接核到 tag commit
`80263da83e96b2972455b0a94b13ee1a10e51391`。该 tag 依赖的 Xray-core 为
`v1.260327.1-0.20260728075948-5ca6f4b7d4dc`。它是发布 native 的可读基础版本，
但**不能再把同版本号解释为发布 Go 源码与官方 tag 完全一致**：发布版
`libgojni.so` 已确认包含定制 Invoke API。

关键源码 / blob：

- `share/parse_share.go` — `9cfcb005f23500f529a3846ff2e29499a431805c`
- `share/transport_build.go` — `11f9d6ba633f512fd555d9ce3b43d18fe08eafa9`
- `share/vmess.go` — `18becd9c6a3ec39c234ad3b46695478ad72cbb0b`
- `share/stream.go` — `b488f2721294a7ee29d600eed86d2e15128bed1a`
- `share/hysteria_mask.go` — `cbdc5e5b706a3d5e9bea9a0ebdbc7c2c1b9a5394`
- `invoke.go` — `9e1ec1a8fe87934015d647eb0bbf17f4eec0dcfd`

### 发布 Go JNI 与官方 tag 的差异

2026-09-26 已直接从固定 full JADX 归档提取两 ABI 发布 `libgojni.so` 并核固定 SHA：

- v7：`6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e`
- v8：`40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece`

两份 ELF 都保留 Go build info / symbol / source line 信息。实际静态 native 检查确认：

- Go：`go1.26.3`，Android 21，NDK r29；
- 两 ABI 都依赖同一 Xray-core `v1.260327.1-0.20260728075948-5ca6f4b7d4dc`；
- `github.com/xtls/libxray` 不是按公开 tag module identity 直接构建，而是由本地 replacement
  `C:\\Users\\Administrator\\Desktop\\Codex\\work\\libXray-final` 构建；
- 发布 `Invoke` 的 `invoke.go:95` 原生指令明确比较 `apiVersion == 2`；不接受官方 tag 的“0 或 1”语义；
- 发布 native 存在 `invokeProbeTLSCertificate` 与
  `invokeProbeHysteria2Certificate`，官方固定 tag 的 Invoke 分发没有这两个入口；
- 发布 `invokeTestXray` / `invokeRunXray` 的类型信息明确解码
  `XrayJson string json:"xrayJson,omitempty"`，与 App 的内联 JSON 调用一致，而不是官方固定 tag 的 `configPath`；
- 发布 `invokePingBatch` 的 item 同样包含 `XrayJson`；
- 两 ABI 都包含 `transportFieldsFromURLQuery`、
  `transportFieldsFromVmessQR`、`buildStreamFromTransportFields`、
  `buildHy2FinalMask`、Trojan / Hy2 / VLESS / VMess outbound 等 converter 符号；
- 发布 binary 的这些 share 函数仍映射到
  `share/transport_build.go`、`share/hysteria_mask.go`、`share/parse_share.go`，
  且关键函数起始源码行与固定官方 tag 对应文件一致（例如 29 / 51 / 78、12、595）。

进一步把发布 JNI 与 official AAR 的实际 Go symbol set 做双 ABI 交叉比较后，已确认
**share converter 本身也存在发布版定制**。发布 v7 / v8 同时出现、而 official AAR 对应 symbol set
没有的关键 helper 包括：

- `normalizeLegacyShadowsocksLink`；
- `normalizeHysteriaMultiPortLink`；
- `firstHysteriaPort`；
- `normalizeHysteriaPinSHA256`；
- `parseSharePort`；
- `decodeShareUserInfo`；
- `parseShareALPN` / `cleanShareALPN`；
- `legacyKCPMTU` / `legacyKCPFinalMask`；
- `rawQueryHasKey`。

发布 ELF 的 Go line table 还把这些 helper 精确映射回定制工作树中的
`share/parse_share.go`、`share/stream.go`、`share/transport_build.go`；
例如 multi-port 位于 `parse_share.go:227`、pin 归一化位于 `stream.go:112`、
legacy KCP helper 位于 `transport_build.go:161/182`。这证明 KCP / HY2 / Trojan / SS
适配不能只按 official tag 源码恢复。

因此当前确认的定制范围至少包含：**Invoke API v2、内联运行配置、ping item、证书探测，
以及 share converter 的 legacy SS、HY2 multi-port/pin、ALPN/port 解析和 legacy KCP 兼容。**
这些 helper 的存在与源码位置属于直接二进制证据；其逐分支可读 Go 源码和发布 native
输入输出 expected 仍在恢复中，不能把函数名推断写成已完整还原源码。

可重复检查入口：`scripts/inspect-published-libxray-native.py`。该脚本只做发布二进制静态 gate，
不会把 Android ARM JNI 当作当前主机可执行文件。

发布版实际转换边界：

- Java 先做 compatibility normalizer / TLS pin 安全处理；
- 然后通过 libXray `convertShareLinksToXrayJson` 生成单个 outbound；
- URL transport 的 `type` 为空时按 `raw`；
- `type=kcp/mkcp` → `KCPSettings`，保留 `headerType` 和 `seed`；
- `type=ws/websocket` → `WSSettings(path, host)`；
- `type=grpc/gun` → `GRPCSettings(authority, serviceName, mode=multi)`；
- `type=httpupgrade` → `HTTPUPGRADESettings(host, path)`；
- `type=xhttp/splithttp` → `XHTTPSettings(host, path, mode, extra)`；
- VMess QR 的 KCP / mKCP 使用 `path` 作为 seed，gRPC 使用 `path` 作为 serviceName；
- VLESS 的 `flow/encryption`、VMess 的 `encryption/scy`、Trojan password 由 native converter 写 outbound settings；
- Hy2 native outbound protocol 为 `hysteria`、version 2；`up/down/ports/hop-interval/obfs/obfs-password` 生成 FinalMask；
- TLS 参数 `fp/sni/alpn/ech/pcs/vcn/insecure` 和 Reality 参数 `pbk/sid/pqv/spx` 由固定 libXray 解析；
- Java transport-security rewrite 对未知 query key 保留原始 `part.raw`，因此不会丢 KCP、gRPC、Reality 或 XHTTP 参数；
- Java 仅对 Trojan / Hy2 literal `+` credential 做发布版兼容回填，并在 native conversion 后验证协议形状。

`LegacyXrayShareLinkNormalizerCases` 已增加 VLESS+KCP、Trojan+KCP、VLESS+gRPC+Reality 和 VMess-QR+KCP 参数保真回归，避免后续重构误删 native 已支持的 transport 字段。

设置与存储：

- share link 使用 Android Keystore AES-GCM；
- preference：`xray_secure`；
- key alias：`fongmi_xray_share_link_v1`；
- UDP 设置与节点一并保存；
- 读回旧节点时再次运行 compatibility normalizer；
- 节点测试使用独立 operation，不留下 playback Xray session；
- 删除节点同时重置 Xray security state；
- 手机导入复用 FongMi 局域网页面，不另起第二个 Server；
- 设置页用 generation / abandon 防止旧 test/import 结果覆盖新输入。

证书安全：

- insecure TLS / Hysteria2 先通过 libXray 探测证书；
- 首次信任后保存 pin；
- 后续证书变化拒绝；
- 已保存 pin 的 ASCII 文本按发布版原样比较，不擅自统一大小写；
- 常量时间比较；
- legacy pin 有明确迁移 / 清理顺序。

错误信息：

- 对完整 share link、UUID、password / token / secret / auth、key / short id / seed 等敏感信息做去敏；
- libXray 返回 error 的“空白”判断按 Unicode code point + `Character.isWhitespace()`，不是 `String.trim()`。

### 5.7 手机导入

已恢复：

- PushActivity 对应 Xray import tab；
- 网页提交 `do=xray`；
- XrayImportEvent；
- 相关 `assets/index.html` 和 JS；
- 导入后设置页旧测试结果不会覆盖新输入。

### 5.8 Android TV 长后台 / 待机网络恢复

这是项目第二核心能力，但不属于 Xray 模块。

发布版行为已恢复到 faithful：

- Activity / SCREEN_ON / SCREEN_OFF 推进网络代际；
- Home onResume / window focus 检查代际；
- 只替换普通 API client，不重置允许继续播放的 player client；
- 旧普通 client 异步执行 cancelAll → evictAll → executor shutdown；
- DNS / DoH transport 根据当前 supplier / concrete config 重建；
- Spider runtime 清理完成后再开始首页网络稳定轮询；
- 旧 RESULT 请求会取消，避免晚到覆盖新页面；
- 网络稳定判定每 500ms 一次；
- 连续 2 次具备 `NET_CAPABILITY_INTERNET` 即继续；
- 最多重试约 12 次，超限也继续刷新，不要求无限等待“真正联网”；
- DLNA 与前后台 / screen lifecycle 配合收口。

当前普通工程已经把这一组 Home、BaseLoader、SiteViewModel、TvNetworkLifecycle、OkDns、OkHttp faithful 文件直接接入；普通工程迁移状态统一记录在 [DEVELOPMENT.md](DEVELOPMENT.md)。

---

## 6. R8 / JADX 类映射

以下名称用于定位发布 APK，不假设它们是丢失源码的原类名。

| R8 / JADX | 恢复责任 | faithful 可读名 |
| --- | --- | --- |
| `yz3` | playback session、generation、start/cleanup timeout | `LegacyXraySessionController` |
| `hz3` | bind/unbind Service、Binder death、bind timeout | `LegacyXrayServiceClient` |
| `ez3` | ServiceConnection + DeathRecipient | Service client 内连接对象 |
| `gz3` | queued service operation | request / operation data |
| `rz3` | callback result | `LegacyXrayOperationResult` |
| `xz3` | playback UI state callback | `LegacyXraySessionListener` |
| `fz3` | service operation callback | callback contract |
| `lz3` | monotonic operation id | `LegacyXrayOperationIds` |
| `pz3` | per-session SOCKS OkHttp resources | `LegacyXrayHttpResources` |
| `oz3` | SOCKS-aware RTSP socket factory | `LegacyXrayProxySocketFactory` |
| `qz3` | private / reserved playback destination guard | `LegacyPublicPlaybackDestinationInterceptor` |
| `lu2` | encrypted share-link + UDP storage | `LegacyXrayConfigStore` |
| `a04` | share-link normalization | `LegacyXrayShareLinkNormalizer` |
| `kz3` | error redaction | `LegacyXrayErrorSanitizer` |
| `et1` | isolated latency test | `LegacyLibXrayApi.testLatency` 路径 |
| `uz3` | IXrayService Binder implementation | `XrayService` Binder |
| `j91` | Binder service interface | `IXrayService` |
| `h91` | Binder callback interface | `IXrayCallback` |
| `dz3` | callback Binder implementation | callback Stub |
| `th2` | PlayerManager / Xray port transition | faithful `PlayerManager` |
| `nq0` | Exo media source factory | faithful `ExoMediaSourceFactory` |
| `or2` | Xray scheme-guard DataSource | `LegacyXraySchemeGuardDataSource` |

发布 Binder descriptor：

- `com.fongmi.android.tv.xray.IXrayService`
- `com.fongmi.android.tv.xray.IXrayCallback`

这与当前实验模块的 `com.fingmi.xray.service.*` descriptor 不同。迁移时不能把“方法形状相同”误当成 Binder 二进制兼容。

---

## 7. 双 ABI APK / DEX 结论

正式 v7 / v8 APK 已在分析 workflow 中按发布 SHA-256 校验后反编译。

已有证据工件：

- v7 完整 JADX：artifact `10847466987`
- v7 / v8 DEX + 报告：artifact `10847337361`
- 历史 v8 完整 JADX：artifact `10825963688`

Actions artifact 只保留作来源溯源；恢复直接需要的关键文本证据已经收口到 `docs/apk-reference/`，以后不应为了查看这些逻辑重新运行 AC。

为避免 artifact 到期后重新反编译，三份完整分析 ZIP 也已持久保存到项目可访问 Library：

- `/FongMi-Xray/apk-reference/v7-full-jadx-v5.6.0-xray.5.zip` — SHA-256 `7aab8c3419717516167eba7cf6a6f320df894b9ef554761c0cfc98d90c580e8d`
- `/FongMi-Xray/apk-reference/v8-full-jadx-v5.6.0-xray.5.zip` — SHA-256 `8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b`
- `/FongMi-Xray/apk-reference/v7-v8-dex-report-v5.6.0-xray.5.zip` — SHA-256 `699eac1ef5d8261c303d953110fa8ec731f91cd7279c04a74c598311211a4c3f`

Library 副本是跨会话便利输入，不改变正式 APK 的证据优先级。

双 ABI 静态结果：

- 两边顶层 DEX 容器不是逐字节相同；
- 57 个包含 Xray / Hysteria / libXray 相关引用的反编译源码中，56 个逐字节相同；
- 唯一差异为 R8 EventBus subscriber index 类的 `HashMap.put` 顺序；
- 重点恢复类（`a04`、`th2`、`nq0`、`pz3`、`or2`、`qz3`、`XrayService`、`SettingXrayActivity` 等）v7 / v8 逻辑一致。

主 DEX 已记录示例：

- v7 `classes.dex` SHA-256：`e4a3e51121c2e0ff53b751bf38ea5f067086acbe8540d6f1405025205b969644`
- v8 `classes.dex` SHA-256：`ad5bf878ba1d5638068c8c204e4488f5aa51733d8379f2cc2c72d6ecf1fb113e`

`docs/apk-reference/` 已保存 selected JADX 源码、双 ABI Manifest、三个 DEX 的 SHA-256 和 APK entry 差异摘要。原始 APK / DEX 大二进制不提交到普通 Git；需要重新做原始字节级检查时必须先核固定发布 SHA，并复用已有脚本。

---

## 8. 已用原始 DEX 收口的 JADX 损坏点

### Hysteria2 authority port hopping

R8 类 `a04`：

- `indexOf(',')` 找到时进入 hopping rewrite；
- 未找到再检查 `indexOf('-')`；
- 任一找到都进入同一 rewrite；
- 两者都没有才走非 hopping 路径。

因此 faithful 条件为：

`contains(",") || contains("-")`

JADX 的矛盾条件是反编译损坏。

### Hysteria2 obfs

JADX 曾出现 null 与 `isEmpty()` 无法同时成立的条件。原始控制流确认：

- null 跳过；
- 非 null 再检查内容和支持类型。

### VMess JSON port

普通整数 port 不能因 `BigDecimal.scale() <= 0` 被拒绝。DEX / 控制流确认只有仍含小数或超出 1..65535 时无效。

### IPv6 / authority port

恢复后的：

- bracket IPv6 必须是 `]:port`；
- 非 bracket endpoint 只有一个 colon 才按 host:port；

与发布控制流一致。

### Runtime config outbound 数量

`XrayService.b` 两处 DEX 都确认：

- `outbounds == null` → 错误；
- `outbounds.length() != 1` → 错误。

JADX 的 `outbounds != null || ...` 是反编译损坏。

### 证书指纹

发布 DEX 确认：

- SHA-256 fingerprint 格式不匹配时抛 invalid fingerprint；
- 新探测值转小写；
- 已保存 pin 不改写大小写；
- 以 ASCII byte + `MessageDigest.isEqual` 比较。

### TLS / Hysteria2 IPv4 literal helper

发布 DEX 的 `j81.r()` 确认 IPv4 literal 判定严格要求：

- 恰好四段；
- 每段非空且最多 3 位；
- 多位数字不能以 `0` 开头；
- 每个字符都必须是十进制数字；
- 每段值必须 ≤ 255。

JADX 伪代码遗漏了这些失败跳转并可能误读成“四段就返回 true”。faithful transport-security 的默认 SNI 判断必须保留严格逻辑。

### public destination guard

`qz3` 的“纯数字 IPv4”判断：

- 遇到非数字、非 `.` 字符直接判定为普通 hostname；
- 不会把普通域名错误当成数字 IPv4。

### Binder stale connection failure

v7 原始 DEX `Lhz3;->d` 确认：

- failure 的 expected connection 为 null 或正是 current connection 时，才清理当前 Binder / pending / active 状态并派发失败；
- expected connection 非 null 且已经不是 current connection 时，只对这个过期 connection 做 unlink / unbind，然后立即 return；
- 晚到的旧连接失败不会继续清理新的 current connection。

faithful `LegacyXrayServiceClient.failLocked` 和实验模块 `XrayServiceClient.failLocked` 均保留这一 stale-connection return。

### TV 网络恢复

发布 DEX 确认：

- 下一轮网络检查 post 后有显式跳转返回，JADX 的 fallthrough 不能用来推断提前加载；
- 旧 OkHttp 清理顺序为 cancelAll → evictAll → executor shutdown。

---

## 9. 已确认并修正的 faithful 细节

以下是恢复过程中已经找到并修正、且容易被“合理化重写”破坏的细节：

- Xray DataSource 在 delegate `open()` 抛错后仍必须能 `close()` 清理；
- DRM 的 `DefaultDrmSessionManagerProvider.setDrmHttpDataSourceFactory` 接受通用 `DataSource.Factory`，Xray DRM 路径是发布版真实行为；
- RTSP User-Agent 的空白判断使用 Unicode code point + `Character.isWhitespace()`；
- artwork URI scheme 与 Xray DataSource scheme 的“空白”判定也按发布版显式 code-point `Character.isWhitespace()` 循环恢复，不依赖 Java 11 `String.isBlank()`；
- libXray error fallback 同样使用 code point whitespace，不是 `trim()`；
- proxy cleanup executor 的 thread 为 daemon；
- Xray core worker thread 为 daemon；
- SOCKS hostname 使用 unresolved address；
- Xray session 不能复用普通 preload / cache 身份；
- STOP timeout 不能在新 START 已 RUNNING 后误断新 Binder；
- stale callbacks 必须由独立 callback generation 过滤。
- settings 45 秒 timeout 的发布顺序是先让 UI 收到 `"Xray operation timed out"` 并清本地状态，再对精确 operation id 发 Binder cancel / unbind；不要把同步 cancel 放到用户提示之前。
- settings 的 timeout、onDestroy 和手机导入 abandon 都会先用全局 `LegacyXrayOperationIds.next()` 推进本地 operation identity；手机导入只放弃旧 Binder generation，不远端 cancel 原 test/validate。
- `LegacyXrayDisplay.describe()` 保持发布版的非 null 输入前提，不额外吞掉 `null`；恢复阶段不要用“更健壮”的防御性分支改变原 helper 语义。
- Binder 请求/结果值对象保持发布版原始字段语义：`shareLink`、`Runnable`、result `message` 不在构造器里额外把 `null` 归一化成空串或 no-op。

这些结论对应的关键反编译文本已集中放入 `docs/apk-reference/`，不再维护多份独立审计 Markdown。

---

## 10. 播放器 AAR 恢复

FongMi 5.6.0 所需自制 `lib-*.aar` 不在上游 Git 中。

### 固定候选

已通过手动 AC 从：

- `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`

编译并取得 16 个候选 AAR。

成功 run：

- run：`36124817040`
- artifact：`10859533459`
- artifact name：`fongmi-media3-aar-candidate-1.11.0`
- ZIP size：`44,336,768` bytes
- ZIP SHA-256：`0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee`
- GitHub Actions artifact `10859533459` 当前到期时间：2026-10-09 10:42:07 UTC
- 已另存一份同 SHA、同 size 的持久副本到项目可访问 Library：`/FongMi-Xray/FingMi-media3-player-AARs-1.11.0-candidate.zip`

该候选不是因为“能编出来”就直接可信，所有 faithful 构建入口必须继续过版本 / ABI 门。Library 副本用于跨会话和本地恢复，**不等于 GitHub Actions artifact**；当前 `recovery-build.yml` 仍会检查固定 GitHub artifact，artifact 过期后若继续使用云端 faithful workflow，需要另行解决 GitHub 侧持久输入，而不是绕过来源门。

### Java API 门

当前对真实候选 ZIP 的精选接口检查：

- 14 个类；
- 54 个公开方法 JVM descriptor；
- 全部匹配固定 TV 5.6.0 恢复源码的实际调用。

新增覆盖包括：

- DRM DataSource setter；
- RTSP force TCP；
- RTSP SocketFactory；
- RTSP User-Agent；
- preload manager / builder；
- FongMi 自定义 renderer / load control 等调用。

**54 项不是完整 Java ABI。** 最终 javac / Gradle 仍然是必要门。

### native 门

候选 AAR 每个 ABI 共有 11 个相关播放器 `.so`：

- 10 个与发布版逐文件 SHA-256 完全相同；
- 1 个不同；
- 没有额外未核对的候选播放器 native 文件。

10 个一致的核心库包括：

- `libmpv.so`
- `libplayer.so`
- `libc++_shared.so`
- `libavcodec.so`
- `libavdevice.so`
- `libavfilter.so`
- `libavformat.so`
- `libavutil.so`
- `libswresample.so`
- `libswscale.so`

### 唯一明确不匹配：libffmpegJNI.so

| ABI | 发布版 SHA-256 | 候选 SHA-256 |
| --- | --- | --- |
| armeabi-v7a | `3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42` | `93cc400a1e6a5cae1fbd941d0e799a5991d3684b60b7ab5b9348ecceeb86af66` |
| arm64-v8a | `26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c` | `10f8fc548bd0d1b66af2f5c49305d6ef165d77c84a53416e96fc9bbe5f060189` |

两边导出符号集合相同，但 `.text` / `.rodata` 也不同，不能宣称等价。

`scripts/build-legacy-faithful.sh` 会在 Gradle 前调用：

`scripts/check-player-ffmpegjni-against-published.py`

因此未经恢复的候选 decoder AAR会被**有意早停拒绝**。

### 已生成的 faithful decoder AAR

当前已有可跨会话取回的真实恢复产物：

- Library：`/FongMi-Xray/dependencies/lib-decoder-ffmpeg-release-faithful.aar`
- size：`23,417,373` bytes
- SHA-256：`31a1db2570416147cc6889643d25345477977205d60a61a6df525ffa5a623a13`
- v7 JNI SHA：`3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42`
- v8 JNI SHA：`26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c`

输入为固定候选 AAR ZIP及两份持久 full JADX ZIP。后者来自先核正式 APK 整包 SHA 后生成的历史分析 run；本次又核 full JADX ZIP 自身 SHA 和内部 JNI SHA。它不是“当前会话重新下载原 APK”的来源链，但实际进入 AAR 的 JNI 字节与已固定发布值完全一致。

### 安全恢复路径

`scripts/restore-published-ffmpegjni.py`：

- 要求原始 v7 / v8 发布 APK；
- 先核两份 APK 总 SHA；
- 核发布 JNI 逐文件 SHA；
- 核候选 ZIP 总 SHA；
- 只替换 decoder AAR 两个 ABI 的 `libffmpegJNI.so`；
- 其余 ZIP entry 必须逐字节不变；
- 输出必须是新文件，不自动覆盖项目依赖。

`scripts/import-player-aar-candidate.py --restored-decoder ...` 再次验证：

- 16 个候选 AAR；
- manifest / source commit；
- 候选 artifact SHA；
- restored decoder 只有两个 JNI 允许变化。

纯 Python 合成 fixture 的 APK/JADX 两条输入路径测试已经覆盖。2026-09-26 又用持久化的 v7/v8 full JADX ZIP 做了真实恢复：两份 ZIP 自身 SHA-256 均固定，内部 `libffmpegJNI.so` 又逐文件命中发布版固定 SHA。生成的 decoder AAR 只改变两个 ABI 的 `libffmpegJNI.so`，其他 entry 内容及顺序不变。

---

## 11. libXray / Go JNI 恢复

官方 libXray Android ZIP：

- version：`26.7.28`
- SHA-256：`28b7dc9d6cc8455fcca5cbd56e387003a7bfb558128651a64899dc3a8ccff666`
- 官方 XTLS/libXray build run：`30426588453`
- run commit：`80263da83e96b2972455b0a94b13ee1a10e51391`
- Android artifact：`8713908442`
- artifact digest：`95ba3c2dee0e11afea22bf2bb83947d50adf2930cfbeeb86d49edcae8b4d7e93`
- artifact 中 `libXray.aar` size：`96,258,827` bytes
- official `libXray.aar` SHA-256：`4708a361a74f7e955635dbe3661cefb459bdc867423c3b1826a2c5a6ea4ac77d`
- official AAR 已持久保存：`/FongMi-Xray/dependencies/libXray-v26.7.28-official.aar`

发布 APK 中的 Go JNI：

| ABI | 发布版 `libgojni.so` SHA-256 |
| --- | --- |
| armeabi-v7a | `6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e` |
| arm64-v8a | `40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece` |

`scripts/restore-published-libxrayjni.py`：

- official AAR 必须命中固定 `4708a361...` SHA；
- 每个 ABI 的 Go JNI 来源可二选一：
  - 原始正式 APK，先核整包 SHA；
  - 持久 full JADX ZIP，先核该 ZIP 固定 SHA；
- full JADX ZIP 只被接受是因为它来自先通过正式 APK 整包 SHA 门的历史分析 run，且本身又有固定 SHA；
- 无论来源是哪一种，提取出的 `libgojni.so` 都必须再次命中发布版固定 SHA；
- 只替换 official AAR 的 v7 / v8 两个 `libgojni.so`；
- x86 / x86_64 JNI、`classes.jar`、Manifest、resources 和所有其他 entry 必须逐字节不变；
- ZIP entry 名称和顺序必须保持不变；
- 输出到新文件，不覆盖 official AAR。

`scripts/check-libxray-gojni.py` 进一步验证：

- `libXray.LibXray.invoke(String): String` Java 方法存在；
- 两 ABI Go JNI 与发布版 SHA 匹配；
- 如果同时提供官方 AAR，则除两个 JNI 外其余 entry 与官方 AAR逐字节一致。

合成 fixture 的 APK / pinned JADX 两条输入路径测试已经通过。

2026-09-26 已完成真实本地 faithful 重包：

- 输入 official AAR SHA：`4708a361a74f7e955635dbe3661cefb459bdc867423c3b1826a2c5a6ea4ac77d`
- v7 full JADX ZIP SHA：`7aab8c3419717516167eba7cf6a6f320df894b9ef554761c0cfc98d90c580e8d`
- v8 full JADX ZIP SHA：`8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b`
- faithful AAR size：`95,011,275` bytes
- faithful AAR SHA-256：`f531a138e82fa08848e47cf22537c69df29227b07eba7d19c2ad3740af657365`
- faithful AAR 已持久保存：`/FongMi-Xray/dependencies/libXray-v26.7.28-faithful.aar`

重包后仅两个 entry 变化：

- `jni/armeabi-v7a/libgojni.so` → `6f01f219...`
- `jni/arm64-v8a/libgojni.so` → `40b08a39...`

official AAR 的 x86 / x86_64 Go JNI、`classes.jar`、Manifest、resources、proguard、R.txt 等其他 entry 均逐字节保持不变，ZIP entry 名称和顺序一致。

---

## 12. Faithful 构建链

### 本地 / 脚本入口

`scripts/build-legacy-faithful.sh` 的顺序：

1. 玩家 AAR class presence 预检；
2. FFmpeg JNI 发布版哈希门；
3. libXray Go JNI 发布版哈希门；
4. 组装固定上游 + faithful overlay；
5. 运行 Gradle。

当前默认 compile task：

`:app:assembleLeanbackArmeabi_v7aDebug`

这是恢复阶段的第一份可编译基准，不等于最终 release 发布流程。

### 手动 native dependency workflow

`.github/workflows/recovery-restore-ffmpegjni.yml`

虽然文件名保留历史命名，现在它承担 **faithful native dependency preparation**：

- 精确检查两个 Release APK asset 的名称、大小、digest；
- 检查固定 player candidate artifact 的 name、size、digest、未过期状态；
- 下载原始发布 APK；
- 恢复 FFmpeg JNI；
- 获取固定官方 libXray；
- 恢复 Go JNI；
- 输出最小 faithful native dependency artifact。

**该 workflow 当前没有实际成功运行记录，不能把 YAML 存在当成依赖已恢复。**

### 手动 faithful build workflow

`.github/workflows/recovery-build.yml`

特点：

- 仅 `workflow_dispatch`；
- 必须显式输入 native dependency artifact id；
- artifact 必须：
  - name 为 `fingmi-faithful-native-dependencies`；
  - 未过期；
  - 来自本仓库 `main`；
  - source run 必须是 `.github/workflows/recovery-restore-ffmpegjni.yml`；
  - source run conclusion 必须为 success；
- 再核固定 player candidate artifact；
- 安装 Android platform 37 + build-tools 36.0.0；
- 导入 restored decoder；
- 对比 restored libXray 与官方 AAR；
- 再跑全部依赖门；
- 运行 faithful build；
- 上传 v7 Leanback debug APK。

**截至本文当前状态，没有可确认的 faithful APK 成功构建。**

---

## 13. GitHub Actions / AC 状态

当前恢复相关 workflow：

- `recovery-apk-analysis.yml`
- `recovery-player-aars.yml`
- `recovery-restore-ffmpegjni.yml`
- `recovery-build.yml`
- `recovery-upstream-snapshot.yml`

当前恢复、分析和构建 workflow 保持 `workflow_dispatch` 手动触发。

项目所有者于 2026-09-26 更新授权：恢复工作需要的 GitHub Actions / AC 可直接执行，
无需逐次询问且不设置次数上限；包括分析、依赖准备、测试、faithful APK 编译以及有明确原因的
失败修复 / 重跑。旧的“10 次额度”“每次新的 run 先申请”和 faithful build 单独授权规则均已失效。
授权不包括把 workflow 改成 push / pull_request / schedule 自动触发，也不包括自动发布正式版本或改变产品目标。

## 13.1 历史 Actions 结果的正确解释

以下历史 run 容易因为 GitHub Actions 最终状态被误读，保留为长期溯源事实：

- APK 分析 run `36095249788` 最终为 failure，但 **v7 完整 JADX 步骤成功**；失败发生在后续 targeted dexdump 筛选。完整 v7 JADX 已保存为 artifact `10847466987`，双 ABI DEX / 报告为 `10847337361`。因此“run 红灯”不能解释为“v7 没有反编译成功”。
- Player AAR run `36123459832` 中固定 FongMi/media 源码的 **484 个 Gradle task 全部成功，BUILD SUCCESSFUL**；run 最终失败是旧 artifact 收集脚本查错输出目录，未把已编出的 AAR 带回。这个 run 证明当时源码能完成该构建，不等于已经得到可使用的候选 artifact。
- 后续经明确授权的 run `36124817040` 完整成功，产生 artifact `10859533459`，其中 16 个候选 AAR 与清单 SHA-256 一致；这是当前固定 player candidate 的来源。
- 提交标题、workflow 是否存在、或 run 总体红/绿灯，都不能替代“具体哪一步成功、实际 artifact 内容和哈希是什么”的核查。

## 13.2 高风险行为的维护规则

第 5 节已经冻结发布版行为，第 8 节记录 DEX 纠错依据，第 9 节记录恢复时最容易被“合理化重写”破坏的细节。后续维护不要再单独复制一张 commit / 风险表；需要追溯具体修改时直接查 Git 历史。

尤其不要在缺少新证据时简化 generation、timeout、private-process 收口、SOCKS unresolved hostname、DRM/RTSP 网络身份、cache/preload 边界、证书 pin 和 TV 网络恢复语义。

## 13.3 已完成的静态组装门

已完成且可重复的静态检查包括：

- 固定上游 Git 对象的 source-only faithful 组装；
- 51 个 upstream overlay 文件、24 个 Xray Java、2 个 AIDL 的组装覆盖；
- 本地提供的 `app/libs/lib-*.aar` 会被复制到 faithful 临时树，不再因上游 Git ignore 丢失；
- 六个 TV Activity 共 77 个 ViewBinding 字段引用均能在相应 layout id 中找到；
- player candidate 的检查已从早期 8 类 / 38 方法扩至当前 14 类 / 54 方法；
- 两 ABI 的 candidate player native 已完整清点为每边 11 件，其中 10 件与发布来源相同、唯一差异为 `libffmpegJNI.so`。

这些检查缩小了构建风险，但仍不能替代真实 Gradle / javac / resource merge。

## 14. 当前恢复状态

| 范围 | 当前状态 |
| --- | --- |
| 原始产品规格 | 已冻结到 `docs/ORIGINAL_README.md` |
| v7 / v8 发布 APK identity | 已固定 |
| APK reference | 已收口到 `docs/apk-reference/`，不再依赖 `recovery/generated/` |
| FongMi 5.6.0 上游基线 | 已固定 |
| Xray Java / AIDL faithful 恢复 | 主要逻辑已恢复，当前无 `DEX_VERIFY` 残留 |
| VOD / Live / Player 静态行为 | 主要发布路径已对照 |
| Binder / Service / generation / timeout | 已做 APK / DEX 静态对照 |
| 分享链接 / 证书 / 设置 / 导入 | Java faithful 已做主要静态恢复；发布 Go JNI 已确认 API v2 / inline JSON / probe 定制及 share converter 符号；native converter 输入输出执行回归仍未完成 |
| TV 待机网络恢复 | faithful 已恢复；普通工程也已接入对应 6 文件 |
| Leanback UI / 资源 | 主要资源已恢复；6 个 TV Activity 共 77 个 ViewBinding 字段已有对应 layout id 的静态检查 |
| faithful source-only 组装 | 已验证 |
| Player candidate AAR | 已取得固定候选 |
| Player selected Java API | 14 类 / 54 方法匹配 |
| Player native | 固定候选每 ABI 11 件中 10 件与发布版相同；第 11 件 FFmpeg JNI 候选不同，但已从固定发布证据恢复并生成 faithful decoder AAR；真实本地 gate 已确认只有 v7/v8 两个 `libffmpegJNI.so` entry 改变 |
| FFmpeg JNI 真包恢复 | 已从固定 full JADX 证据恢复；faithful decoder AAR 已持久保存；2026-09-26 真实本地 gate 通过，entry 名称/顺序不变且只有 v7/v8 两个 `libffmpegJNI.so` 改变 |
| libXray Go JNI 真包恢复 | 已从固定 full JADX 发布证据恢复；official / faithful AAR 均持久保存；2026-09-26 真实本地 gate 通过，Java `invoke(String): String` 存在，entry 名称/顺序不变且只有 v7/v8 两个 Go JNI entry 改变 |
| native dependency workflow | 已配置且手动；未实际成功跑完 |
| faithful Gradle build | 未完成 |
| Android TV v7 真机回归 | 未完成 |
| v8 构建 / ABI 最终验收 | 未完成 |
| 正式 `:xray` 模块迁移 | 不属于恢复完成项；faithful 过门后开始 |

历史聊天中出现过“95% / 92%”等经验比例，这些数字不作为验收标准。以本表和下面的完成条件为准。

---

## 15. Recovery 完成条件

只有同时满足以下门槛，才可以把恢复阶段标记为完成：

1. 关键发布版 APK / DEX 文本证据已经保存到仓库的 `docs/apk-reference/`，不依赖未来重新跑 AC 才能理解；
2. faithful 源码在固定上游上可以重现组装；
3. player AAR、FFmpeg JNI、libXray Go JNI 均通过固定来源 / 哈希门；
4. faithful v7 APK 至少完成一次可复现 Gradle 构建；
5. 真实编译暴露的 API / resource / ViewBinding 问题已经修正；
6. v7 Android TV 关键行为回归完成；
7. 回归至少覆盖：
   - 节点保存 / 删除 / 手机导入；
   - validate / test；
   - start / stop；
   - VOD 开关；
   - Live 开关；
   - 切集 / 自动下一集；
   - 切频道 / 源 / 线路；
   - 换播放器；
   - DRM / RTSP；
   - subtitle / danmaku / download 等 side network；
   - startup / bind / stop timeout；
   - Binder / private process death；
   - insecure certificate first trust / changed cert reject；
   - Xray 失败恢复直连；
   - 长后台 / 待机网络恢复；
8. v8 至少完成编译、ABI 和关键静态交叉验证；
9. 所有剩余差异均有明确“发布版有意差异 / 不影响 / 后续开发项”的结论；
10. 本文的“当前阻塞”归零，之后冻结恢复文档并将主工作入口切到 `DEVELOPMENT.md`。

---

## 16. 当前阻塞与下一步

### 已通过的真实本地 native gate

2026-09-26 在不启动 AC 的情况下，对两份实际 faithful 依赖重新执行真实本地校验：

- `libXray-v26.7.28-faithful.aar`
  - SHA-256：`f531a138e82fa08848e47cf22537c69df29227b07eba7d19c2ad3740af657365`
  - Java `LibXray.invoke(String): String` 存在；
  - v7 / v8 `libgojni.so` 命中固定发布 SHA；
  - 与 official AAR 相比只变化两个 v7 / v8 Go JNI entry；
  - x86 / x86_64 JNI 和所有其他 entry 逐字节不变。
- `lib-decoder-ffmpeg-release-faithful.aar`
  - SHA-256：`31a1db2570416147cc6889643d25345477977205d60a61a6df525ffa5a623a13`
  - v7 / v8 `libffmpegJNI.so` 命中固定发布 SHA；
  - 与固定 player candidate 的 decoder AAR 相比只变化两个 v7 / v8 `libffmpegJNI.so` entry；
  - ZIP entry 名称和顺序保持不变。

这说明本地 faithful native 输入已经通过内容门；发布 Go JNI 还额外通过了 API v2 / inline JSON / probe / share converter symbol 静态 gate。当前剩余的是把同样的输入通过手动 GitHub workflow 生成受来源约束的云端 native dependency artifact，再进入 faithful Gradle build。

### 阻塞 A：云端 native dependency artifact 尚未生成

按 2026-09-26 当前授权，应直接通过手动入口运行：

`recovery-restore-ffmpegjni.yml`

成功后必须先检查：

- source run；
- artifact name；
- artifact digest；
- restored decoder AAR；
- restored libXray AAR；
- FFmpeg JNI 两 ABI SHA；
- Go JNI 两 ABI SHA；
- 非 JNI entry 不变。

不能拿“workflow success”四个字直接当依赖完成证明。

### 阻塞 B：faithful build 尚未运行

native artifact 本地 / 静态复核通过后，直接运行已授权的 faithful build 手动入口。

首次目标是 v7 Leanback debug faithful compile，用来暴露真实 Java / resource / Gradle 问题。

### 阻塞 C：发布 native converter 输入输出回归尚未执行

当前已拿到两 ABI 固定发布 `libgojni.so` 并完成真实二进制静态 gate，但它们是 Android ARM ELF，
当前普通 Linux/JDK 环境不能冒充匹配执行环境。下一步需要在 Android ARM 匹配环境中，用合成节点
直接调用发布 `LibXray.invoke`，冻结“原始输入 → Java normalize/security → native JSON → runtime config”
结果，重点覆盖 KCP / VMess QR KCP、HY2、Trojan、SS/SIP003、IPv6、重复/冲突参数和错误返回。

在这项执行回归完成前，不把官方 share 源码或当前 faithful 实现自产出的 JSON 当作发布 native 的 expected。

### 阻塞 D：设备回归尚未开始

编译成功后按第 15 节回归表测试。

---

## 17. 更新本文件的规则

只在恢复事实发生变化时更新：

- 新 APK / DEX 证据改变了 faithful 结论；
- 修复了 faithful 源码偏差；
- 依赖门通过或发现新阻塞；
- native artifact 真正生成并复核；
- faithful build 真正成功 / 失败并形成有效结论；
- 设备回归状态变化；
- recovery 完成条件变化。

不要记录：

- 没产生结论的搜索过程；
- 重复的时间线；
- 已被后续结果取代的中间状态；
- 实验模块普通开发细节。

任何确定的 faithful 代码修改完成后：

1. 先及时提交代码到 `main`；
2. 再立即更新本文件对应结论；
3. 提交本文；
4. 再开始下一项。

这样下一位接手者不需要重新完整阅读仓库来判断“之前到底做到哪里”。

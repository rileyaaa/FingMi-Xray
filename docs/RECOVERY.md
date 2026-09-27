# FingMi-Xray v5.6.0 发布版恢复

本文是 v5.6.0-xray.5 faithful 恢复的唯一主文档。只记录当前有效结论、证据入口、构建门和剩余验收项；调试时间线由 Git 历史承担。

长期项目边界见 [PROJECT.md](PROJECT.md)。当前 5.6.3 main、模块化和工程规则见 [DEVELOPMENT.md](DEVELOPMENT.md)。

## 1. 固定恢复基线

### 正式发布

- FingMi-Xray：v5.6.0-xray.5
- FongMi/TV：5.6.0
- faithful versionCode：56005
- libXray / Xray-core 发布版本：v26.7.28

正式 APK：

| ABI | 文件 | SHA-256 |
| --- | --- | --- |
| armeabi-v7a | FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk | cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda |
| arm64-v8a | FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk | b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d |

固定 FongMi/TV 上游：

- commit：1a19fee278fa2234da725d61a53bf59b69fe9127
- version：5.6.0

固定官方 libXray：

- tag：v26.7.28
- commit：80263da83e96b2972455b0a94b13ee1a10e51391
- 官方 Android ZIP SHA-256：28b7dc9d6cc8455fcca5cbd56e387003a7bfb558128651a64899dc3a8ccff666
- 官方 libXray.aar SHA-256：4708a361a74f7e955635dbe3661cefb459bdc867423c3b1826a2c5a6ea4ac77d

判断发布行为时遵循 [PROJECT.md](PROJECT.md) 的可信依据顺序。

## 2. Faithful 源码

恢复源码集中在 recovery/legacy-src：

- recovery/legacy-src/upstream/：固定 FongMi 5.6.0 上游覆盖；
- recovery/legacy-src/com/fongmi/android/tv/xray/：发布版 Xray Service；
- recovery/legacy-src/com/fongmi/android/tv/xray/legacy/：可读的 helper、网络和会话控制；
- recovery/legacy-src/aidl/：发布版 Binder contract；
- recovery/legacy-tests/：恢复门测试。

当前组装范围包括：

- 51 个上游覆盖文件；
- 24 个 Xray Java；
- 2 个 AIDL；
- Leanback Manifest、布局、strings 和手机导入网页资源。

scripts/prepare-legacy-faithful.sh 从固定上游 commit 组装临时 faithful tree。source-only 组装已验证，但它不等同于 Gradle 构建成功。

当前没有遗留 DEX_VERIFY 项。已知 JADX 控制流损坏均已用更强证据收口。

## 3. 已冻结的发布行为

以下内容已由正式 APK、DEX、资源或 native 证据支持，并由 faithful 源码承载。这里的“已恢复”表示恢复实现和证据已经建立，不代表 Android TV 真机回归已经完成。

### Service、Binder 与会话

- Xray Core 位于独立 :xray 私有进程；
- VOD 与 Live 分别拥有播放会话；
- operation id 与 generation 防止旧异步结果污染新会话；
- bind timeout 约 5 秒；
- playback start timeout 30 秒；
- previous STOP cleanup timeout 1500 ms；
- settings test / security reset timeout 45 秒；
- Binder death、binding died、null binding、service disconnected 均有收口路径；
- STOP 失败、取消、Service destroy 与 private process kill 的边界已经恢复；
- daemon worker / cleanup 线程语义保留；
- 旧 STOP 不得误断已经 RUNNING 的新 START；
- stale callback 使用独立 generation 过滤。

正式 Binder descriptor：

- com.fongmi.android.tv.xray.IXrayService
- com.fongmi.android.tv.xray.IXrayCallback

### 播放网络

- Xray 仅服务当前手动开启的播放身份；
- 新集、新频道、新源、新地址、新播放器默认直连；
- Xray session 强制使用 Exo；
- HTTP(S) 使用独立 SOCKS OkHttp 资源；
- SOCKS hostname 使用 unresolved address；
- Xray session 不复用普通直连 cache / preload 身份；
- RTSP / RTSPT 使用 SOCKS SocketFactory；
- DRM license 使用当前 Xray session 的 DataSource；
- public-destination guard 拒绝 localhost、私网和保留 IPv4 / IPv6 目标；
- side-network 请求不得跨播放会话复用旧 client；
- session 结束后 cancel Dispatcher、evict ConnectionPool 并关闭 executor。

### VOD 与 Live

VOD：

- 仅在已有可播放 session 且播放器进入 READY 后允许开启；
- 切集、自动下一集、切线路、换源、刷新实际地址、真正换播放器、播放结束或离开页面均结束旧会话；
- 直连与代理切换可保留当前播放快照；
- artwork 不能跨网络身份复用。

Live：

- 切频道、线路 / 源、整套直播配置或播放器后不继承旧 Xray；
- 已播放频道可在切 proxy port 时保留当前播放；
- 正在解析频道时允许 pending start，成功后继续解析；
- Xray 启动失败不能破坏原直播放；
- EPG / XML / metadata 跟随当前播放网络身份；
- logo / artwork 避免跨网络身份混用；
- onStop / onDestroy 收口会话。

### 分享链接、设置与安全

支持的主要输入：

- VLESS；
- VMess；
- Trojan；
- Shadowsocks；
- Hysteria2 / hy2。

已恢复的兼容边界包括 legacy SS、SIP003 v2ray-plugin、VMess JSON port、HY2 默认端口 / multi-port / pinSHA256 / obfs、IPv6、URI 编码、Trojan / SS credential 加号、KCP / gRPC / Reality / XHTTP 参数等。

设置与安全：

- share link 使用 Android Keystore AES-GCM；
- preference 为 xray_secure；
- key alias 为 fongmi_xray_share_link_v1；
- 读回旧节点时再次执行兼容归一化；
- 节点测试是独立 operation，不留下 playback session；
- 删除节点同步重置 security state；
- 手机导入复用 FongMi 局域网页面；
- insecure TLS / HY2 首次信任后保存 pin，证书变化时拒绝；
- pin 比较和迁移顺序按发布行为保留；
- 错误信息会对链接、UUID、密码、token、secret、key、short id、seed 等敏感内容去敏；
- 空白判断在关键 faithful 路径按 Unicode code point + Character.isWhitespace 处理。

### Android TV 网络恢复

发布版第二核心能力已恢复：

- Activity、SCREEN_ON / SCREEN_OFF 推进网络代际；
- Home resume / focus 检查代际；
- 只替换普通 API client，不重置允许继续播放的 player client；
- 旧 client 异步 cancelAll、evictAll、shutdown；
- DNS / DoH transport 重建；
- Spider 清理后再进行首页网络稳定轮询；
- 旧 RESULT 请求取消，避免晚到覆盖新页面；
- 每 500 ms 检查一次网络；
- 连续 2 次具备 NET_CAPABILITY_INTERNET 后继续；
- 最多约 12 次，超限后也继续刷新；
- DLNA 与前后台 / screen 生命周期一起收口。

## 4. APK / DEX 证据

恢复直接需要的反编译文本统一保存在 [apk-reference/README.md](apk-reference/README.md)。原始 APK、DEX、AAR、SO 不进入普通 Git 历史。

### 关键类映射

| JADX / R8 名 | 恢复责任 | faithful 可读实现 |
| --- | --- | --- |
| yz3 | playback session、generation、timeout | LegacyXraySessionController |
| hz3 | Service bind、Binder death、bind timeout | LegacyXrayServiceClient |
| rz3 | operation result | LegacyXrayOperationResult |
| lz3 | operation id | LegacyXrayOperationIds |
| pz3 | SOCKS OkHttp resources | LegacyXrayHttpResources |
| oz3 | RTSP SOCKS SocketFactory | LegacyXrayProxySocketFactory |
| qz3 | private / reserved destination guard | LegacyPublicPlaybackDestinationInterceptor |
| lu2 | encrypted share-link store | LegacyXrayConfigStore |
| a04 | share-link normalizer | LegacyXrayShareLinkNormalizer |
| kz3 | error redaction | LegacyXrayErrorSanitizer |
| uz3 | IXrayService Binder | XrayService |
| th2 | PlayerManager / proxy transition | faithful PlayerManager |
| nq0 | Exo MediaSource factory | faithful ExoMediaSourceFactory |
| or2 | scheme guard DataSource | LegacyXraySchemeGuardDataSource |

### 已用 DEX 收口的高风险点

已确认并修正：

- Hysteria2 authority port hopping 与 mport；
- HY2 obfs / password；
- VMess JSON port；
- IPv6 authority / port；
- runtime config outbound 数量；
- TLS / HY2 certificate fingerprint；
- strict IPv4 literal helper；
- public destination guard；
- stale Binder connection 失败分支；
- TV 网络恢复控制流。

另外保留以下容易被“合理化修改”破坏的语义：

- delegate open 抛错后 DataSource 仍可 close；
- DRM setter 接受通用 DataSource.Factory；
- RTSP User-Agent、artwork scheme、Xray scheme、libXray error 的空白判断语义；
- settings timeout 先通知 UI，再 cancel 精确 operation；
- settings abandon / 手机导入不会误杀远端 operation；
-请求 / 结果对象不擅自把 null 归一化为空串或 no-op。

## 5. 播放器与 FFmpeg JNI

固定 player candidate 来源：

- FongMi/media commit：3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d
- 成功 run：36124817040
- artifact：10859533459
- artifact name：fongmi-media3-aar-candidate-1.11.0
- ZIP size：44,336,768 bytes
- ZIP SHA-256：0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee

精选 Java 接口门当前覆盖 14 类 / 54 个公开方法 descriptor。该门只证明已核调用面，不等于完整 Java ABI。

候选每个 ABI 有 11 个相关播放器 native：

- 10 个与发布版 SHA-256 一致；
- 唯一明确不同的是 libffmpegJNI.so。

发布版 FFmpeg JNI：

| ABI | SHA-256 |
| --- | --- |
| armeabi-v7a | 3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42 |
| arm64-v8a | 26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c |

已生成并本地验证 faithful decoder AAR：

- SHA-256：31a1db2570416147cc6889643d25345477977205d60a61a6df525ffa5a623a13
- 只替换 v7 / v8 两个 libffmpegJNI.so；
- 其他 ZIP entry 内容、名称和顺序保持不变。

scripts/restore-published-ffmpegjni.py 与 scripts/check-player-ffmpegjni-against-published.py 负责来源和内容门。

## 6. libXray / Go JNI

发布 APK 中的 Go JNI：

| ABI | SHA-256 |
| --- | --- |
| armeabi-v7a | 6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e |
| arm64-v8a | 40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece |

发布二进制和官方 v26.7.28 并非完全相同。已经确认的项目定制至少包括：

- Invoke API version 2；
- test / run 使用内联 xrayJson；
- pingBatch item 使用内联 xrayJson；
- TLS certificate probe；
- HY2 certificate probe；
- age subscription / key generation；
- legacy SS、HY2 multi-port / pin、ALPN / port、legacy KCP 等 share converter 兼容。

已生成并本地验证 faithful libXray AAR：

- SHA-256：f531a138e82fa08848e47cf22537c69df29227b07eba7d19c2ad3740af657365
- Java LibXray.invoke(String): String 存在；
- 只替换 official AAR 的 v7 / v8 libgojni.so；
- x86 / x86_64 JNI 与所有其他 entry 保持不变。

scripts/restore-published-libxrayjni.py 与 scripts/check-libxray-gojni.py 负责来源和内容门。

### 可读 native 行为重建的定位

仓库中的以下补丁是“依据发布二进制行为重建的可读实现”，不是找回的原始 Go 源码：

- recovery/libxray/share-converter-recovery.patch；
- recovery/libxray/native-v2-recovery.patch；
- recovery/libxray/native-age-errors.patch。

已有证据覆盖：

- v7 发布 JNI 共冻结 364 条 converter / chain / runtime 响应；
- share converter 327 / 327 差分通过；
- API v2、inline lifecycle、ping、TLS / HY2 probe、age 错误与 key 形状均有定向发布运行证据；
- lifecycle / concurrency 使用独立 barrier harness；
- HY2 有合成本地 QUIC 成功握手与证书 pin 对照；
- arm64 已完成精选 28-case 与 TLS / QUIC 交叉验证；
- v2rayN 形状输入、真实形状输入和节点 DNS / IPv6 dial 责任另有固定测试目录。

主要入口集中在：

- recovery/native-tests/；
- recovery/v2rayn-tests/；
- recovery/node-dns-tests/；
- scripts/test-recovered-libxray.py；
- scripts/test-native-abi-parity.py；
- scripts/test-v2rayn-share-chain.py；
- scripts/test-v2rayn-reference-chain.py。

这些重建源码用于理解和回归发布行为。faithful APK 继续使用固定发布 Go JNI，不使用重建 Go 产物冒充原二进制。

## 7. Faithful 构建链

### 本地入口

scripts/build-legacy-faithful.sh 依次执行：

1. player AAR 接口门；
2. FFmpeg JNI 发布哈希门；
3. libXray Go JNI 发布哈希门；
4. 固定上游 + faithful overlay 组装；
5. Gradle 构建。

默认目标为 v7 Leanback Debug faithful APK。

### 手动 Actions

Prepare faithful native dependencies：

- 文件：.github/workflows/recovery-restore-ffmpegjni.yml
- 验证正式 Release APK、固定 player artifact、FFmpeg JNI、official libXray 与发布 Go JNI；
- 输出 fingmi-faithful-native-dependencies。

Recovery faithful TV build：

- 文件：.github/workflows/recovery-build.yml
- 必须显式输入已验证的 native dependency artifact id；
- 再次核 artifact 来源、player candidate 和 native 内容；
- 组装固定 5.6.0 faithful tree 后执行 Gradle。

两者都只允许 workflow_dispatch。当前还没有可以确认的 faithful APK 成功构建。

## 8. 当前恢复状态

| 范围 | 状态 |
| --- | --- |
| 原始产品说明 | 已冻结 |
| v7 / v8 APK identity | 已固定 |
| APK / DEX 文本证据 | 已收口 |
| FongMi 5.6.0 上游 | 已固定 |
| Xray Java / AIDL faithful | 主要逻辑已恢复，无 DEX_VERIFY 残留 |
| VOD / Live / Player 静态行为 | 主要发布路径已对照 |
| Binder / Service / timeout / generation | 已对照 |
| 分享链接 / 设置 / 安全 | faithful Java 已恢复；发布 JNI 有实际运行证据 |
| TV 待机网络恢复 | faithful 已恢复 |
| faithful source-only 组装 | 已验证 |
| player candidate | 已固定并通过精选接口 / native 门 |
| FFmpeg JNI faithful AAR | 已生成并通过本地内容门 |
| libXray faithful AAR | 已生成并通过本地内容门 |
| 云端 native dependency artifact | 未生成 |
| v5.6.0 faithful Gradle build | 未完成 |
| v7 Android TV 真机回归 | 未完成 |
| v8 构建 / ABI 最终验收 | 未完成 |

当前 5.6.3 main 的成功构建属于开发线证据，只说明升级工程可以 compile / assemble，不能替代本表中的 v5.6.0 faithful 构建与设备回归。

## 9. 恢复完成条件

恢复阶段只有在以下项目全部满足后才能关闭：

1. 发布 APK / DEX 关键文本证据可在仓库中直接复核；
2. faithful 源码可从固定上游重现组装；
3. player AAR、FFmpeg JNI、libXray Go JNI 通过固定来源 / 哈希门；
4. v7 faithful APK 至少完成一次可复现 Gradle 构建；
5. 编译暴露的 Java / resource / ViewBinding 问题全部修正；
6. v7 Android TV 关键回归完成；
7. 回归覆盖节点保存 / 删除 / 导入、validate / test、start / stop、VOD、Live、切集 / 切台 / 换源 / 换播放器、DRM、RTSP、字幕 / 弹幕 / 下载旁路、timeout、Binder / 私有进程异常、证书 pin、失败回直连和 TV 待机网络恢复；
8. v8 完成构建、ABI 和关键路径交叉验证；
9. 所有剩余差异都有明确结论。

## 10. 当前下一步

恢复线按以下顺序继续：

1. 手动运行 Prepare faithful native dependencies；
2. 核对产物名称、来源 run、digest、两份 AAR 和四个关键 JNI SHA；
3. 把该 artifact id 交给 Recovery faithful TV build；
4. 修正真实 Gradle 编译问题直到 v7 faithful APK 可构建；
5. 执行 v7 Android TV 回归；
6. 完成 v8 构建 / ABI 最终核验。

原始定制 Go 源码没有找回，但这不阻止 faithful APK 使用已固定的发布 Go JNI。可读重建继续作为行为解释和回归证据，不作为“原源码已恢复”的宣称。

## 11. 本文维护规则

只在 faithful 事实发生变化时修改本文，例如：

- 新证据改变发布行为结论；
- faithful 源码偏差被修正；
- 依赖门状态变化；
- native dependency artifact 真正生成并复核；
- faithful build 得到新结论；
- 设备回归状态变化。

不要在本文追加逐次搜索、每次 commit 的过程说明、普通 5.6.3 开发细节或已经被后续结论取代的中间状态。

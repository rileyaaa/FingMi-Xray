# README / APK / Legacy 行为对照矩阵

本文件把项目根目录 `README.md` 中记录的产品行为，与最终发布 APK
`v5.6.0-xray.5` 的反编译证据以及当前可读 legacy 恢复源码绑定在一起。

恢复阶段的优先级：

1. **最终 APK 实际行为**：运行时事实，优先级最高。
2. **README 明确描述**：用于确认当时的设计意图、修复目标和用户可见语义。
3. **当前恢复源码**：必须同时满足前两项；不允许因为“重构更漂亮”而提前简化。

状态：

- ✅ **APK 已验证 / 已恢复**：README 行为已有 APK 证据并有 legacy 可读源码承载。
- 🟨 **APK 已验证 / 仍需最终构建验证**：逻辑已恢复，但还需要未来 faithful build 做集成验证。
- 🟦 **README 设计说明**：属于使用边界/设计意图，APK 主要通过结构和“没有某组件”来佐证。
- ⬜ **待继续核对**：不能只凭 README 推断。

---

## 核心产品边界

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| 基于 FongMi/TV 5.6.0 | 发布 APK/资源版本与恢复基线均为 5.6.0；历史基线已锁定 | 整个 `recovery/legacy-src/upstream/` 以 5.6.0 可读源码为载体 | ✅ |
| Xray 使用独立 `:xray` 私有进程 | Manifest 中 `.xray.XrayService android:process=":xray"` | `upstream/app/src/leanback/AndroidManifest.xml`、`com/fongmi/android/tv/xray/XrayService.java` | ✅ |
| 不创建 Android 系统 VPN | APK Manifest 无 Xray VpnService；播放网络通过本地 SOCKS 注入 Exo 网络层 | `LegacyXrayHttpResources`、`PlayerEngineFactory`、`ExoPlayerSession` | 🟦 |
| 不全局接管设备网络 | Xray client 只存在于当前 Exo session；普通 API 仍使用全局普通 OkHttp | `PlayerManager.getHttpClient()`、`LegacyXrayHttpResources`、`PlaybackActivity` | ✅ |
| 只服务当前手动开启的媒体会话 | 每个 Video/Live Activity 各有 `yz3` session owner；切换播放身份会 stop/reset | `LegacyXraySessionController`、legacy `VideoActivity`、legacy `LiveActivity` | ✅ |

## Xray 进程、Binder 与资源释放

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| 会话结束后停止 Xray Core | `sz3/tz3/XrayService` operation 4；Core stop 有重试 | `XrayService`、`LegacyLibXrayApi` | ✅ |
| 清理 SOCKS、本地连接、Socket、HTTP 连接 | Xray Exo session 使用独立 Dispatcher / ConnectionPool / SOCKS client；release 后 shutdown/cancel/evict | `LegacyXrayHttpResources`、`LegacyXrayProxySocketFactory` | ✅ |
| 回收 libXray / Go Runtime 资源 | 私有进程在无法可信清理、取消 native 工作或 Service destroy 时可自杀 | `XrayService`、`LegacyXrayGenerationGate` | ✅ |
| Xray 不长期驻留后台 | Service session 结束后 Core stop；必要时 kill `:xray` | `LegacyXrayServiceClient`、`XrayService` | ✅ |
| 防止旧异步结果污染新会话 | playback/settings 两套 generation gate + operation id | `LegacyXrayOperationIds`、`LegacyXrayGenerationGate`、`LegacyXraySessionController` | ✅ |
| Binder 异常能自恢复/收口 | bind timeout、linkToDeath、binding died、null binding、stale callback 过滤 | `LegacyXrayServiceClient` | ✅ |
| 播放启动超时 | 最终 APK startup timeout 30s | `LegacyXraySessionController` | ✅ |
| 设置测试/安全重置超时 | 最终 APK 45s | `LegacyXraySettingsController` | ✅ |

## 播放地址和播放器网络

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| Xray 只代理真正媒体播放连接 | `th2/sq0/pz3` 只把 session port 注入播放器 engine | `PlayerManager`、`PlayerEngineFactory`、`ExoPlayerEngine` | ✅ |
| Xray 播放强制 Exo | port > 0 时 engine factory resolve 为 Exo；非 Exo session client 不可用 | `PlayerEngineFactory`、`PlayerEngine.getXrayHttpClient()` | ✅ |
| SOCKS hostname 保持 unresolved | `InetSocketAddress.createUnresolved` + 自定义 RTSP SocketFactory | `LegacyXrayHttpResources`、`LegacyXrayProxySocketFactory` | ✅ |
| 阻止 localhost / 私网 / 保留地址绕进代理 | APK `qz3` 对 IPv4/IPv6 保留网段逐项过滤 | `LegacyPublicPlaybackDestinationInterceptor` | ✅ |
| 实际媒体支持 HTTP/HTTPS/RTSP/RTSPT | APK URL 资格判断不仅含 HTTP(S)，还含 RTSP/RTSPT | `LegacyXrayPlaybackAddress` | ✅ |
| Live 原始地址不能把需 FongMi 二次解析的链接直接塞入 Xray | APK 对 HTTP(S) `.strm`、YouTube/youtu.be 额外排除 | `LegacyXrayPlaybackAddress.isDirectLiveSourceSupported()` | ✅ |
| Xray session 不做下一集预加载 | APK Xray port/session active 时 preload 被禁用 | `PlayerManager.canPreloadNext()`、`ExoPlayerEngine` | ✅ |

## 点播 VOD

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| 播放菜单手动开启 Xray | VideoActivity 最终 binding/action 含 `xray` | legacy `VideoActivity` + `view_control_vod_action.xml` | ✅ |
| 只有已有可播放会话且播放器 READY 后才能开 | APK `f3153W` 在 Player READY 置 true；菜单还检查 PlaySpec/session | legacy `VideoActivity.xrayPlaybackReady` | ✅ |
| 下一集/上一集不会继承 Xray | controller 切 episode 前 reset Xray | `VodPlaybackController` + `VodPlaybackHost.resetXrayForPlaybackChange()` | ✅ |
| 自动下一集不会继承 | playback ended -> next episode -> 同一 reset 路径 | `VodPlaybackController`、legacy `VideoActivity` | ✅ |
| 切线路不会继承 | flag/line select 会 reset | `VodPlaybackController.selectFlag()` | ✅ |
| 换源/换实际地址不会继承 | source/refresh 路径 reset | `VodPlaybackController.switchSource()/refresh()` | ✅ |
| 更换播放器结束 Xray | 最终 PlayerEngineDialog 只有 engine 真变更时先回调 reset | legacy `PlayerEngineDialog` + legacy `VideoActivity.onPlayer()` | ✅ |
| 播放结束结束 Xray | Player.STATE_ENDED 清 READY 并 stop session | legacy `VideoActivity.onStateChanged()` | ✅ |
| 离开页面/后台状态变化结束 Xray | `onStop` 调 session stop；可只保留正常直连播放快照 | legacy `VideoActivity.onStop()` | ✅ |
| Xray 切换期间避免封面图走错网络 | APK 存储 Glide target；Xray session 时停止新 artwork 请求 | legacy `VideoActivity.mArtworkTarget/setArtwork()` | ✅ |
| 开启 Xray 后点播不一定可播，可手动关闭回直连 | Xray port 可带 preserve snapshot 切回 0 | `PlayerManager.setXrayPort(0, preserve)` | ✅ |

## 直播 Live

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| Xray 与“切换源”同级菜单 | 最终 live action binding 含 Xray 控件 | legacy `LiveActivity` + `view_control_live_action.xml` | ✅ |
| 切频道不继承上一频道 Xray | live request reset 参数默认 true | `LivePlaybackController` | ✅ |
| 切直播源/线路不继承 | line/source request reset Xray | `LivePlaybackController.switchLine()` | ✅ |
| 更换整套直播配置结束 Xray | APK setLive 路径先 stop/reset | legacy `LiveActivity.setLive()` | ✅ |
| 更换播放器结束 Xray | APK PlayerEngineDialog change callback -> stop/reset + logo restore | legacy `PlayerEngineDialog` + `LiveActivity.onPlayer()` | ✅ |
| 正在已有频道播放时开启 Xray | RUNNING 后 port transition preserve=true | legacy `LiveActivity.onXrayState()` | ✅ |
| 频道还在解析时开启 Xray | APK `f3113o0`；成功后 resubmit pending request with resetXray=false | `LivePlaybackController.resumeChannelAfterXrayStart()`、legacy `LiveActivity` | ✅ |
| Xray 启动失败时不破坏原本正常直播放 | APK `f3114p0` 区分“已有播放”与“本来就没 session” | legacy `LiveActivity.mXrayStartedFromExistingPlayback` | ✅ |
| EPG/XML 与媒体 session 使用一致网络 | APK Live metadata API 接收当前 PlayerManager client | `LiveApi`、`EpgParser`、`LiveViewModel` | ✅ |
| Xray 切换时取消旧 metadata，但不误杀当前 URL resolver | APK 只取消 XML/EPG task；metadata tag 在 normal/Xray 两个 client 都 cancel | `LiveViewModel.cancelXrayMetadataRequests()`、legacy `LiveActivity` | ✅ |
| Xray 时频道 logo / 当前 logo / artwork 不混用旧网络 | APK `m2002U1` + stored Glide target | `ChannelAdapter.setXrayLogoSuppressed()`、legacy `LiveActivity` | ✅ |
| onStop / onDestroy 收口 | APK `m1995N1` + session dispose | legacy `LiveActivity.onStop()/onDestroy()` | ✅ |

## 节点设置、兼容和安全

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| 设置中添加/修改单节点分享链接 | `SettingXrayActivity` + encrypted preferences | `LegacyXrayConfigStore`、legacy `SettingXrayActivity` | ✅ |
| 主要兼容 v2rayN 导出的标准单节点链接 | README 明确设计目标；APK normalizer 包含多种现实兼容修补 | `LegacyXrayShareLinkNormalizer` | 🟦 |
| VLESS | normalizer whitelist | `LegacyXrayShareLinkNormalizer` | ✅ |
| VMess | whitelist + base64 JSON port validation | 同上 | ✅ |
| Trojan | TLS normalize + credential `+` 修复 | normalizer + `LegacyXrayRuntimeConfigFactory` | ✅ |
| Shadowsocks | legacy base64 + SIP003 v2ray-plugin -> Xray transport 参数 | normalizer | ✅ |
| Hysteria2 / hy2 | default 443、port hopping、mport、pin、obfs 等 | normalizer + transport security | ✅ |
| 节点测试 | Binder operation 2 + latency result | `LegacyXraySettingsController`、`XrayService` | ✅ |
| UDP 开关 | secure config store + settings UI | `LegacyXrayConfigStore`、legacy `SettingXrayActivity` | ✅ |
| 删除节点同时清安全状态 | operation 5 + pin/key reset | `LegacyXraySettingsController`、`LegacyXrayCertificateStore` | ✅ |
| insecure TLS 首次证书 pin、后续变更拒绝 | APK libXray probe + encrypted pin store + constant-time compare | `LegacyXrayTransportSecurity`、`LegacyXrayCertificateStore` | ✅ |

## 手机导入

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| 复用手机/电视局域网页面导入，不另起第二套 Server | PushActivity `tab=6` | legacy `PushActivity` | ✅ |
| 网页提交 Xray share link | server Action `do=xray` -> XrayImportEvent | `server/process/Action.java`、`XrayImportEvent.java` | ✅ |
| 导入时不应让旧测试结果覆盖新输入 | settings-side generation/abandon 逻辑 | `LegacyXraySettingsController`、legacy `SettingXrayActivity` | ✅ |
| 相关网页静态资源已恢复 | APK assets index/script 差异 | `recovery/legacy-src/upstream/app/src/main/assets/` | ✅ |

## Android TV 待机 / 长后台网络恢复

| README 行为 | 最终 APK 证据 | Legacy 恢复源码 | 状态 |
| --- | --- | --- | --- |
| Fast Start / SCREEN_OFF / 全部 Activity 后台后不继续盲用旧网络 | `gn3` ActivityLifecycleCallbacks + SCREEN_ON/OFF receiver | `TvNetworkLifecycle` | ✅ |
| 回前台后判断是否跨过一个网络代际 | HomeActivity 保存/比较 generation；onResume + window focus 双触发 | legacy `HomeActivity` | ✅ |
| 清旧 Socket / HTTP 连接 | `TvNetworkCleanup` daemon executor | legacy catvod `OkHttp` | ✅ |
| 重建 DNS / DoH 环境 | APK `ha2` 销毁旧 DoH client 并保留配置重建 | legacy `OkDns` | ✅ |
| 清 Spider 自己持有的旧网络运行时 | APK `C1145ma.m6157p()` 销毁 Jar/JS/Python Spider + cache | legacy `BaseLoader.clear(callback)` | ✅ |
| 防止旧首页请求晚到覆盖新页面 | recovery 前取消 RESULT future | legacy `SiteViewModel.cancelResultRequest()` | ✅ |
| 等系统网络稳定再重新请求 | 每 500ms；连续 2 次 INTERNET；最多约 12 次 | legacy `HomeActivity` | ✅ |
| 不误杀允许继续的后台媒体播放 | Home recovery 只替换 normal API client，不 reset player client | legacy `OkHttp.resetApiNetworkForResume()` | ✅ |
| DLNA 服务随真正前后台/SCREEN 状态收口 | `gn3` start/stop DLNARendererService | `TvNetworkLifecycle` | 🟨 |

## 资源 / Manifest / UI 补丁

| 内容 | APK 证据 | Legacy 恢复位置 | 状态 |
| --- | --- | --- | --- |
| Xray 设置 Activity | Manifest + decompiled Activity | `upstream/app/src/leanback/AndroidManifest.xml`、legacy SettingXrayActivity | ✅ |
| `:xray` Service | Manifest | legacy Manifest + XrayService | ✅ |
| 设置页 Xray 入口 | activity_setting resource | `upstream/app/src/leanback/res/layout/activity_setting.xml` | ✅ |
| VOD 菜单 Xray | view_control_vod_action | 对应 legacy layout | ✅ |
| Live 菜单 Xray | view_control_live_action | 对应 legacy layout | ✅ |
| 简中 / 繁中 / 默认 strings | APK resources | legacy values / values-zh-rCN / values-zh-rTW | ✅ |
| 手机导入 assets | APK assets | legacy `assets/index.html` + `assets/js/script.js` | ✅ |

---

## 仍需完成的“恢复阶段”工作

目前 Java 行为和 Leanback 资源已经接近完整，但**还不能宣布 faithful recovery 完成**。开始正式架构重构前仍需：

1. 对所有 legacy 源码做一次统一静态编译/签名检查，修掉恢复过程中产生的 API 名称漂移。
2. 对 `LegacyXrayShareLinkNormalizer` 中仍标记为 decompiler-repaired 的条件继续用 DEX/smali 验证。
3. 将 legacy 资源/Manifest/Java 补丁组装成一套真正可构建的 5.6.0 TV faithful variant。
4. 只在一个恢复里程碑上集中跑一次 GitHub Actions，避免持续消耗免费额度。
5. 用发布 APK 做行为回归：节点兼容、启动/停止、切集、切台、换源、换播放器、后台/待机恢复、进程死亡、失败/超时、证书 pin。
6. faithful build 通过后，再把行为逐块迁移到当前 `:xray` 模块；每迁移一块必须由本矩阵对应的回归项兜底。

> README 是设计意图和用户可见行为的重要依据，但当 README 与 APK 在细节上不一致时，以最终发布 APK 的实际运行逻辑为准。

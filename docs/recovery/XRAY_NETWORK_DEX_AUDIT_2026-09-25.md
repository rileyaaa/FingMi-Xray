# Xray 与电视待机网络路径：发布版 DEX 对照（2026-09-25）

## 证据及范围

- 对照发布 APK v7 的完整 JADX 工件 `10847466987`，并用 v7/v8 原始 DEX 工件 `10847337361` 检查 JADX 易误读的控制流。v7 `classes.dex` SHA-256 为 `e4a3e51121c2e0ff53b751bf38ea5f067086acbe8540d6f1405025205b969644`。
- 这次只审计下列可定位路径；静态匹配不代表 APK 已编译或电视设备回归成功。反编译的 `p000` 混淆名仅作定位，不是新源码的正式 API。

## 电视网络恢复：确认，无需改动

| 原版定位 | 直接证据 | 对恢复层的结论 |
| --- | --- | --- |
| `Ll61;->run`，首页网络检查 | DEX 方法 `code_off=3177084`、`insns_size=204`；code-unit `0x83` 调用 `App.post` 排下一轮检测后，`0x86` 的 `goto +0x2f` 跳到 `0xb5` 的 `return-void`。JADX 的平铺显示容易误以为会继续加载首页。 | 网络尚不稳定时只重排检测并返回；恢复的提前 `return` 符合原始 DEX。 |
| `Lyd0;->run`，旧 HTTP 客户端清理 | DEX 方法 `code_off=2526188`、`insns_size=806`；code-unit `0x3d` `Dispatcher.cancelAll`，`0x44` `ConnectionPool.evictAll`，`0x4f` `ExecutorService.shutdown`。 | 恢复的 OkHttp 异步清理覆盖这三步，未见顺序漂移。 |

JADX 的 `gn3`/屏幕广播链路表明亮屏或 Activity 重回前台会推进网络代际并管理 DLNA；首页网络检查和 `la2`/`ha2` DoH 清理需与此配合。恢复层分别放在 `TvNetworkLifecycle`、Home 和 HTTP/DNS 适配中；这些是 app 的网络恢复行为，不应整体移入 Xray 模块。

进一步核对 `HomeActivity.m1976O0`（发布版）与恢复的 `HomeActivity.checkNetworkGeneration()`：仅把普通 API 客户端置空，保留独立播放器客户端；按当前 DoH supplier/配置刷新 DoH，异步清理旧客户端；使用 `RunnableC0541f7` 在 Jar/JS/Python Spider 清理完成后才把首页检查排入主线程。`l61` 网络检查要求连续两次 `NET_CAPABILITY_INTERNET`，最多重新排队 12 次、每次 500 ms；超限后继续刷新首页，即使网络能力仍未恢复。这符合恢复层 `mStableNetworkChecks`、`mRecoveryChecks` 的门槛；**不能误写成必须等到网络真正可用才刷新**。退出或 Activity 销毁期间不再启动此轮首页加载。`gn3` 第一 Activity 启动及亮屏代际控制与恢复的 `TvNetworkLifecycle` 也一致。以上是静态对照，没有长时间待机设备验证。

## Xray 会话及服务：本轮已核静态点

- 发布版 `yz3` 负责会话代际、待完成的 stop 与 start 超时；`vz3` 调度清理超时 `1500L` 和启动超时 `30000L`。恢复的 `LegacyXraySessionController` 两个限时值与此相同。
- 发布版 `XrayService` START/STOP 的操作代际检查、销毁时失效代际、异步 stop、最多等待 3 秒及销毁独立 `:xray` 进程，和恢复层的既有生命周期方向一致。这只是选取关键路径核对，尚未宣称节点配置、Binder 回调、所有并发竞态或 APK 行为完全一致。
- 原始 v7 DEX `XrayService.e`（JADX `m2091e`）的 `code_off=5376512`：`0x1d`/`0x26` 的 `AtomicLong.compareAndSet` 只在匹配操作代际时继续，`0x31`/`0x38` 置无效代际，`0x3f` 调用 `Process.killProcess`。`XrayService.onDestroy` 的 `code_off=5376300`：`0x0b`/`0x14` 失效两门，`0x1f` 提交 stop 任务，`0x22` shutdown，`0x29` awaitTermination（传入 3 秒），`0x2f` 或中断分支 `0x47` shutdownNow，最终 `0x3c`/`0x52` killProcess。这些是发布版在进程收口上的直接 DEX 证据；恢复层保留相同顺序。
- 发布版 `tz3.run` 停止操作：旧 STOP 代际直接成功回调，当前 STOP 最多经 `XrayService.m2092g` 的内部重试后成功回调；停止失败而失败消息**已经送达**主进程时，服务不抢先 kill，而主进程 `yz3` 收到失败后对精确 id 执行 cancel 并结束私有进程；失败消息送不到时服务自行 cancel/kill。恢复的 `XrayService.stopInternal` 和 `LegacyXraySessionController.onOperationResult` 保留此二段收口。此处仅静态控制流对照。
- 发布版 `hz3`/`ez3`/`dz3` 的服务绑定、Binder 死亡/断开、5 秒绑定超时、回调代际检查，以及 `uz3` 操作 1–6 的 Binder 分发，已与 `LegacyXrayServiceClient`/`XrayService` 逐路径静态比对。晚到的旧回调在主线程再次比较绑定代际；恢复层也在派发时捕获代际、在主线程比较后转发。此项不代表并发设备实测。

### 配置工厂出口计数条件：v7/v8 原始 DEX 消除 JADX 歧义

`XrayService.b`（JADX 显示 `m2089b`）在 v7 和 v8 的 `classes.dex` 中，方法 `code_off=5371464`，`insns_size=2322`；两个 ABI 此方法以下 code-unit 指令相同：

| 条件 | 指令 offset | 跳向 | 意义 |
| --- | --- | --- | --- |
| `converted.optJSONArray("outbounds")` 后 `if-eqz v1` | `0x6a9` | `0x902` | 缺数组则报转换后出口数错误 |
| `JSONArray.length()` 后 `const/4 v14, #1` 与 `if-ne v6, v14` | `0x6b0` | `0x902` | 非单出口则同样报错 |
| 复制配置后第二次 `optJSONArray`，`if-eqz v1` | `0x712` | `0x8e2` | 缺数组则报“Exactly one Xray outbound is required” |
| 第二次 `length()` 后 `const/4 v14, #1` 与 `if-ne v2, v14` | `0x719` | `0x8e2` | 非单出口则同样报错 |

因此恢复的 `LegacyXrayRuntimeConfigFactory` 两处 `outbounds == null || outbounds.length() != 1` 正确。JADX 产物在这一段出现 `outbounds != null || ...` 和空 `if`，不能作为语义证据。复核可在原 DEX 工件上运行 `python3 scripts/inspect-published-dex.py v7-v8-dex.zip v7-dex/classes.dex 'Lcom/fongmi/android/tv/xray/XrayService;' b x --decode-from 0x6a5 --decode-to 0x6b9`，把 member 改成 `v8-dex/classes.dex` 再做交叉核对；此工具仅做部分 opcode 的定位显示，不是完整反汇编器。v8 `classes.dex` SHA-256 为 `ad5bf878ba1d5638068c8c204e4488f5aa51733d8379f2cc2c72d6ecf1fb113e`。

### Hysteria2 首次证书探测：拒绝无效 SHA-256，保留原样存储 pin

同一原始方法 `XrayService.b` 的 v7/v8 code-unit `0x25d` 调用 `String.matches` 检查探测得到的 SHA-256 文本；`0x261` `if-eqz` 在不匹配时跳到 `0x2bc` 创建“invalid fingerprint”异常。JADX 对该条件曾显示为“匹配时抛错”，属于反编译颠倒。后续 `0x263` 对新探测值 `toLowerCase`；已保存 pin 路径在 `0x287` 检查合法格式、`0x28f`/`0x293` 分别取字节、`0x297` `MessageDigest.isEqual`，`0x29b` 不相同时跳到证书变化错误。恢复的 `LegacyXrayTransportSecurity.verifyOrTrust` 对新值小写化、对旧存储文本不改写、以 ASCII 字节比较并拒绝变更，符合这段发布版指令。证书握手/Android Keystore 仍须设备回归。

TLS 探测同理：`0x5a5` `String.matches`、`0x5a9` `if-eqz` 跳无效指纹异常 `0x5f8`；新的指纹转小写后，旧存储指纹在 `0x5cc` 验格式，`0x5d4`/`0x5d8` 取两份字节，`0x5dc` `MessageDigest.isEqual`，`0x5e0` 不相同则拒绝。双 ABI 对应代码段相同；只证明这一段的分支，不推出证书探测 API 在设备上成功。

## 下一步

继续核 `yz3` 的竞态、节点安全和 libXray 调用参数；如果发现确证偏差，修复 faithful 层并在此文或 `DEBUG_HISTORY.md` 记录 DEX/JADX 定位。尚缺 `libXray.aar`、完整资源/Java ABI 检查、APK 编译和设备回归。本轮没有运行新的 AC。

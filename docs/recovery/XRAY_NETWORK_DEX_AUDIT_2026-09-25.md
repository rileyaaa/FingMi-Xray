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

## Xray 会话及服务：本轮已核静态点

- 发布版 `yz3` 负责会话代际、待完成的 stop 与 start 超时；`vz3` 调度清理超时 `1500L` 和启动超时 `30000L`。恢复的 `LegacyXraySessionController` 两个限时值与此相同。
- 发布版 `XrayService` START/STOP 的操作代际检查、销毁时失效代际、异步 stop、最多等待 3 秒及销毁独立 `:xray` 进程，和恢复层的既有生命周期方向一致。这只是选取关键路径核对，尚未宣称节点配置、Binder 回调、所有并发竞态或 APK 行为完全一致。

## 下一步

继续核 `hz3`/`uz3` Binder 断线重连、`yz3` 竞态和 libXray 调用参数；如果发现确证偏差，修复 faithful 层并在此文或 `DEBUG_HISTORY.md` 记录 DEX/JADX 定位。尚缺 `libXray.aar`、完整资源/Java ABI 检查、APK 编译和设备回归。本轮没有运行新的 AC。

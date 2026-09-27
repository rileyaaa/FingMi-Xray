# 发布 APK 反编译证据索引

本目录保存 v5.6.0-xray.5 两份正式 APK 中与 faithful 恢复直接相关的文本证据。

这里的内容用于复核发布行为，不是维护源码。可读 faithful 实现位于 recovery/legacy-src，恢复结论统一维护在 [../RECOVERY.md](../RECOVERY.md)。

## 固定 APK

| ABI | 文件 | SHA-256 | 用途 |
| --- | --- | --- | --- |
| armeabi-v7a | FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk | cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda | 主恢复与设备回归基准 |
| arm64-v8a | FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk | b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d | ABI、DEX 与 native 交叉验证 |

## 已持久保存的完整分析材料

历史 Actions：

- v7 完整 JADX：artifact 10847466987；
- v7 / v8 DEX + APK diff：artifact 10847337361；
- v8 完整 JADX：artifact 10825963688。

对应完整 ZIP 另有项目 Library 持久副本：

| 内容 | Library 路径 | bytes | ZIP SHA-256 |
| --- | --- | ---: | --- |
| v7 full JADX | /FongMi-Xray/apk-reference/v7-full-jadx-v5.6.0-xray.5.zip | 76,359,062 | 7aab8c3419717516167eba7cf6a6f320df894b9ef554761c0cfc98d90c580e8d |
| v8 full JADX | /FongMi-Xray/apk-reference/v8-full-jadx-v5.6.0-xray.5.zip | 78,694,282 | 8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b |
| v7 / v8 DEX + reports | /FongMi-Xray/apk-reference/v7-v8-dex-report-v5.6.0-xray.5.zip | 11,501,328 | 699eac1ef5d8261c303d953110fa8ec731f91cd7279c04a74c598311211a4c3f |

Library 副本只是跨会话材料来源。正式 APK 的固定 SHA-256 仍是发布身份依据。

历史 v7 分析 run 最终为 failure，是因为后续 targeted dexdump 筛选失败；完整 JADX sources 已正常生成并保存。不要把 run 最终红灯解释为“v7 没有反编译成功”。

## 仓库保存范围

仓库从两份完整 JADX 中选取 64 个与恢复直接相关的 Java 文件，覆盖：

- Xray Service / Binder / session；
- share-link / runtime config / certificate / error sanitizer；
- PlayerManager / Exo / SOCKS / destination guard；
- VOD / Live / Setting / Push；
- libXray Java bridge 数据类；
- TV 待机网络恢复相关 Home / lifecycle / HTTP / DNS R8 helper。

双 ABI 对照：

- selected source：64；
- v7 / v8 逐字节相同：63；
- 差异：1；
- 缺失：0；
- AndroidManifest：逐字节相同。

唯一差异是 p000/ip0.java，对应 R8 EventBus subscriber index。注册项相同，只是 HashMap.put 顺序不同，因此其余 63 个 selected source 只保存一份。

## 目录说明

- shared/sources/：两 ABI 相同的 selected JADX；
- shared/AndroidManifest.xml：两 ABI 相同的反编译 Manifest；
- shared/dex-sha256.txt：两边 classes DEX SHA-256；
- shared/apk-diff.txt：在核正式 APK SHA 后生成的 ZIP entry 差异；
- shared/source-parity.txt：selected source 对照结论；
- v7/ip0.java、v8/ip0.java：唯一 selected-source 差异；
- native-share-symbols.json：发布 JNI 中 share / Invoke 相关 Go symbol、源码行和地址索引。

native 行为 fixture、重建补丁和执行脚本不放在本目录，统一位于 recovery/native-tests、recovery/libxray 及 scripts；结论见 RECOVERY.md。

## 使用规则

1. 先确认正式 APK SHA，再使用对应证据。
2. 查询发布 Java 语义时优先查本目录。
3. JADX 出现明显矛盾时继续核 RECOVERY.md 已记录的 DEX / native 结论，必要时再运行检查脚本。
4. 不把 R8 类名当长期 API。
5. 不直接把未经核对的 JADX 复制成维护源码。
6. 不在 Git 中提交原始 APK、classes.dex、AAR、SO 等大型二进制。
7. 本目录只维护证据索引和必要文本，不记录项目当前开发进度或调试时间线。

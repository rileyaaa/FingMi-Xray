# 发布 APK 反编译参考

本目录保存 FingMi-Xray `v5.6.0-xray.5` 两个正式发布 APK 中，**与本项目恢复直接相关的文本证据**。

目的：

- 后续 Chat / Work / Codex 不需要为了重新查看关键发布版逻辑再跑 GitHub Actions；
- 为 `docs/RECOVERY.md` 的 faithful 结论提供可直接检索的 APK / JADX / DEX 依据；
- 保留双 ABI 对照结果，但避免在 Git 中重复保存几乎相同的反编译源码。

这里的文件是反编译证据，不是维护源码。真正的 faithful 可读实现仍在 `recovery/legacy-src/`。

## 正式 APK

### armeabi-v7a（主基准）

- 文件：`FongMi-Xray-TV-v5.6.0-xray.5-armeabi-v7a.apk`
- SHA-256：`cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda`
- 实际使用架构，也是恢复和设备回归主基准。

### arm64-v8a（交叉验证）

- 文件：`FongMi-Xray-TV-v5.6.0-xray.5-arm64-v8a.apk`
- SHA-256：`b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d`
- 用于关键源码、DEX、ABI 和 native 交叉验证。

## 证据来源

已有历史 Actions artifact：

- v7 完整 JADX：`10847466987`
- v7 / v8 原始 DEX + APK diff：`10847337361`
- v8 完整 JADX：`10825963688`

这些 artifact 可能过期，因此本目录保存恢复直接需要的文本材料。同时已将三份完整 ZIP 持久保存到项目可访问 Library，供 selected reference 不足时离线查阅：

| 内容 | Library 路径 | bytes | ZIP SHA-256 |
| --- | --- | ---: | --- |
| v7 full JADX | `/FongMi-Xray/apk-reference/v7-full-jadx-v5.6.0-xray.5.zip` | 76,359,062 | `7aab8c3419717516167eba7cf6a6f320df894b9ef554761c0cfc98d90c580e8d` |
| v8 full JADX | `/FongMi-Xray/apk-reference/v8-full-jadx-v5.6.0-xray.5.zip` | 78,694,282 | `8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b` |
| v7/v8 DEX + reports | `/FongMi-Xray/apk-reference/v7-v8-dex-report-v5.6.0-xray.5.zip` | 11,501,328 | `699eac1ef5d8261c303d953110fa8ec731f91cd7279c04a74c598311211a4c3f` |

Library 是跨会话便利副本，不替代发布 APK 的固定 SHA 身份；判断发布行为仍以本文件上方两份正式 APK SHA 为准。

v7 JADX 工作流记录的 JADX exit code 为 3，但完整 `sources/` 已正常生成并保存；历史 Action 红灯发生在后续 targeted dexdump 筛选，不等于 v7 没有反编译源码。

## 保存范围

从两份完整 JADX 中选取了 64 个与以下范围直接相关的 Java 文件：

- Xray Service / Binder / session；
- share-link / config / certificate / error sanitizer；
- player manager / Exo media source / SOCKS / destination guard；
- VOD / Live / Setting / Push 关键 Activity；
- libXray Java bridge 数据类；
- TV 待机网络恢复的 Home / lifecycle / HTTP / DNS 相关 R8 helper。

逐文件比较结果：

- selected source files：64
- v7 / v8 逐字节相同：63
- 不同：1（`p000/ip0.java`）
- 缺失：0
- AndroidManifest：双 ABI 逐字节相同

`ip0` 是 R8 生成的 EventBus subscriber index；已核注册项相同，差异只在 `HashMap.put` 顺序。因此其他 63 个文件只保留一份到 `shared/sources/`。

## 目录

- `shared/sources/`：双 ABI 完全相同的 selected JADX 源码；
- `shared/AndroidManifest.xml`：双 ABI 相同的反编译 Manifest；
- `shared/dex-sha256.txt`：两边三个 DEX 的 SHA-256；
- `shared/apk-diff.txt`：在核两份 APK 总 SHA 后生成的 ZIP entry 差异摘要；
- `shared/source-parity.txt`：selected source 对照范围和结论；
- `v7/ip0.java`、`v8/ip0.java`：唯一 selected-source 差异。
- `native-share-symbols.json`：发布 v8 JNI 的 share/helper/Invoke 清理函数 Go symbol、定制源码行与虚拟地址；实际执行 fixture、局部 Go patch、复现命令及边界统一维护于 `../RECOVERY.md` 第 11 节和 `recovery/native-tests/`。

## 使用规则

1. 需要确认发布版语义时先查本目录，不要先跑 AC。
2. JADX 出现不可能条件或控制流冲突时，继续查 `RECOVERY.md` 已记录的原始 DEX 结论；必要时才使用 `scripts/inspect-published-dex.py` 配合已固定 DEX 证据。
3. 不把反编译类名当正式 API。
4. 不直接复制 unreviewed JADX 到维护源码。
5. 本目录不提交原始 APK、`classes*.dex`、AAR、SO 等大型二进制；只保存文本证据、哈希和可复核来源。


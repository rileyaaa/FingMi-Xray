# TV 5.9.0 依赖与迁移记录

当前状态：BOOTSTRAP_ONLY_UPSTREAM_NOT_IMPORTED。上游源码、独立补件、自有业务分别管理。精确 root/tree 与保留路径身份见 [UPSTREAM.lock.json](../UPSTREAM.lock.json)。

## 上游原件

- FongMi/TV 5.9.0，commit d3a0b84b24cf6628d72a4dbc2be453875b005536，tree 82953e314d3009f039bb220db05ca537e0eadc92；仓库 GPL-3.0。完整产品导入必须保留固定树中除上游 .github 外的全部 1363 个受追踪 blob 路径。各上游二进位仍需单独核对适用许可证与分发义务。
- Gradle 9.7.1、AGP 9.5.1、Java 21、compile/target SDK 37；API36 Robolectric 仅为测试运行时，不能代替 SDK37 编译。Build Tools 与 platform revision 以实际 runner 解析及 package metadata 为准。
- 导入前核查发现现有 fork 两个参考树只包含 654 个对应 blob 路径，709 路径（698 个独有 blob，100658732 bytes）没有可复用的现存对象证据；固定 TV tree 不能直接在目标仓库解析。正常 Git 对象导入及整树读回尚未完成，不用不完整的文字复制冒充完整源码。

## 自有模块

- xray、libxray：与维护锚点及旧开发分支的 subtree 一致，现有直播分组/频道规则、单播放会话、导入/安全边界保留。libxray 仅为依赖容器，不含已验证稳定版 AAR。
- tv-recovery：选择旧开发分支已审阅的独立模块 subtree；相对于维护锚点，仅 Coordinator 与其 JUnit 测试不同。恢复条件、过期回调与重复完成守门必须保留。宿主接线待固定 TV 导入后重新正向适配。
- tests/recovery 下仅保留必要合成回归、旧 JNI 行为 oracle 和对照源，不作为产品 Java/native 输入。旧 dev 中其余源审查与历史测试不迁入；待宿主接线时选取必要回归。历史结果不是本分支新运行结果。

## 独立补件

| 项目 | 当前来源及状态 | 构建/ABI/验收与回退 |
| --- | --- | --- |
| Xray Core 稳定版 | XTLS/libXray v26.11.9 (5a0f7d8d1c28b34afb5727b04b26a10f6dbac7e3, MIT)；XTLS/Xray-core v26.11.9 (676eaf66f8f05d4d558ee7a74b4736623d3feeb9, MPL-2.0)。正式 go.mod 要求 Go 1.27.3。 | 需同次构建匹配 bindings/JNI，arm64-v8a 与 armeabi-v7a，固定实际产物摘要；旧候选 23/26、API2/API3 与 TOFU 未闭合。VMess QR 相容层独立 4/4、37/37，不是本分支已迁移或正式 converter 已通。不预先替换既有 v26.7.28 维护基线。 |
| Media3 / MPV / FFmpeg | 固定 FongMi/media 3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d；旧版本缺真实 setLibraryLoader、MpvDecoderMode、ProgressiveIsoCache 等 5.9.0 消费合同。 | 只允许匹配的合法同源实现或可验证真实源码重建；不得使用未知 AAR、空壳、删能力或无权分发 AV3A。完整 Java/JNI/双 ABI/许可证及实际媒体能力均待闭合，失败停止，不混装旧依赖。 |
| #114 真实 EPG 宿主 | 旧分支保留 fixed replay、历史定向 JVM 与数据层证据。 | 真实 Leanback App/Looper/LiveData、late worker/main queue 与 eager 单变异仍须执行。不能用合成测试替代真实宿主，不重跑明确拒绝的 F3/115/116 动作。 |

新增补件必须记录缺失原因、官方来源/版本/commit、实体 size/SHA-256、许可证、放置与构建方式、ABI、实际测试与回退。当前没有合格的新 APK 或稳定 Core 产品产物；安装/覆盖升级/设备验证均未完成。

## 最小回归入口（迁移后待执行）

- `python3 tests/test-tv-network-recovery-reentry.py`：真 Java Coordinator，受控 Hooks。
- `python3 tests/test-xray-normalizer-parity.py`：旧链接归一化对照。
- `python3 tests/test-xray-error-sanitizer.py`：错误脱敏。
- `python3 tests/test-xray-session-races.py`：真控制器，Android/Binder/config 测试边界为替身。

没有 Android Gradle 根工程或可直接执行的 APK 构建。完整上游源码与必要接线、匹配依赖到位后，才恢复一条普通可复用的 Actions 入口；不带旧诊断、签名或发布工作流。

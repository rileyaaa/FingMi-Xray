# AI 协作开发准则

本文件集中维护 AI 在 FingMi-Xray 仓库中与用户共同开发时必须遵守的执行限制。工程事实以 [DEVELOPMENT.md](DEVELOPMENT.md) 为准，长期架构以 [PROJECT.md](PROJECT.md) 为准，旧发布版证据以 [RECOVERY.md](RECOVERY.md) 为准。

## 1. Actions / AC 默认不跑，且禁止原地轮询

- 用户使用的 Actions / AC 额度有限，应把 CI 计算额度视为稀缺资源。**默认不触发 Actions；能通过静态审计、现有源码 guard / JVM / parity 脚本、已有且仍适用的证据完成判断时，就不要为了“再验证一下”启动 AC。**
- 每次准备触发 run 前必须先综合评估：这次 run 是否会提供能够改变当前开发决策的新增证据；是否存在不消耗 AC 的等价验证；是否可以先把同一轮源码审计和确定修复集中完成，再一次性验证。三项中没有明确必要性时，不运行。
- 适合消耗 AC 的场景主要是：静态审计已经收敛、需要 compiler / Gradle / APK / native / Manifest 级证据确认当前 HEAD；某个已定位问题只有真实构建或运行环境才能判定；或用户明确要求执行。即使需要运行，也只执行与本项目 Android TV / Leanback 目标和当前变更直接相关的最小验证，不顺带编译无关 variant。
- 禁止形成“发现一个小问题 → 改一次 → 跑一次 AC”的循环；普通文档修改、source guard 小改、尚未完成的一轮竞态审计，以及纯粹出于安心的重复构建，都不足以单独触发 run。应优先积累到一个稳定检查点后再集中验证。
- 已有 Actions artifact / log 只有在仍对应当前代码事实时才能复用；不得拿旧 run 冒充最新 HEAD 已验证。是否需要新 run 仍按上述必要性判断，而不是因为旧证据过期就自动触发。
- 同一个 GitHub Actions run 在同一工作阶段最多主动检查一次状态；禁止反复查询 run / jobs / logs 只为了等待 `queued` / `in_progress` 变成完成。
- 如果该次检查仍未完成，立即继续其他有实际产出的审计、测试、代码或文档工作。
- 没有其他可做工作时，结束当前回复并报告状态，不占着会话等待 CI。
- 只有 run 已完成、步骤发生实质变化，或需要定位明确失败时，才读取具体 jobs / logs。

## 2. Actions 当前状态必须从最新 runs 列表重新确认

- 向用户报告 Actions 状态前，先刷新仓库最新 runs 列表，再定位目标 run。
- 之前读取的单个 run、jobs 或日志结果只能代表当时状态，不能直接当成当前状态。
- 最新 runs 列表确认 run 已完成后，才读取该 run 的 jobs / logs 核对实际成功步骤或失败原因。
- 临时 `push` trigger 只允许用于必要验证；完整 run 入队后不得继续向 `main` 提交任何内容，也不得提前恢复 `workflow_dispatch`；必须等该 run 完整结束后再恢复 manual-only。`current-main-build.yml` 与 publish workflow 都使用两阶段 marker：先用只修改 workflow 的 arm commit 增加仅监听对应 marker path 的 `push`，该 arm commit 本身不得触发完整构建；再用只修改 `.github/.trigger-current-main-build` 或 `.github/.trigger-publish-current-main-test` 的 marker commit 作为真正 checkout / build source，并由 workflow source guard 验证 marker-only diff。publish 还必须等 Release 创建、tag / digest 校验与上一测试版替换全部完成后才能撤回 trigger。不得把直接修改 workflow YAML 的 arm commit 当成 current build 或 Release target。验证结束还要确认 current-main 与 publish workflow 都是纯手动且 marker 已删除。
- 如果当前自动化环境既没有 `workflow_dispatch` 调用能力，又明确阻止修改 workflow trigger，则不得通过强制移动 `main`、回退默认分支、复用旧自动 trigger commit 或其他方式绕过平台安全限制。保持仓库 pure manual-only，由用户在 GitHub Actions 页面使用 `Run workflow` 触发；AI 继续完成不依赖该触发动作的审计、文档、存储清理和后续结果核验。
- GitHub Releases 只用于发布产物，不作为长期文件仓库。正常状态只保留 `v5.6.0-xray.5` 黄金参考和一个当前可上真机测试的版本；构建输入、recovery 材料、旧测试版和临时文件应改为项目内源码 / 脚本 / fixture / hash 或短期 Actions artifact。不得为了省事新建 build-input Release。

## 3. 正常开发只保留 `main` 一个分支

- 仓库正常开发状态只保留默认分支 `main`；普通开发、审计、验证、上游同步和文档维护都直接在 `main` 上进行。
- 未经用户明确要求，不得为了普通工作长期创建第二条开发分支，也不得把临时分支留成并行开发线。
- 如果受平台能力限制确实必须临时创建额外分支，只允许作为短期机制使用；相关工作合回 `main` 后必须立即删除。
- 临时 Actions marker / trigger 属于 CI 机制，不等同于开发分支，但仍必须遵守本文的 CI 清理规则。
- 交接、发布和工作阶段收尾前检查仓库 branches；正常状态应只剩 `main`。发现已完全并入 `main` 的遗留分支时应优先清理，不得继续搁置。

## 4. 会话接近平台时限时立即交接

- 如果判断当前会话接近平台时限、上下文容量限制或可能被系统中断，不再开启新的长流程、批量审计、CI 等待或大范围修改。
- 立即返回可继续接手的信息：当前 `main` HEAD、已完成提交、未完成事项、临时 workflow trigger 状态、下一步最具体的文件 / run / commit / 操作入口。
- 不等会话被强制中断后留下半截工作。
- 用户再次发送“继续工作”后，直接从交接状态继续，不重复已经确认的检查。

## 5. 及时维护文档，但不复制 Git / Actions 流水

代码、架构、构建链、验证入口、发布边界或历史证据出现会影响后续开发判断的稳定变化时，应在同一工作阶段更新 canonical 文档；不能依赖聊天上下文代替仓库文档。

长期文档只保存当前事实、约束、复现方式、验证入口和必要的故障结论。Git 历史回答“哪次提交做了什么”，Actions 保存 run / job / log；单次失败尝试、临时 trigger、普通 commit SHA、一次性 run id 和很快被后续结果取代的状态不重复抄进长期说明。

**例外：`DEVELOPMENT.md` 可以维护按日期、版本或里程碑组织的精选维护记录。** 这类记录用于保留长期有价值的根因、迁移决策、兼容约束和验证基线，不等于把每天的操作过程写成开发日志。

文档更新时还必须：

- 准确区分静态证据、JVM/单元测试、native 动态 parity、Gradle 编译、APK assemble、模拟器和真机运行；
- 一个事实尽量只由一个 canonical 文档负责，其他文档通过链接引用；
- 交接前检查代码事实与对应文档是否一致；
- 不重新创建已经被合并掉的目录 README，除非目录出现无法由 canonical 文档合理承载的新职责。

## 6. 六份项目文档的职责

除 `LICENSE.md` 外，项目长期只维护 6 份 Markdown 项目文档。**未经用户明确同意，不得新增第 7 份项目文档，也不得重新创建已经合并删除的目录 README。**

新增文档属于项目结构变化，必须先向用户说明为什么现有 6 份文档无法承载该内容，并取得明确同意后才能创建。不能因为“方便记录”“临时交接”“单独说明某个目录”就自行增加 Markdown 文档。


| 文档 | 职责 |
| --- | --- |
| `README.md` | 仓库入口、项目定位、当前版本概览和文档导航 |
| `docs/PROJECT.md` | 产品边界、模块职责和长期架构约束 |
| `docs/DEVELOPMENT.md` | 当前源码、构建、测试、兼容层、上游同步、验证矩阵和精选维护记录 |
| `docs/AI_COLLABORATION.md` | AI 与用户共同开发时的执行限制 |
| `docs/RECOVERY.md` | v5.6.0-xray.5 faithful 恢复、APK/JADX/DEX/native 证据、provenance 和黄金行为索引 |
| `docs/ORIGINAL_README.md` | 冻结的旧发布说明，不随 current-main 改写 |

`tests/`、`compat/` 的说明属于 DEVELOPMENT；`recovery/`、`docs/apk-reference/` 的说明属于 RECOVERY。

后续维护遵循“**按时更新，只更新对应文档**”：

- 工程结构、构建、测试、compat、验证矩阵和精选维护记录，只更新 `DEVELOPMENT.md`；
- 产品边界和长期架构，只更新 `PROJECT.md`；
- AI 协作限制，只更新 `AI_COLLABORATION.md`；
- 历史恢复、APK/JADX/DEX/native provenance 和黄金行为证据，只更新 `RECOVERY.md`；
- 仓库入口、版本概览和导航，只更新 `README.md`；
- `ORIGINAL_README.md` 保持冻结，不随 current-main 更新。

一个事实如果已经有明确 canonical 文档，不得为了“同步”而在其他文档复制同一段说明；其他文档只有在确实需要导航时保留最短链接。对应事实发生稳定变化时，应在同一工作阶段及时更新它所属的 canonical 文档，避免文档晚于代码事实。

## 7. CI 产物必须区分长期存留与临时使用

- 在创建、上传或保留较大的 APK、AAR、ZIP、构建报告或测试证据前，先判断它是发布产物、可重建输入、不可重建的黄金证据，还是一次性临时产物。
- GitHub Releases 只承载发布版本；正常状态只保留 `v5.6.0-xray.5` 黄金参考和一个当前可上真机测试的版本。不得把 player AAR、recovery ZIP、构建缓存或其他 build input 另建 Release 长期存放。
- 可重建的长期输入应保存固定 source commit、构建脚本、最小 fixture / patch 和校验规则；构建时现场重建并验证。不可重建且确属黄金发布来源的二进制只能从保留的黄金 Release 按固定 digest 取证。
- 适合 Git 长期保存的证据应是最小、可复核的文本、源码、patch、fixture 与 hash；不要把大型 APK / AAR / SO 直接塞入普通 Git 历史。
- Actions artifacts 只用于短期调试、交接、人工复核或失败排查，应采用短 retention、尽量只保留最新必要副本，用完及时删除；不得让重复构建产物随每次 CI 线性累积。
- 临时产物如果仍在当前工作阶段会被继续使用可以暂留；一旦用途结束，应在同一阶段或最近一次收尾中清理。
- 具体 workflow 的 retention、自动 pruning、源码重建输入与发布清理规则统一维护在 `DEVELOPMENT.md`，本文件只约束 AI 的存储决策。

## 8. 上游只以公开源码仓库为准

- 判断 FongMi/TV、FongMi/media 等“上游当前版本”时，只以对应公开源码仓库的实际默认分支、commit、tree 和仓库内版本配置为准；公开仓库 HEAD 是本项目上游同步的唯一源码基线。
- FongMi Release / APK 的版本号即使高于公开源码仓库中的 `versionName`，也不得据此认定公开仓库“落后”，更不得通过反编译较新 APK 将未公开实现反向移植到 `main`，并把这种行为称为“跟随上游”。
- Release / APK 反编译只允许用于以下范围：本项目既有黄金版本的行为恢复与 parity 取证；必要的 ABI、native provenance 或兼容性验证；以及用户明确授权的专项研究。除这些场景外，不得把 APK 反编译结果当作上游源码替代品。
- 当公开源码仓库仍为 5.6.3，而 Release / APK 显示 5.6.8 等更高版本时，本项目仍以公开仓库 HEAD 为上游；未在公开仓库出现的 Dolby、MPV bridge、ISO / UDF、光碟导航或其他 Release-only 功能不得为了“追版本”主动迁入。
- 上游同步时应优先记录并验证目标仓库 commit，而不是只看版本号。版本号用于描述仓库当时声明的版本，不得凌驾于源码 commit/tree 之上。

## 9. 开发与 Bug 修复范围只限 Xray 和 TV 待机网络恢复

- 本 fork 的长期维护范围只有两个：**Xray 功能**与**Android TV 待机 / 息屏后的网络恢复功能**。无论是主动开发、重构、代码审计、Bug 排查、兼容修复还是测试补强，都必须先判断问题是否直接属于这两个范围。
- 除上述两个范围外，其它播放器、UI、业务接口、解析器、媒体能力、设置项、数据库、DLNA、字幕、弹幕等功能均以 FongMi 公开上游源码为准。即使审计过程中确认存在 Bug，只要该 Bug 与 Xray 或 TV 网络恢复无直接因果关系，**本 fork 也不修、不加 workaround、不做“顺手优化”**；等待并跟随上游。
- 可以修改上游文件中的 Xray / TV 网络恢复**必要接线点**，例如播放网络 client 注入、播放身份边界、Home recovery 生命周期、API client / DNS / Spider generation 清理等；但改动必须严格局限于服务这两个模块，不能借接线文件顺带改变其它上游行为。
- 如果一个现象同时涉及上游功能与本 fork 功能，只修本 fork 新增或修改部分造成的问题；若移除本 fork 逻辑后问题仍然存在，应视为上游现状，不继续在本 fork 扩大修复范围。
- 审计时可以为了排除因果关系阅读其它上游代码，但“阅读到问题”不等于取得修改授权。最终提交、测试和文档记录都应只围绕 Xray / TV 网络恢复及其必要集成边界。
- 判断是否允许修改时优先问：**如果没有 Xray 和 TV 网络恢复，这个改动是否仍然值得做？** 如果答案是“是”，通常说明它属于上游通用问题，本 fork 不应修改。

## 10. 黄金版是恢复基线，不是不可修正的绝对正确实现

- `v5.6.0-xray.5` v7 黄金 APK 的定位是：在原始源码丢失、当前模块尚未经过足够多轮真机验证、且没有更强证据时，为 Xray 提供**最可靠的已知行为基线和恢复起点**。它长期实际使用、相对稳定、目前没有已知的明显或致命问题，因此“什么都没有”的情况下应优先按它还原，而不是凭空重新设计。
- “黄金参考 / parity”不等于“黄金版绝对无 Bug”。反编译只能说明已发布程序做了什么，长期使用也不能证明所有边界都正确；隐藏竞态、安全缺口、异常路径和低概率故障仍可能存在。
- 恢复阶段应先把未经验证的漂移收回黄金行为；恢复完成后，如果在 **Xray 或 TV 网络恢复**维护范围内出现可复现故障、明确竞态、安全问题、资源泄漏或有更强源码 / DEX / native / 真机证据证明黄金行为本身有缺陷，可以正常修复，不得仅以“黄金版就是这样”为理由拒绝修 Bug。
- 修正黄金自身问题时必须把两件事分开记录：一是“黄金原始行为/证据是什么”，二是“current 为什么有意不同、修复解决什么问题、用什么证据约束”。parity guard 应允许明确登记的有意修复，而不能为了追求字节或行为一致把已证明的 Bug 重新带回。
- 对尚不能证明是 Bug 的差异，仍以黄金为保守默认；不要把个人偏好、重构便利或理论上的“更合理”当成偏离黄金的理由。证据不足时先还原，证据充分后再修。
- 当前模块化重构已经完成。旧黄金版的一体化实现只作为历史行为证据，不要求 current 回到把 Xray 深度写进 FongMi 业务代码的结构。后续开发目标是维持清晰模块边界、修复 Xray / TV 待机网络恢复中的真实问题，并让普通 FongMi 代码持续容易跟随公开上游更新。

## 执行优先级

用户最新明确指令优先于本文；没有冲突时，后续 AI 必须继续遵守这些协作限制。

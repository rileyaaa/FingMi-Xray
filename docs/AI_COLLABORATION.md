# AI 协作开发准则

本文件集中维护 AI 在 FingMi-Xray 仓库中与用户共同开发时必须遵守的执行限制。工程事实以 [DEVELOPMENT.md](DEVELOPMENT.md) 为准，长期架构以 [PROJECT.md](PROJECT.md) 为准，旧发布版证据以 [RECOVERY.md](RECOVERY.md) 为准。

## 1. 禁止原地轮询 CI / Actions

- 同一个 GitHub Actions run 在同一工作阶段最多主动检查一次状态；禁止反复查询 run / jobs / logs 只为了等待 `queued` / `in_progress` 变成完成。
- 如果该次检查仍未完成，立即继续其他有实际产出的审计、测试、代码或文档工作。
- 没有其他可做工作时，结束当前回复并报告状态，不占着会话等待 CI。
- 只有 run 已完成、步骤发生实质变化，或需要定位明确失败时，才读取具体 jobs / logs。

## 2. Actions 当前状态必须从最新 runs 列表重新确认

- 向用户报告 Actions 状态前，先刷新仓库最新 runs 列表，再定位目标 run。
- 之前读取的单个 run、jobs 或日志结果只能代表当时状态，不能直接当成当前状态。
- 最新 runs 列表确认 run 已完成后，才读取该 run 的 jobs / logs 核对实际成功步骤或失败原因。
- 临时 `push` trigger 只允许用于必要验证；完整 run 入队后不得继续向 `main` 提交任何内容，也不得提前恢复 `workflow_dispatch`；必须等 Release 创建与校验完成后再恢复 manual-only，避免 default branch 与显式 Release target 的 workflow 树在发布前发生差异。对 publish workflow 必须使用两阶段 marker 触发：先用一个只修改 workflow 的 commit 临时增加 `push`，其自身触发的 run 必须被 marker source guard 立即拒绝；再用第二个只修改 `.github/.trigger-publish-current-main-test` 的 commit 真正触发完整构建。只有第二个 marker commit 可以作为 checkout / build / Release target。不得把直接修改 workflow YAML 的临时 arm commit 作为显式 Release target。验证结束还要确认 current-main 与 publish workflow 都是纯手动。

## 3. 会话接近平台时限时立即交接

- 如果判断当前会话接近平台时限、上下文容量限制或可能被系统中断，不再开启新的长流程、批量审计、CI 等待或大范围修改。
- 立即返回可继续接手的信息：当前 `main` HEAD、已完成提交、未完成事项、临时 workflow trigger 状态、下一步最具体的文件 / run / commit / 操作入口。
- 不等会话被强制中断后留下半截工作。
- 用户再次发送“继续工作”后，直接从交接状态继续，不重复已经确认的检查。

## 4. 及时维护文档，但不复制 Git / Actions 流水

代码、架构、构建链、验证入口、发布边界或历史证据出现会影响后续开发判断的稳定变化时，应在同一工作阶段更新 canonical 文档；不能依赖聊天上下文代替仓库文档。

长期文档只保存当前事实、约束、复现方式、验证入口和必要的故障结论。Git 历史回答“哪次提交做了什么”，Actions 保存 run / job / log；单次失败尝试、临时 trigger、普通 commit SHA、一次性 run id 和很快被后续结果取代的状态不重复抄进长期说明。

**例外：`DEVELOPMENT.md` 可以维护按日期、版本或里程碑组织的精选维护记录。** 这类记录用于保留长期有价值的根因、迁移决策、兼容约束和验证基线，不等于把每天的操作过程写成开发日志。

文档更新时还必须：

- 准确区分静态证据、JVM/单元测试、native 动态 parity、Gradle 编译、APK assemble、模拟器和真机运行；
- 一个事实尽量只由一个 canonical 文档负责，其他文档通过链接引用；
- 交接前检查代码事实与对应文档是否一致；
- 不重新创建已经被合并掉的目录 README，除非目录出现无法由 canonical 文档合理承载的新职责。

## 5. 六份项目文档的职责

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

## 6. CI 产物必须区分长期存留与临时使用

- 在创建、上传或保留较大的 APK、AAR、ZIP、构建报告或测试证据前，先判断它是长期资产还是可重建的临时产物。
- 长期需要复用的二进制构建输入、正式/测试发布 APK 应进入项目 Release，并保留固定 digest / provenance；不要依赖会自动过期的 Actions artifact 作为长期来源。
- 适合 Git 长期保存的证据应是最小、可复核的文本材料；不要把大型 APK / AAR / SO 直接塞入普通 Git 历史。
- Actions artifacts 只用于短期调试、交接或失败排查，应采用短 retention、尽量只保留最新必要副本，用完及时删除；不得让重复构建产物随每次 CI 线性累积。
- 临时产物如果仍在当前工作阶段会被继续使用可以暂留；一旦用途结束，应在同一阶段或最近一次收尾中清理。
- 具体 workflow 的 retention、自动 pruning 与当前长期 build-input Release 位置属于工程实现，统一维护在 `DEVELOPMENT.md`，本文件只约束 AI 的存储决策。

## 执行优先级

用户最新明确指令优先于本文；没有冲突时，后续 AI 必须继续遵守这些协作限制。

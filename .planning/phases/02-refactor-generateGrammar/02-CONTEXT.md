# Phase 2: 重构 generateGrammar 模块 - Context

**Gathered:** 2026-05-04T10:54:55.000Z
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段完成第一项完整脚本重构：围绕 `/home/zzh/project/Pacman/2.Pac-man/structre-learning/scripts/fmriDataProcess/generateGrammar.py` 的默认入口 `main("ghost2", 0.5, False)`，在 LoPS 中重新设计并实现高内聚低耦合的新模块、运行入口和验证流程。

本阶段包括：默认路径深度分析、调用模块同轮重构、模块级行为测试、脚本级一致性验证、输出兼容层和完成记录。

本阶段不包括：`ghost4` 分支、`needShuffle=True` 分支、默认入口未调用函数、默认入口未使用数据和其它未来功能。

</domain>

<decisions>
## Implementation Decisions

### 重构范围边界
- **D-01:** 本轮只保留并重构默认有效路径：`main("ghost2", 0.5, False)` 实际走到的逻辑。
- **D-02:** `ghost4`、`needShuffle=True`、未调用函数、未走到分支全部不迁移。
- **D-03:** 若 plan 或 execute 期间发现新的实际调用路径，必须先回到 discuss 确认，不能自动扩大范围。

### 依赖模块迁移边界
- **D-04:** 本轮只迁移默认运行实际调用闭包。
- **D-05:** 必须迁移并测试：`generateGrammar.py` 默认路径实际调用的函数、`src.bayesianScore.BDscore`、`src.bayesianScore.learnBayesNetBlock`、`src.Utils.count`。
- **D-06:** `src.condindepEmp` 以及 `bayesianScore.py` 中默认运行未调用函数不迁移。
- **D-07:** 实现风格必须是 LoPS 新模块结构下的重设计和重实现，不按旧文件边界机械搬运。

### 输出兼容性
- **D-08:** 新实现内部可以使用更清晰的数据结构，但对外必须导出旧 pickle 兼容结构。
- **D-09:** 旧输出中存在的键，新实现输出必须保留同名键，且键值必须一致。
- **D-10:** 兼容输出至少包含旧结构字段：`sets`、`pro`、`gram`、`sequence`、`time_pro`、`frequency`、`seq`、`state`、`S`、`fileNames`、`components`、`skipGram`、`skipGramNum`。
- **D-11:** 若内部新结构与旧结构表达方式不同，必须提供明确转换层，并以旧结构作为验证输出。

### 验证基准与一致性粒度
- **D-12:** 使用原项目既有 `grammar2/` 34 个 pickle 作为固定验证基准。
- **D-13:** 已验证原实现在 LoPS sandbox 中全量重跑后，34/34 输出与原项目既有 `grammar2/` 文件 MD5 完全一致；因此固定基准可信。
- **D-14:** 新实现优先对比固定 `grammar2/` 基准；若验证失败，再 sandbox 重跑原实现作为诊断手段。
- **D-15:** 脚本级验证目标是旧输出存在的键和值一致。若可以做到 pickle 文件 MD5 一致，应作为强验收；若因 pickle 序列化细节无法 MD5 一致，必须证明每个旧键对应值语义一致，并记录原因。
- **D-16:** 参与重构的调用模块必须做模块级行为测试，在相同数据和相同随机参数下与原始模块结果一致。
- **D-17:** 默认路径无随机过程，不需要人为设置随机种子；若未来支持 `needShuffle=True`，必须另行讨论 seed 接口。

### 架构与实现原则
- **D-18:** 重构不是代码搬运，而是基于原始行为进行架构模块重设计、接口重设计和代码重实现。
- **D-19:** 新模块必须高内聚低耦合，清晰区分数据读取、状态条件解析、离散数据组织、Bayesian scoring、grammar chunk 学习、skip-gram 检测、输出兼容和运行入口。
- **D-20:** 恪守 KISS 原则，优先直接、清晰、易维护，避免过度工程化、过早抽象和不必要的防御性设计。
- **D-21:** 所有输入目录、状态图目录、输出目录、`alpha` 等必须显式参数化，不能依赖当前工作目录或 `sys.path` 修改。
- **D-22:** 原项目目录只读；所有新增实现、测试、脚本、验证输出和记录都必须写在当前 LoPS 仓库内。

### the agent's Discretion
- plan 可以决定具体模块文件命名和函数命名，但必须遵守高内聚低耦合、KISS、输出兼容和验证约束。
- plan 可以决定模块级测试的拆分粒度，但必须至少覆盖 `count`、`BDscore`、`learnBayesNetBlock` 和主流程输出兼容。
- plan 可以决定是否让新运行入口默认排序 cluster 文件；如果排序改变控制台日志顺序，必须说明不影响逐文件输出内容。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目与阶段约束
- `.planning/PROJECT.md` - 项目核心价值、确认门、调用模块同轮重构、KISS 和目录边界。
- `.planning/REQUIREMENTS.md` - Phase 2 的 ANLY、DSGN、MOD、ARCH、DATA、VERF 需求追踪。
- `.planning/ROADMAP.md` - Phase 2 目标、成功标准、重构 phase 模式和调用模块测试原则。
- `.planning/STATE.md` - 当前状态、已完成分析结论和下一步阻塞点。

### 本轮重构输入与分析
- `.planning/runs/2026-05-04-generateGrammar/intake.md` - 目标脚本、运行环境、默认入口、写入边界和运行记录。
- `.planning/phases/02-refactor-generateGrammar/02-ANALYSIS.md` - 深度分析报告、调用闭包、数据结构、运行验证和 discuss 问题。

### 仓库约定
- `README.md` - LoPS 目录职责和每轮重构入口说明。
- `.planning/runs/README.md` - run 目录约定。
- `.planning/runs/INTAKE-TEMPLATE.md` - intake 模板。
- `docs/prompt.md` - 用户原始科研脚本重构要求。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 当前 `src/LoPS/`、`script/`、`data/` 仍为空目录结构，没有可复用实现。
- `.planning/phases/02-refactor-generateGrammar/02-ANALYSIS.md` 已包含原脚本行为、数据结构、依赖闭包和验证基准，可直接作为 plan 输入。

### Established Patterns
- Markdown 文档使用中文；代码路径、函数名、字段名保留英文。
- 每个重构 phase 在同一阶段内完成分析、讨论、计划、执行和验证。
- 正式模块进入 `src/LoPS/`，运行入口进入 `script/`，需要纳入项目的数据进入 `data/`。
- `src/LoPS/temp/` 只用于验证阶段的临时旧实现副本，验证后必须清理。

### Integration Points
- 新 LoPS 模块应接收显式路径参数，读取原项目 `StrategySequence/` 和 `StateGraph/`，输出到 LoPS 指定目录。
- 新运行脚本应能在 conda `fmri` 环境下运行。
- 验证流程应读取原项目既有 `grammar2/` 作为固定基准，并对 LoPS 输出进行逐文件对比。
- 模块级行为测试应对比原始 `Utils.count`、`BDscore`、`learnBayesNetBlock` 与新实现。

### External Source Files (read-only)
- `/home/zzh/project/Pacman/2.Pac-man/structre-learning/scripts/fmriDataProcess/generateGrammar.py`
- `/home/zzh/project/Pacman/2.Pac-man/structre-learning/src/bayesianScore.py`
- `/home/zzh/project/Pacman/2.Pac-man/structre-learning/src/Utils.py`

### External Data (read-only)
- `/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/StrategySequence/`
- `/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/StateGraph/`
- `/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/grammar2/`

</code_context>

<specifics>
## Specific Ideas

- 用户选择：`A=1 B=1 C=1 D=1`。
- 用户强调：输出除了集合之外还有概率等；如果旧数据中存在某个键，新代码输出必须保留该键且键值一致。
- 用户强调：原脚本和原脚本所在目录不能修改；除当前 LoPS 仓库外不能写其它目录。
- 用户强调：重构要做架构模块重设计、接口重设计和代码重实现，不是搬运代码。
- 用户强调：高内聚低耦合，恪守 KISS，避免过度工程化、过早抽象和不必要防御性设计。

</specifics>

<deferred>
## Deferred Ideas

- 支持 `ghost4` 分支。
- 支持 `needShuffle=True` 及随机种子接口。
- 迁移 `bayesianScore.py` 中默认运行未调用的其它函数。
- 迁移 `src.condindepEmp` 中默认运行未调用的函数。

</deferred>

---

*Phase: 2-重构 generateGrammar 模块*
*Context gathered: 2026-05-04T10:54:55.000Z*

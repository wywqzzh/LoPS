# Phase 2: 重构 generateGrammar 模块 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-04T10:54:55.000Z
**Phase:** 02-refactor-generateGrammar
**Areas discussed:** 重构范围边界, 依赖模块迁移边界, 输出兼容性标准, 验证基准与一致性粒度

---

## 重构范围边界

| Option | Description | Selected |
|--------|-------------|----------|
| 只保留默认有效路径 | 只实现 `main("ghost2", 0.5, False)` 实际走到的逻辑。`ghost4`、`needShuffle=True`、未调用函数、未走到分支全部不迁移。 | ✓ |
| 默认路径为主，保留少量未来参数口 | 实现默认路径，但接口预留 `alpha`、输入目录、输出目录等参数；不实现 `ghost4` 和 shuffle 行为。 | |
| 顺手迁移更多分支 | 同时迁移 `ghost4`、`needShuffle=True` 等路径。范围明显扩大。 | |

**User's choice:** A=1  
**Notes:** 本轮只保留默认有效路径；未使用分支不迁移。

---

## 依赖模块迁移边界

| Option | Description | Selected |
|--------|-------------|----------|
| 只迁移实际调用闭包 | 迁移 `BDscore`、`learnBayesNetBlock`、`Utils.count`，以及 `generateGrammar.py` 默认路径实际调用的函数。不迁移 `condindepEmp` 和 `bayesianScore` 未调用函数。 | ✓ |
| 迁移整个 `bayesianScore.py` 的相关文件 | 包括未调用函数一起迁移。减少遗漏风险，但会引入大量不参与本轮验证的代码。 | |
| 只在新模块中重写需要的算法，不保留旧模块结构 | 不按旧文件边界迁移，而是把 scoring/count/block-learning 重新设计成 LoPS 内的新模块。 | |

**User's choice:** B=1  
**Notes:** 范围选择为实际调用闭包；实现仍应按 LoPS 新模块结构重设计，不机械保留旧文件边界。

---

## 输出兼容性标准

| Option | Description | Selected |
|--------|-------------|----------|
| 内部重设计，外部导出旧 pickle 结构 | 新代码内部使用清晰结构；最终输出仍包含旧字段，方便与旧结果对比。 | ✓ |
| 完全沿用旧结构 | 内部和外部都尽量贴近旧 dict。最容易字节级一致，但不利于架构重设计。 | |
| 只输出新结构 | 最干净，但会破坏旧下游和当前 `grammar2` 验证基准。 | |

**User's choice:** C=1  
**Notes:** 用户补充：旧输出除了集合之外还有概率等；如果旧数据中存在某个键，新代码输出必须保留该键且键值一致。

---

## 验证基准与一致性粒度

| Option | Description | Selected |
|--------|-------------|----------|
| 固定 `grammar2/` 基准 + 必要时 sandbox 重跑原实现 | 以原项目现有 34 个 `grammar2` pickle 为固定基准；已验证 sandbox 原实现输出与其 34/34 MD5 一致。新实现优先对比固定基准，若失败再重跑原实现诊断。 | ✓ |
| 每次都 sandbox 重跑原实现作为基准 | 最严格，但耗时更长，也让验证依赖原代码可运行状态。 | |
| 只做语义一致，不要求 pickle 字节级一致 | 比较关键字段值、数组、DataFrame、列表等内容一致；不要求 pickle 文件 MD5 一致。 | |

**User's choice:** D=1  
**Notes:** 验证以固定 `grammar2/` 为基准；旧键必须保留且键值一致。若可达到 pickle MD5 一致，应作为强验收；若不能，必须证明旧键对应值一致并记录原因。

---

## the agent's Discretion

- 规划阶段可以决定 LoPS 新模块文件名和函数名。
- 规划阶段可以决定模块级行为测试的具体拆分方式。
- 规划阶段可以决定是否排序 cluster 文件，但必须说明对输出内容的影响。

## Deferred Ideas

- 支持 `ghost4`。
- 支持 `needShuffle=True` 和随机种子接口。
- 迁移默认路径未调用的 `bayesianScore.py` 函数。
- 迁移默认路径未调用的 `condindepEmp` 函数。

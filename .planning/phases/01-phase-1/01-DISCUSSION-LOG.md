# Phase 1: 项目骨架与任务接收契约 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-03
**Phase:** 1-项目骨架与任务接收契约
**Areas discussed:** 任务记录形式, 必填信息严格度, 目录职责说明粒度, 每轮状态记录位置, 轮次命名方式

---

## 任务记录形式

| Option | Description | Selected |
|--------|-------------|----------|
| Markdown 模板为主 | 每轮一个中文 `.md`，方便读写和补充背景。 | ✓ |
| 机器可读 manifest 为主 | 每轮一个 `.json`/`.yaml`，便于自动化，但早期较僵硬。 | |
| 两者结合 | Markdown 给人读，manifest 放关键字段；更完整但维护成本更高。 | |

**User's choice:** A=1  
**Notes:** 入口记录以人工可读和可补充为优先。

---

## 必填信息严格度

| Option | Description | Selected |
|--------|-------------|----------|
| 最小阻塞 | 目标脚本路径、运行环境、数据来源三项必填；运行命令、权限、预期输出可先占位。 | ✓ |
| 严格阻塞 | 目标脚本、环境、数据、运行命令、权限、预期输出都必须齐全才能进入 Phase 2。 | |
| 宽松开始 | 只要有目标脚本路径即可开始，缺失信息在分析中逐步补。 | |

**User's choice:** B=1  
**Notes:** Phase 1 模板要区分必填字段和可占位字段。

---

## 目录职责说明粒度

| Option | Description | Selected |
|--------|-------------|----------|
| 简洁 README | 写一个项目级说明，明确 `src/LoPS`、`script`、`data`、`docs`、`.planning` 的职责。 | ✓ |
| 目录内 README | 每个关键目录都放 README，职责最清楚，但文件更多。 | |
| 只写在 `.planning` | 不新增面向仓库读者的说明文件，保持根目录更少。 | |

**User's choice:** C=1  
**Notes:** 下游计划应优先创建或更新项目级 README，而不是分散多个目录说明。

---

## 每轮状态记录位置

| Option | Description | Selected |
|--------|-------------|----------|
| 每轮独立目录 | 例如 `.planning/runs/<run-id>/`，里面放 intake、analysis、proposal、verification。 | ✓ |
| 集中记录 | 所有轮次都写进一个总表或总文档，简单但后期容易变长。 | |
| 跟随 GSD phase 目录 | 把每轮记录放在 `.planning/phases/...` 下，贴近 GSD，但科研轮次和 GSD 阶段可能混在一起。 | |

**User's choice:** D=1  
**Notes:** 科研重构轮次和 GSD 阶段要分开。

---

## 轮次命名方式

| Option | Description | Selected |
|--------|-------------|----------|
| 日期加短名 | 例如 `2026-05-03-kalman-filter`，可读且天然排序。 | ✓ |
| 递增编号 | 例如 `run-001`，稳定但不直观。 | |
| 目标脚本名派生 | 例如 `fit-models`，直观但可能重名。 | |

**User's choice:** E=1  
**Notes:** 建议格式为 `YYYY-MM-DD-short-name`，短名使用小写 ASCII、数字和连字符。

## the agent's Discretion

- Markdown 模板具体章节标题和字段顺序交由计划阶段决定。
- 项目级 README 的具体修复方式交由计划阶段根据当前 `README.md/` 目录状态决定。
- 用户随后补充 Phase 1 可以简单些；计划阶段应把 Phase 1 控制为最小可用骨架，不提前设计完整状态系统或多套模板。

## Deferred Ideas

None.

# LoPS

## 这是什么

LoPS 是一个用于系统性重构既有科研脚本的 Python 项目。每一轮工作都由用户提供目标脚本、运行环境和数据来源，项目需要先理解原始功能，再提出可确认的重构方案，最后在 `src/LoPS`、`script` 和 `data` 中落地模块、运行脚本和数据组织。

它不是一次性清理某个脚本，而是一套可重复执行的科研代码迁移流程：先保护原始行为，再重构结构，最后用相同输入和随机种子证明新旧输出一致。

## 核心价值

每次重构都必须在不改变科研计算结果的前提下，把外部脚本迁移成边界清晰、可运行、可验证的 LoPS 模块。

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] 用户可以为每一轮重构提供目标脚本、运行环境和数据来源。
- [ ] LoPS 可以记录原始脚本的输入、输出、执行流程、依赖文件和数据关系。
- [ ] LoPS 可以判断某段功能是否值得在 `src/LoPS` 下抽成独立模块。
- [ ] LoPS 可以在修改代码前产出重构方案，并等待用户确认。
- [ ] LoPS 可以把确认后的功能拆分到清晰的模块、脚本和数据目录中。
- [ ] LoPS 可以在相同输入和随机种子下对比旧实现与新实现的输出。
- [ ] 如果原始代码存在未固定的随机过程，LoPS 可以临时复制旧代码到 `src/LoPS/temp` 并加入统一随机种子进行验证，验证后清理临时代码。
- [ ] 每轮重构完成后都有可复现的运行入口和验证记录。

### Out of Scope

- 自动扫描并决定全部待重构科研项目：当前流程由用户逐轮指定目标脚本，避免错误选择范围。
- 在未获确认前直接修改业务代码：这会破坏用户要求的方案确认门。
- 追求完整通用工作流平台或 GUI：当前重点是可靠的代码重构、运行和验证。
- 在没有原始输出证据时声称完全等价：无法证明一致性时必须记录限制和替代验证方式。

## Context

- 初始上下文来自 [docs/prompt.md](../docs/prompt.md)，该文档明确要求先理解原始科研脚本，再评估模块化必要性、制定方案、等待确认、执行重构、整理数据和运行脚本，并最终做一致性验证。
- 当前仓库已有目录：`src/LoPS/`、`src/LoPS/temp/`、`script/`、`data/`、`docs/`。这些目录应分别承载可复用模块、临时旧代码、运行入口、项目数据和说明材料。
- 目标脚本来自本项目外部，后续执行时可能需要用户授予读取和执行其他目录的权限。
- 项目优先服务科研代码，因此“结果一致”比“代码看起来更整洁”优先级更高。
- 若原始代码没有随机过程，不应人为加入随机种子；若存在随机过程但原始代码没有固定种子，应只在临时旧版本中加入统一种子来构造公平对照。

## Constraints

- **确认门**：重构方案经用户同意前不得修改目标实现代码，原因是用户明确要求先确认方案。
- **目录边界**：可复用逻辑进入 `src/LoPS`，运行入口进入 `script`，输入数据进入 `data`，临时旧实现只允许放入 `src/LoPS/temp`。
- **验证标准**：默认要求完全一致；若浮点或外部库行为导致完全一致不现实，必须明确记录容差、原因和对比对象。
- **外部依赖**：目标脚本、运行环境和数据源每轮可能不同，代码不能假设所有资源都已经在本仓库内。
- **科研可追溯性**：重构不能抹掉原始输入、输出和参数含义，验证脚本必须能说明对比了什么。

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 每轮由用户指定目标脚本、环境和数据 | 初始提示明确把这些信息作为每轮输入，自动扫描容易误判范围 | - Pending |
| 方案确认前不改实现代码 | 用户明确要求等待确认后再执行重构 | - Pending |
| 默认以相同输入和随机种子的输出一致性作为验收标准 | 科研代码重构最重要的是保护计算结果 | - Pending |
| `src/LoPS/temp` 只用于验证随机旧实现，验证后清理 | 保留公平对照，同时避免临时代码污染正式模块 | - Pending |
| 规划文档使用中文 | 用户要求后续交流和 Markdown 文档使用中文 | - Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-03 after initialization*

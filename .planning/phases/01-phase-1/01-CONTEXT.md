# Phase 1: 项目骨架与任务接收契约 - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段只交付“每轮重构如何开始”的输入契约和目录说明。范围包括：任务接收记录格式、最小必填信息、项目目录职责说明、每轮状态记录位置、轮次命名规则。

本阶段不分析具体外部脚本、不执行重构、不移动数据、不设计一致性验证实现；这些分别属于后续 Phase 2-5。

</domain>

<decisions>
## Implementation Decisions

### 任务记录形式
- **D-01:** 每轮重构的入口信息以中文 Markdown 模板为主，不在 Phase 1 强制引入 JSON/YAML manifest。
- **D-02:** Markdown 模板需要适合人工补充背景，字段固定但允许占位和说明性文字。

### 必填信息严格度
- **D-03:** 采用“最小阻塞”策略：目标脚本路径、运行环境、数据来源三项是进入后续分析的最低必填信息。
- **D-04:** 运行命令、必要权限、预期输出可以先占位，但模板必须显式标记为“待补充”，以免下游误以为已经确认。

### 目录职责说明粒度
- **D-05:** Phase 1 应创建或更新一个简洁的项目级 README，说明 `src/LoPS`、`script`、`data`、`docs`、`.planning` 的职责。
- **D-06:** 不在 Phase 1 为每个目录都创建目录内 README，避免早期文档过散。

### 每轮状态记录位置
- **D-07:** 每轮重构使用独立目录记录状态和材料，推荐根路径为 `.planning/runs/<run-id>/`。
- **D-08:** 每轮目录应能容纳 intake、analysis、proposal、verification 等材料，但 Phase 1 只需要定义契约和初始模板，不需要实现后续阶段的完整内容。
- **D-09:** 不把科研重构轮次直接塞进 `.planning/phases/...`，避免 GSD 阶段目录和科研脚本轮次混淆。

### 轮次命名方式
- **D-10:** 每轮目录名采用“日期加短名”，格式建议为 `YYYY-MM-DD-short-name`，例如 `2026-05-03-kalman-filter`。
- **D-11:** 短名应从目标脚本或科研功能派生，使用小写 ASCII、数字和连字符，便于排序、引用和命令行使用。

### the agent's Discretion
- Phase 1 计划可以决定 Markdown 模板的具体章节标题和字段顺序，只要遵守 D-01 到 D-11。
- Phase 1 计划可以决定项目级 README 是新建根目录 `README.md` 还是修正当前异常的 `README.md/` 目录结构，但不得破坏用户已有内容。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目约束
- `.planning/PROJECT.md` - 项目目标、核心价值、目录边界、确认门和中文文档要求。
- `.planning/REQUIREMENTS.md` - Phase 1 对应的 INTK-01 到 INTK-04 需求和后续阶段边界。
- `.planning/ROADMAP.md` - Phase 1 目标、成功标准和计划拆分。
- `.planning/STATE.md` - 当前项目状态和阻塞项。

### 原始用户意图
- `docs/prompt.md` - 用户最初描述的科研脚本重构流程、确认门、数据整理和一致性验证要求。

### 协作规则
- `AGENTS.md` - 中文交流、目录职责、强制流程和质量要求。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 当前没有可复用代码资产；`src/LoPS/` 和 `src/LoPS/temp/` 为空目录结构。
- `docs/prompt.md` 是唯一已有项目文档，应该作为任务接收模板设计的主要语义来源。

### Established Patterns
- 仓库当前是早期骨架：`src/LoPS/`、`script/`、`data/`、`docs/` 已存在，但没有正式 Python 包配置或测试结构。
- 规划文档和对用户说明应使用中文；配置键名和代码路径可以保留英文。

### Integration Points
- Phase 1 的主要落点应是项目级 README 和 `.planning/runs/` 下的模板/说明。
- 后续 Phase 2 应读取每轮独立目录中的 intake 信息，而不是重新向用户索要已经记录的目标脚本、环境和数据来源。

</code_context>

<specifics>
## Specific Ideas

- 用户明确选择：A=1、B=1、C=1、D=1、E=1。
- 这代表：Markdown 模板为主、最小阻塞、简洁 README、每轮独立目录、日期加短名。

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 1-项目骨架与任务接收契约*
*Context gathered: 2026-05-03*

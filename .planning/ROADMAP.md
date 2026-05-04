# 路线图：LoPS

## 概览

v1 的目标是把 LoPS 建成一套可重复的科研脚本重构流程：Phase 1 建立任务接收和目录契约；从 Phase 2 开始，每个 phase 都对应一项具体脚本重构，并在同一个 phase 内完成深度分析、疑点讨论、方案设计、用户确认、实现和一致性验证。

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions marked with INSERTED

- [x] **Phase 1: 项目骨架与任务接收契约** - 定义每轮重构如何接收目标脚本、环境、数据和状态记录。 (completed 2026-05-03)
- [ ] **Phase 2: 重构 generateGrammar 模块** - 作为第一项完整脚本重构，在一个 phase 内完成 generateGrammar.py 的深度分析、多轮讨论、方案确认、实现和一致性验证。

## Phase Details

### Phase 1: 项目骨架与任务接收契约
**Goal**: 明确一轮重构开始时必须收集的信息，并让仓库目录和记录方式支持后续执行。
**Depends on**: Nothing (first phase)
**Requirements**: [INTK-01, INTK-02, INTK-03, INTK-04]
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. 用户可以提供目标脚本路径、环境、运行命令和数据来源。
  2. 每轮重构都有统一记录位置保存输入信息和当前状态。
  3. `src/LoPS`、`script`、`data`、`docs`、`.planning` 的职责被明确记录。
  4. 后续阶段可以直接读取任务记录，不需要重新询问基础上下文。
**Plans**: 2 plans

Plans:
**Wave 1**
- [x] 01-01: 定义每轮重构的任务接收记录格式。

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02: 补齐项目目录职责和初始化说明。

### Phase 2: 重构 generateGrammar 模块
**Goal**: 完整重构 generateGrammar.py 脚本：先深度分析原始行为（包括依赖模块、随机过程和数据使用），再围绕不清楚的功能和可舍弃范围与用户讨论，随后制定并确认重构方案，最后在 LoPS 中实现新模块并验证新旧输出完全一致。
**Depends on**: Phase 1
**Requirements**: [ANLY-01, ANLY-02, ANLY-03, ANLY-04, DSGN-01, DSGN-02, DSGN-03, DSGN-04, MOD-01, MOD-02, MOD-03, MOD-04, DATA-01, DATA-02, DATA-03, DATA-04, VERF-01, VERF-02, VERF-03, VERF-04, VERF-05, VERF-06, VERF-07, VERF-08]
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. 已产出脚本深度分析报告，覆盖当前功能、执行流程、调用模块、输入输出、数据来源、随机过程、副作用和工作目录假设。
  2. discuss 阶段已基于分析报告向用户追问不清楚的功能、边界、保留范围、舍弃范围和验证期望；如问题未收敛，允许多轮 discuss 后再进入 plan。
  3. plan 阶段已制定详细重构计划和实施计划，覆盖模块边界、接口设计、数据路径、运行入口、迁移步骤和验证方式。
  4. 重构方案经用户确认后，才修改正式实现代码。
  5. `src/LoPS` 中实现了边界清晰的新模块，通过显式参数接收路径、配置和必要随机种子。
  6. `script` 中存在可运行新模块的入口脚本。
  7. 必要数据被整理到 `data` 并记录来源。
  8. 使用相同输入和随机种子，新旧实现输出完全一致；若完全一致不现实，必须记录原因、容差和差异结论。
  9. `src/LoPS/temp` 中的临时验证代码已清理。
  10. 完成记录说明运行方式、验证方式和一致性结论。
**Plans**: TBD（分析报告 → 多轮讨论 → 重构计划审核 → 执行实现 → 一致性验证）

## 重构 Phase 模式

从 Phase 2 开始，每个新增 phase 都代表一项完整脚本重构，而不是把一次重构拆成多个 phase。每个重构 phase 应按以下顺序推进：

1. 用户提供目标脚本、运行环境、运行命令、数据来源和预期输出。
2. 先对目标脚本做深度分析，并把分析报告写入该 phase 文档。
3. 基于分析报告进入 discuss，向用户追问不清楚的功能、边界、弃用逻辑、数据语义和验证要求。
4. 如果讨论后仍不清楚，继续 discuss；不强行进入 plan。
5. plan 阶段制定详细重构计划和实施计划，并在用户审核通过后进入 execute。
6. execute 阶段按确认计划实现重构、整理数据和运行入口。
7. 最后验证新旧实现一致性，并留下验证记录。

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> ...

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 项目骨架与任务接收契约 | 2/2 | Complete    | 2026-05-03 |
| 2. 重构 generateGrammar 模块 | 0/TBD | Not started | - |

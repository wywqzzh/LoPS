# 路线图：LoPS

## 概览

v1 的目标是把 LoPS 建成一套可重复的科研脚本重构流程：先建立任务接收和目录契约，再分析原始行为，随后形成需要用户确认的重构方案，确认后实施模块化和数据脚本整理，最后用一致性验证证明结果未变。

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions marked with INSERTED

- [x] **Phase 1: 项目骨架与任务接收契约** - 定义每轮重构如何接收目标脚本、环境、数据和状态记录。 (completed 2026-05-03)
- [ ] **Phase 2: 重构 generateGrammar 模块** - 完整重构 generateGrammar.py：深度分析原始行为、制定重构方案、实现新模块、验证一致性。

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
**Goal**: 完整重构 generateGrammar.py 脚本：深度分析原始行为（包括依赖模块）、制定重构方案、在 LoPS 中实现新模块、验证新旧输出完全一致。
**Depends on**: Phase 1
**Requirements**: [ANLY-01, ANLY-02, ANLY-03, ANLY-04, DSGN-01, DSGN-02, DSGN-03, DSGN-04, MOD-01, MOD-02, MOD-03, MOD-04, DATA-01, DATA-02, DATA-03, DATA-04, VERF-01, VERF-02, VERF-03, VERF-04, VERF-05, VERF-06, VERF-07, VERF-08]
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. 原始脚本的功能、执行流程、依赖（包括 src.bayesianScore）、输入输出、随机过程被完整分析并记录。
  2. 重构方案经用户确认，覆盖模块边界、接口设计、数据路径和验证方式。
  3. `src/LoPS` 中实现了边界清晰的新模块，通过显式参数接收路径、配置和随机种子。
  4. `script` 中存在可运行新模块的入口脚本。
  5. 必要数据被整理到 `data` 并记录来源。
  6. 使用相同输入和随机种子，新旧实现输出完全一致。
  7. `src/LoPS/temp` 中的临时验证代码已清理。
  8. 完成记录说明运行方式、验证方式和一致性结论。
**Plans**: TBD (discuss → plan → execute → verify)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> ...

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 项目骨架与任务接收契约 | 2/2 | Complete    | 2026-05-03 |
| 2. 重构 generateGrammar 模块 | 0/TBD | Not started | - |

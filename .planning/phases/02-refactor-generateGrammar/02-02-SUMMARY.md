---
phase: 02-refactor-generateGrammar
plan: 02-02
subsystem: scoring
tags: [python, numpy, scipy, unittest, legacy-comparison]
requires:
  - phase: 02-refactor-generateGrammar
    provides: "02-01 基础模块、数据入口和 StateGraph 读取器"
provides:
  - "默认路径使用到的 Utils.count 重实现"
  - "默认路径使用到的 BDscore 重实现"
  - "默认路径使用到的 learnBayesNetBlock 重实现"
  - "scoring 模块级旧新行为对照测试"
affects: [generate_grammar, scoring, phase-2]
tech-stack:
  added: ["scipy.special.gammaln"]
  patterns: ["生产代码不导入原项目", "测试代码临时导入旧实现做行为对照"]
key-files:
  created:
    - src/LoPS/generate_grammar/scoring.py
    - tests/test_generate_grammar_scoring.py
  modified: []
key-decisions:
  - "只迁移默认运行实际调用的 scoring 闭包，不迁移 condindepEmp 和其它未调用 Bayesian 网络学习函数。"
  - "保留旧版 1-based 状态编码、Fortran order reshape 和 bd1 / bd2 > 1 判定，确保科研行为一致。"
patterns-established:
  - "参与重构的旧调用模块使用同数据行为测试锁定。"
  - "真实数据测试复刻旧 organize_data 中传给 learnBayesNetBlock 的矩阵构造方式。"
requirements-completed: [MOD-04, MOD-05, VERF-09, VERF-10]
duration: 9 min
completed: 2026-05-04
---

# Phase 2 Plan 02-02: 重实现 scoring 模块并对比原始模块行为 Summary

**完成默认分支 scoring 闭包重实现，并用旧模块对照验证行为一致。**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-04T12:20:30Z
- **Completed:** 2026-05-04T12:29:37Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 创建 `src/LoPS/generate_grammar/scoring.py`，重实现 `count_state_combinations()`、`bd_score()` 和 `learn_state_condition_links()`。
- 新 scoring 生产模块只依赖 `numpy` 和 `scipy.special.gammaln`，不导入原项目代码。
- 创建 `tests/test_generate_grammar_scoring.py`，在测试中临时导入旧 `src.Utils.count`、`src.bayesianScore.BDscore` 和 `learnBayesNetBlock`。
- 使用固定小数组验证 count 和 BD score 完全一致。
- 使用真实 `031222-401.pkl` 数据构造旧 `organize_data` 的输入矩阵，验证 `Alearn` 与旧实现完全一致。

## Task Commits

Each task was committed atomically:

1. **Task 1: 实现 count_state_combinations 和 bd_score** - `23fa30b` (feat)
2. **Task 2: 实现 learn_state_condition_links** - `f3b4335` (feat)
3. **Task 3: 添加 scoring 行为对照测试** - `72bb485` (test)

## Files Created/Modified

- `src/LoPS/generate_grammar/scoring.py` - 新 scoring 模块，覆盖旧默认路径实际调用的三个函数。
- `tests/test_generate_grammar_scoring.py` - 旧新模块级行为对照测试。

## Verification

已通过：

```bash
PYTHONPATH=src conda run -n fmri python -m unittest tests.test_generate_grammar_scoring
```

结果：

```text
Ran 3 tests in 0.087s
OK
```

## Decisions Made

- `count_state_combinations()` 保留旧 `Utils.count` 的空输入返回 `[]`、1-based 到 0-based 编码和组合索引方式。
- `bd_score()` 保留旧 `BDscore` 的 parent/无 parent 分支、`order="F"` reshape 和 `gammaln` 公式。
- `learn_state_condition_links()` 保留旧 `learnBayesNetBlock` 的 `conditions -> block_message` 展开方式和 `v - (casual_num - block_num)` 输出下标。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

`02-03` 可以基于 foundation 和 scoring 模块实现 token 化 grammar 学习核心。

---
*Phase: 02-refactor-generateGrammar*
*Completed: 2026-05-04*

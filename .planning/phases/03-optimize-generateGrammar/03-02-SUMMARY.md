---
phase: 03-optimize-generateGrammar
plan: 03-02
subsystem: algorithm
tags: [generate_grammar, parsed-sequence, longest-parse]
requires:
  - phase: 03-01
    provides: tuple token 接口和过程一致性基线
provides:
  - _build_parsed_sequence 共享解析构建流程
  - _parse_longest 和 _parse_probabilities 的兼容委托实现
  - learn 主循环中的 ParsedSequence 解析读取点
affects: [generate_grammar, parser, learner]
tech-stack:
  added: []
  patterns: [single parse source, compatibility wrapper]
key-files:
  created: []
  modified:
    - src/LoPS/generate_grammar/grammar.py
    - tests/test_generate_grammar_process.py
key-decisions:
  - "解析、频次、概率、时间占比和 position_grammar 由一次 ParsedSequence 构建产生。"
  - "旧解析入口保留原返回类型，由 ParsedSequence 委托实现。"
  - "learn 主循环使用 ParsedSequence，但候选评分和 pair_posterior 顺序不变。"
patterns-established:
  - "旧公开/测试入口可作为兼容包装，核心解析逻辑只保留一份。"
  - "ParsedSequence 额外记录 span_starts/span_lengths，用于无重复解析地保持状态行对齐。"
requirements-completed: [OPT-02, OPT-04, OPT-05, OPT-06, OPT-07]
duration: 5 min
completed: 2026-05-05
---

# Phase 03 Plan 03-02: 合并解析与概率统计 Summary

**单一 ParsedSequence 构建流程驱动最长匹配解析、概率统计和 learn 解析读取点**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-05T04:25:00Z
- **Completed:** 2026-05-05T04:29:40Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 新增 `_build_parsed_sequence()`，一次性生成 tuple token、字符串 token、span、频次、概率、时间占比和 `position_grammar`。
- `_parse_longest()` 与 `_parse_probabilities()` 改为兼容包装，返回值保持不变。
- `GrammarLearner.learn()` 的解析读取点改为直接使用 `ParsedSequence`，没有引入 `TransitionStats`，也没有改变 `pair_posterior` 计算位置。
- 扩展过程测试，明确证明 `ParsedSequence` 能还原旧解析入口的 token、概率、频次和位置级 grammar。

## Task Commits

1. **Task 1-3: 实现共享解析构建并接入 learn** - `796c908`
2. **Task 2: 增加 ParsedSequence 等价性测试** - `6073d89`

## Files Created/Modified

- `src/LoPS/generate_grammar/grammar.py` - 新增 `_build_parsed_sequence()` 和状态对齐辅助函数，旧解析入口委托共享结果。
- `tests/test_generate_grammar_process.py` - 新增 `ParsedSequence` 与旧解析入口一致性测试。

## Decisions Made

- `ParsedSequence` 记录 `span_starts` 和 `span_lengths`，用于保持旧状态行对齐逻辑，同时避免 `_parse_longest()` 重复扫描。
- 保留旧 `position_grammar` 填充规则，使用最后一个 grammar token 长度作为固定重复次数，确保验证输出完全一致。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

```bash
PYTHONPATH=.:src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest tests.test_generate_grammar_process
PYTHONPATH=.:src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest tests.test_generate_grammar_grammar
PYTHONPATH=.:src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest discover -s tests
PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python script/generate_grammar/validate_generate_grammar.py --quiet
```

结果：

- `tests.test_generate_grammar_process`: 5 tests OK。
- `tests.test_generate_grammar_grammar`: 5 tests OK。
- `unittest discover -s tests`: 23 tests OK。
- 全量验证：`Validation passed for 34 files.`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

03-03 可以在 `ParsedSequence` 基础上重写 `_organize_discrete_data()` 的内部矩阵构建流程，并继续使用当前过程测试保护 parent/child/condition 矩阵。

---
*Phase: 03-optimize-generateGrammar*
*Completed: 2026-05-05*

---
phase: 03-optimize-generateGrammar
plan: 03-05
subsystem: algorithm
tags: [generate_grammar, skip-gram, legacy-adapter]
requires:
  - phase: 03-04
    provides: 清晰的 learn 主循环和候选评分边界
provides:
  - SkipGramCandidateTrace 过程指标
  - _build_skip_gram_sequence N 插入映射函数
  - _score_skip_gram_sequence skip-gram BD score 函数
  - legacy adapter 中旧 gram 字段重建逻辑
affects: [generate_grammar, validation-adapter, structured-output]
tech-stack:
  added: []
  patterns: [trace-only diagnostics, adapter-only legacy reconstruction]
key-files:
  created: []
  modified:
    - src/LoPS/generate_grammar/grammar.py
    - src/LoPS/generate_grammar/structured.py
    - script/generate_grammar/legacy_adapter.py
    - tests/test_generate_grammar_process.py
    - tests/test_generate_grammar_grammar.py
    - tests/test_generate_grammar_validation.py
key-decisions:
  - "N 插入映射保留旧实现的单步 if 逻辑，每个解析 token 后最多插入一个 N。"
  - "SkipGramCandidateTrace 只用于测试和过程解释，不进入正式输出。"
  - "正式 structured 输出移除 parsed.position_grammar，旧 gram 字段由 legacy adapter 重建。"
patterns-established:
  - "旧格式兼容逻辑集中在 script/generate_grammar/legacy_adapter.py。"
  - "skip-gram 的序列构建和评分分离，便于分别测试 N 位置和 posterior。"
requirements-completed: [OPT-04, OPT-05, OPT-06, OPT-07]
duration: 4 min
completed: 2026-05-05
---

# Phase 03 Plan 03-05: 重构 skip-gram 和输出适配边界 Summary

**skip-gram N 插入与 posterior trace 分离，旧 gram 字段从验证适配器重建**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-05T04:39:19Z
- **Completed:** 2026-05-05T04:43:37Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- 新增 `SkipGramCandidateTrace`，记录 `sequence_with_n`、`n_insert_positions`、`n_parent`、`target_child`、score 和 posterior。
- `detect_skip_gram()` 拆分为 `_build_skip_gram_sequence()` 与 `_score_skip_gram_sequence()`，保留旧 N 插入和窗口判断语义。
- 正式结构化输出移除 `parsed.position_grammar`，避免为了旧 `gram` 字段保留核心冗余字段。
- `legacy_adapter.py` 从 `parsed.sequence` 和 grammar token 顺序重建旧 `gram` 字段，验证适配逻辑继续与正式模块隔离。

## Task Commits

1. **Task 2: 重构 detect_skip_gram 内部表达** - `e91616b`
2. **Task 3: 清理正式输出与旧格式适配边界** - `8c6e691`
3. **Task 1: 建立 skip-gram 过程测试** - `f4cf386`

## Files Created/Modified

- `src/LoPS/generate_grammar/grammar.py` - 新增 skip-gram trace 和私有函数，移除 `GrammarLearningResult.position_grammar`。
- `src/LoPS/generate_grammar/structured.py` - 正式 parsed 输出不再包含 `position_grammar`。
- `script/generate_grammar/legacy_adapter.py` - 新增 `_legacy_position_grammar()` 重建旧 `gram` 字段。
- `tests/test_generate_grammar_process.py` - 新增 skip-gram 过程快照测试。
- `tests/test_generate_grammar_grammar.py` - 同步 `GrammarLearningResult` 构造参数。
- `tests/test_generate_grammar_validation.py` - 断言正式输出不包含 `parsed.position_grammar`。

## Decisions Made

- 不改变 skip-gram 的 `N` 插入位置、窗口边界、BD score 参数或 posterior 阈值。
- 不把旧格式 `gram` 字段反向引入核心 structured 输出。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

```bash
PYTHONPATH=.:src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest tests.test_generate_grammar_process tests.test_generate_grammar_validation
PYTHONPATH=.:src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest discover -s tests
PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python script/generate_grammar/validate_generate_grammar.py --quiet
```

结果：

- 局部测试：12 tests OK。
- `unittest discover -s tests`: 26 tests OK。
- 全量验证：`Validation passed for 34 files.`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

03-06 可以执行最终过程测试、历史测试、34 文件全量验证和计时验证，并写入 Phase 3 验证报告。

---
*Phase: 03-optimize-generateGrammar*
*Completed: 2026-05-05*

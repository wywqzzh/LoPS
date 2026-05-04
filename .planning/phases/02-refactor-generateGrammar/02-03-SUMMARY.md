---
phase: 02-refactor-generateGrammar
plan: 02-03
subsystem: grammar-core
tags: [python, numpy, pandas, unittest, tokenized-grammar]
requires:
  - phase: 02-refactor-generateGrammar
    provides: "02-01 foundation 和 02-02 scoring"
provides:
  - "token 化 grammar 学习核心"
  - "最长匹配解析"
  - "离散 parent/child/condition 数据组织"
  - "skip-gram 检测"
  - "grammar 核心单元测试"
affects: [generate_grammar, grammar-core, phase-2]
tech-stack:
  added: []
  patterns: ["纯内存核心算法", "token 序列替代旧占位符", "核心学习与 IO/legacy 输出分离"]
key-files:
  created:
    - src/LoPS/generate_grammar/grammar.py
    - tests/test_generate_grammar_grammar.py
  modified: []
key-decisions:
  - "核心算法使用 G-L / E-A 形式的 token，不生成旧占位符。"
  - "parse_probabilities 保留旧 parse_pro 的默认行为，用于后续 legacy 输出一致性。"
  - "skip-gram 在核心层使用 skip_gram_target='E-A'，旧字符串兼容留给 legacy 层。"
patterns-established:
  - "GrammarLearner 只接收内存数据并返回 GrammarLearningResult，不读写文件。"
  - "真实文件 smoke test 使用 031222-401.pkl 覆盖完整 learn 调用。"
requirements-completed: []
duration: 9 min
completed: 2026-05-04
---

# Phase 2 Plan 02-03: 实现 token 化 grammar 学习核心 Summary

**完成 `GrammarLearner` 核心算法，实现 token 化 chunk 学习、离散数据组织和 skip-gram 检测。**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-04T12:30:00Z
- **Completed:** 2026-05-04T12:39:10Z
- **Tasks:** 4
- **Files modified:** 2

## Accomplishments

- 创建 `GrammarLearningResult`、`OrganizedGrammarData` 和 `SkipGramResult` 数据类。
- 实现 `static_probability()`、`choose_candidate_chunks()` 和 `kl_divergence()`。
- 实现 `GrammarLearner._parse_longest()`、`_parse_probabilities()` 和 `_organize_discrete_data()`。
- 实现 `GrammarLearner.learn()`，使用新 token 表示执行默认路径 grammar chunk 学习。
- 实现 `GrammarLearner.detect_skip_gram()`，使用 `E-A` token 检测旧默认 `N -> EA` 语义。
- 添加 grammar 核心测试，覆盖构造样例和真实 `031222-401.pkl` 文件调用。

## Task Commits

Each task was committed atomically:

1. **Task 1: 定义 grammar 结果数据类和基础统计函数** - `0f0b57e` (feat)
2. **Task 2: 实现解析和离散数据组织** - `6bb359c` (feat)
3. **Task 3: 实现 learn 和 detect_skip_gram** - `a98ccd9` (feat)
4. **Task 4: 添加 grammar 核心单元测试** - `f9ebe29` (test)

## Files Created/Modified

- `src/LoPS/generate_grammar/grammar.py` - token 化 grammar 学习核心。
- `tests/test_generate_grammar_grammar.py` - grammar 核心单元测试。

## Verification

已通过：

```bash
PYTHONPATH=src conda run -n fmri python -m unittest tests.test_generate_grammar_grammar
PYTHONPATH=src conda run -n fmri python -m unittest tests.test_generate_grammar_scoring
PYTHONPATH=src conda run -n fmri python -m unittest tests.test_generate_grammar_foundation tests.test_generate_grammar_scoring tests.test_generate_grammar_grammar
```

最终全量当前测试结果：

```text
Ran 12 tests in 0.648s
OK
```

## Decisions Made

- 核心 grammar 学习不读文件、不写文件，也不接触旧占位符映射。
- 新 chunk 直接由 `combine_tokens(parent, child)` 生成，例如 `"G-L"`、`"E-A"`。
- 候选过滤保留旧算法的 parent/child 排除、基础 token 交集跳过、pair frequency 阈值和 KL 收敛规则。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

`02-04` 可以继续实现 legacy/structured 输出适配、pipeline 编排和运行脚本。

---
*Phase: 02-refactor-generateGrammar*
*Completed: 2026-05-04*

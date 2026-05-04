---
phase: 02-refactor-generateGrammar
plan: 02-05
subsystem: validation
tags: [python, unittest, validation, data-provenance, exact-comparison]
requires:
  - phase: 02-refactor-generateGrammar
    provides: "02-04 运行入口和输出 pipeline"
provides:
  - "legacy 精确比较验证脚本"
  - "验证工具单元测试"
  - "数据来源记录"
  - "全量 34 文件逐 key/value 验证报告"
affects: [generate_grammar, validation, phase-2]
tech-stack:
  added: []
  patterns: ["精确比较", "无数值容差", "外部数据只读记录"]
key-files:
  created:
    - script/validate_generate_grammar.py
    - tests/test_generate_grammar_validation.py
    - data/generate_grammar/README.md
    - .planning/phases/02-refactor-generateGrammar/02-VERIFICATION.md
  modified: []
key-decisions:
  - "默认路径无随机过程，不设置随机种子。"
  - "新输出整体 pickle 不以旧文件 MD5 作为通过条件，验证目标是 new['legacy'] 与旧输出逐 key/value 精确一致。"
  - "不复制外部 Pacman 数据到 LoPS，仅记录只读来源和基准路径。"
patterns-established:
  - "验证脚本先运行新 pipeline，再读取新输出 legacy 与旧基准比较。"
  - "DataFrame、ndarray、列表、字典和标量分别使用精确比较。"
requirements-completed: [DATA-01, DATA-04, VERF-01, VERF-02, VERF-03, VERF-04, VERF-05, VERF-06, VERF-07, VERF-08]
duration: 7 min
completed: 2026-05-04
---

# Phase 2 Plan 02-05: 建立验证脚本、数据来源记录和完成验证报告 Summary

**完成验证闭环：全量生成新输出，并证明 `legacy` 与旧 `grammar2` 基准 34/34 文件逐 key/value 精确一致。**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-04T12:50:30Z
- **Completed:** 2026-05-04T12:57:28Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- 创建 `script/validate_generate_grammar.py`，实现 `compare_values()`、`compare_legacy_dict()` 和 `validate_outputs()`。
- 添加验证工具单元测试，覆盖 list、ndarray、DataFrame、缺失 key 和代表性 legacy key。
- 创建 `data/generate_grammar/README.md`，记录只读数据来源、固定旧基准和不复制数据的原因。
- 运行 `unittest discover`，18 个测试全部通过。
- 运行验证脚本，生成 34 个新输出并与旧 `grammar2/` 基准逐 key/value 精确比较通过。
- 写入 `.planning/phases/02-refactor-generateGrammar/02-VERIFICATION.md`。

## Task Commits

Each task was committed atomically:

1. **Task 1: 实现 legacy 输出精确比较工具** - `fd88077` (feat)
2. **Task 2: 添加验证脚本测试** - `4502114` (test)
3. **Task 3: 记录数据来源和不复制数据的原因** - `893693d` (docs)
4. **Task 4: 运行全量验证并写入验证报告** - `6cb5461` (docs)

## Files Created/Modified

- `script/validate_generate_grammar.py` - 旧新输出精确比较脚本。
- `tests/test_generate_grammar_validation.py` - 验证工具测试。
- `data/generate_grammar/README.md` - 数据来源记录。
- `.planning/phases/02-refactor-generateGrammar/02-VERIFICATION.md` - 全量验证报告。

## Verification

已通过：

```bash
PYTHONPATH=src conda run -n fmri python -m unittest discover -s tests
PYTHONPATH=src conda run -n fmri python script/validate_generate_grammar.py
find src/LoPS/temp -mindepth 1 | wc -l
```

结果：

```text
Ran 18 tests in 1.748s
OK
Validation passed for 34 files.
0
```

## Decisions Made

- 由于新输出顶层包含 `legacy` 和 `structured`，不以整文件 MD5 与旧 pickle 一致作为通过条件。
- 默认路径无随机过程，本轮不注入 seed，也不需要 `src/LoPS/temp` 中的临时旧实现。
- 外部数据只读引用，不复制进 LoPS 仓库。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Phase Completion

Phase 2 的 5 个执行计划已全部完成。新实现、运行脚本、验证脚本、数据来源记录和验证报告均已落地。

---
*Phase: 02-refactor-generateGrammar*
*Completed: 2026-05-04*

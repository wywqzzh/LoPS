---
quick_id: 260505-dek
slug: generategrammar
status: complete
completed: 2026-05-05T09:44:08+08:00
commit: uncommitted
---

# Quick 任务总结：隔离 generateGrammar 旧格式兼容

## 完成内容

- 删除 `src/LoPS/generate_grammar/legacy.py`，正式核心包不再包含旧格式输出转换模块。
- 修改 `src/LoPS/generate_grammar/pipeline.py`，核心 pipeline 只输出新版本结构，不再返回 `legacy`/`structured` 双字典。
- 修改 `src/LoPS/generate_grammar/config.py`，移除 `baseline_grammar_dir`，旧基准路径只属于验证脚本。
- 修改 `src/LoPS/generate_grammar/structured.py`，在新结构 `parsed.original_sequence` 中保留原始 token 序列，供独立验证适配层使用。
- 新增 `script/generate_grammar_legacy_adapter.py`，提供统一转换接口 `convert_generate_grammar_output_to_legacy()`。
- 修改 `script/validate_generate_grammar.py`，验证流程先运行新 pipeline 生成新结构，再通过转换接口映射到旧格式，与 `data/generate_grammar/baseline/grammar` 比较。
- 更新测试：核心 pipeline 测试只验证新结构，验证测试单独覆盖旧格式转换接口。

## 验证

已运行：

```bash
PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest discover -s tests
PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python script/run_generate_grammar.py --max-iterations 1 --output-dir data/generate_grammar/smoke-output
PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python script/validate_generate_grammar.py
rg -n "legacy|LEGACY|baseline_grammar_dir|build_legacy_output|LoPS\.generate_grammar\.legacy|\"legacy\"" src/LoPS/generate_grammar --glob '!*.pkl'
PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python -c "import pandas as pd; data=pd.read_pickle('data/generate_grammar/refactored-output/grammar/031222-401.pkl'); print(sorted(data.keys())); print('legacy' in data)"
```

结果：

- 单元测试：18 个测试通过。
- 运行脚本：生成 34 个新结构输出文件。
- 一致性验证：转换接口映射后 `Validation passed for 34 files.`。
- 核心包扫描：`src/LoPS/generate_grammar` 中没有 `legacy`、`baseline_grammar_dir`、`build_legacy_output` 或旧格式模块引用。
- 代表性新输出顶层字段为 `['grammar', 'parameters', 'parsed', 'skip_gram', 'source']`，不包含 `legacy`。

## 提交状态

本 quick 任务未创建 git commit。当前工作区在任务开始前已有多项未提交修改，直接提交会混入非本任务内容。

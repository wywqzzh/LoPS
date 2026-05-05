---
quick_id: 260505-dek
slug: generategrammar
status: in_progress
created: 2026-05-05
---

# Quick 任务计划：隔离 generateGrammar 旧格式兼容

## 目标

Phase 2 的正式新版本代码不应继续输出或依赖旧版本格式。核心 `src/LoPS/generate_grammar` 只生成新结构；为了验证新旧结果一致性，在 `script` 下提供统一转换接口，把新结构映射到旧输出格式后再与旧基准比较。

## 实施范围

- 从核心 pipeline 移除 `legacy` 输出。
- 删除正式包中的旧格式转换模块。
- 从核心配置 `GenerateGrammarConfig` 中移除验证基准路径。
- 新增脚本层旧格式适配接口。
- 更新验证脚本：运行新 pipeline 后，读取新输出并通过适配接口转换为旧格式再比较。
- 更新测试：核心测试只验证新结构，验证测试单独覆盖转换接口。

## 验证

- 运行全部单元测试。
- 运行 `script/run_generate_grammar.py`，确认默认路径输出新结构。
- 运行 `script/validate_generate_grammar.py`，确认通过转换接口后 34 个文件与旧基准一致。
- 搜索 `src/LoPS/generate_grammar`，确认核心包不再包含 `legacy` 模块或 `legacy` 输出路径。

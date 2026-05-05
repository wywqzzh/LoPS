---
phase: 03-optimize-generateGrammar
status: passed
verified_at: 2026-05-05T12:46:26+08:00
environment: conda LoPS
validation_scope: generate_grammar algorithm optimization
---

# Phase 3 验证报告：generateGrammar 顶层算法审计与优化

## 结论

Phase 3 通过验证。优化后的 `generate_grammar` 正式模块在当前仓库数据上完成 34 个被试全量运行，新输出经 `script/generate_grammar/legacy_adapter.py` 统一转换后，与基准输出逐 key/value 完全一致。

本阶段同时通过新增过程一致性测试和 Phase 2 历史测试，验证范围覆盖解析、概率统计、离散数据组织、BD score 候选评分、主循环候选选择、skip-gram 的 `N` 插入和 posterior 计算。

## 执行环境

- 日期：2026-05-05
- 环境：`/home/zzh/anaconda3/envs/LoPS/bin/python`
- 项目目录：`/home/zzh/project/LoPS`
- 数据目录：`data/generate_grammar`
- 验证适配器：`script/generate_grammar/legacy_adapter.py`

## 验证命令

```bash
PYTHONPATH=.:src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest tests.test_generate_grammar_process
PYTHONPATH=.:src /home/zzh/anaconda3/envs/LoPS/bin/python -m unittest discover -s tests
PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python script/generate_grammar/validate_generate_grammar.py --quiet
/usr/bin/time -f 'elapsed=%E user=%U sys=%S' env PYTHONPATH=src /home/zzh/anaconda3/envs/LoPS/bin/python script/generate_grammar/validate_generate_grammar.py --quiet
```

## 过程一致性

`tests.test_generate_grammar_process` 当前包含 8 个过程测试，全部通过：

- `_parse_longest()`：验证最长匹配解析得到的 token 序列、token 时间、频次和位置映射。
- `_parse_probabilities()`：验证概率统计和解析结果共用同一套基础解析过程。
- `_build_parsed_sequence()`：验证统一解析结构与公开解析入口输出一致。
- `_organize_discrete_data()`：验证数组化后的 parent、child、condition 矩阵、状态名顺序和状态依赖邻接矩阵。
- `bd_score()` 的 pair posterior：验证候选转移统计仍来自带先验的 BD score，而不是被误改成纯频次统计。
- `_score_candidate_pair()`：验证候选评分中的 `score_with_parent`、`score_without_parent`、`score_ratio`、`pair_posterior` 和 `pair_frequency`。
- `_select_next_chunk()`：验证候选选择仍遵守现有 ratio 排序和 `candidate_ratio_keep` 保留规则。
- `_build_skip_gram_sequence()` 与 `_score_skip_gram_sequence()`：验证 `N` 的插入位置、`n_parent`、`target_child`、score、posterior 和最终 skip-gram 判断。

执行结果：

```text
Ran 8 tests in 0.016s
OK
```

测试过程中，小型空依赖图 fixture 会触发 `learn_state_condition_links()` 中的既有 `RuntimeWarning: invalid value encountered in scalar divide`。该 warning 来自极小过程样例中的空条件边界，不改变断言结果，也未出现在 34 个被试全量验证的失败路径中。

## 历史测试

完整测试发现命令通过：

```text
Ran 26 tests in 0.060s
OK
```

这说明 Phase 2 已有 token、配置、数据读取、状态图读取、scoring、核心学习、pipeline 和验证适配器行为没有因为 Phase 3 优化发生回归。

## 全量一致性验证

34 个被试全量验证通过：

```text
Validation passed for 34 files.
```

验证标准保持为严格逐 key/value 一致：

- 正式新输出不直接兼容旧格式。
- 旧格式转换只发生在 `script/generate_grammar/legacy_adapter.py`。
- `gram` 等旧字段由适配器从新结构重新构造。
- 34 个文件的新输出经适配后与 `data/generate_grammar` 中的基准逐 key/value 一致。
- 未使用数值容差。

## 性能观察

分析基线记录为：

```text
elapsed=0:32.46 user=47.36 sys=0.15
```

Phase 3 完成后的计时验证结果为：

```text
Validation passed for 34 files.
elapsed=0:10.20 user=25.06 sys=0.20
```

本次优化主要来自顶层数据流收敛、解析过程合并、离散数据数组化和候选评分边界整理。耗时变化是同仓库同命令下的观察结果，不作为未来环境的硬性性能承诺；Phase 3 的硬验收仍是过程一致性和 34 文件全量一致性。

## 已验证的设计约束

- 未引入 `TransitionStats` 预筛选，候选转移 posterior 仍由 `bd_score(data_child, data_parent, 2, 2, 1)` 计算。
- 未做候选 frequency 预筛选，避免改变低频候选的可恢复行为。
- 未做状态条件缓存，避免把行为验证风险扩大到状态依赖图层。
- 未做批处理并行化，Phase 3 只处理单文件核心算法和数据流优化。
- 正式模块不依赖旧版本代码、旧版本数据路径或旧输出格式。
- 旧格式兼容逻辑只在验证适配器中存在，不反向污染核心模块。

## 保留权衡

- `bd_score()` 数学公式未改写。本阶段只验证其调用和数据输入边界，避免把公式级改写与顶层流程优化混在一起。
- `choose_candidate_chunks()` 的排序和保留规则保持不变，只通过 `_select_next_chunk()` 包装，使主循环更清楚。
- skip-gram 的 `N` 映射方式可以在内部表达上更清晰，但插入逻辑、插入位置和 posterior 判断保持过程一致。

## 一致性结论

Phase 3 满足用户要求：优化不是只看最终输出，而是对相同输入下的重要中间指标建立过程测试，并继续通过历史测试和 34 个被试的全量最终输出验证。


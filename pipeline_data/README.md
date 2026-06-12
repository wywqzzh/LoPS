# 完整数据处理流程数据目录

`pipeline_data/` 是完整非视频数据处理流程的统一数据根目录。除原始 `.mat`
数据使用软链接接入外，后续每一步生成的数据都写入本目录，避免和
`data/` 下的验证数据、阶段数据混在一起。

## 目录结构

- `constant_data/`：fMRI 迷宫常量表，包含 `adjacent_map_fmri.csv` 和 `dij_distance_map_fmri.csv`。
- `pacman_data/raw_mat_data`：指向 `data/pacman_data/raw_mat_data` 的软链接，作为原始输入入口。
- `pacman_data/raw_subject_data/`：由 raw mat 转换得到的单被试逐 trial 数据。
- `pacman_data/frame_data/`：由 raw subject 数据转换得到的 frame data。
- `human_tile_data_preprocess/tile_data/`：从 frame data 抽样得到的 tile data。
- `human_tile_data_preprocess/corrected_tile_data/`：插入缺失路径点并修正位置后的 tile data。
- `hierarchical_utility/utility_data/`：预估 9 类策略 utility 后的数据。
- `correct_utility_human/corrected_utility_data/`：把不可走方向 Q 值修正为 `-np.inf` 后的数据。
- `dynamic_strategy_fitting/weight_data/`：动态策略拟合得到的权重数据。
- `revise_human_weight/corrected_weight_data/`：规则修正后的权重数据。
- `extract_features_human/feature_data/`：连续特征数据。
- `extract_features_human/discrete_feature_data/`：离散特征数据。
- `human_fmri_data_preprocess/fmri_discrete_feature_data_ghost2/`：ghost2 离散特征数据。
- `human_fmri_data_preprocess/fmri_discrete_feature_data_ghost4/`：ghost4 离散特征数据。
- `human_fmri_data_preprocess/fmri_formed_data_ghost2/`：ghost2 formed 数据。
- `human_fmri_data_preprocess/strategy_sequence/`：grammar 和状态图使用的策略序列。
- `state_dependency_graph/state_dependency_graph_data/`：状态依赖图结果。
- `generate_grammar/grammar/`：最终 grammar 输出。

## 运行命令

以下命令都在仓库根目录执行：

```bash
cd /home/zzh/project/LoPS
```

1. raw mat 到 raw subject data：

```bash
PYTHONPATH=src python script/pacman_data/run_mat_to_raw_subject_data.py \
  --raw-root pipeline_data/pacman_data/raw_mat_data \
  --output-dir pipeline_data/pacman_data/raw_subject_data \
  --workers 34
```

2. raw subject data 到 frame data：

```bash
PYTHONPATH=src python script/pacman_data/run_raw_subject_data_to_frame_data.py \
  --input-dir pipeline_data/pacman_data/raw_subject_data \
  --output-dir pipeline_data/pacman_data/frame_data \
  --workers 34
```

3. frame data 到 tile data 和 corrected tile data：

```bash
PYTHONPATH=src python script/human_tile_data_preprocess/run_human_tile_data_preprocess.py \
  --frame-dir pipeline_data/pacman_data/frame_data \
  --tile-dir pipeline_data/human_tile_data_preprocess/tile_data \
  --corrected-dir pipeline_data/human_tile_data_preprocess/corrected_tile_data
```

4. corrected tile data 到 hierarchical utility：

```bash
PYTHONPATH=src python script/hierarchical_utility/run_preestimate_fmri_utility.py \
  --input-dir pipeline_data/human_tile_data_preprocess/corrected_tile_data \
  --output-dir pipeline_data/hierarchical_utility/utility_data \
  --constant-dir pipeline_data/constant_data \
  --workers 34
```

5. 修正不可走方向的 utility：

```bash
PYTHONPATH=src python script/correct_utility_human/run_correct_utility_human.py \
  --input-dir pipeline_data/hierarchical_utility/utility_data \
  --adjacent-map pipeline_data/constant_data/adjacent_map_fmri.csv \
  --output-dir pipeline_data/correct_utility_human/corrected_utility_data
```

6. 动态策略权重拟合：

```bash
PYTHONPATH=src python script/dynamic_strategy_fitting/run_dynamic_strategy_fitting.py \
  --input-dir pipeline_data/correct_utility_human/corrected_utility_data \
  --output-dir pipeline_data/dynamic_strategy_fitting/weight_data \
  --adjacent-map pipeline_data/constant_data/adjacent_map_fmri.csv \
  --workers 8
```

7. 修正人类策略权重：

```bash
PYTHONPATH=src python script/revise_human_weight/run_revise_human_weight.py \
  --input-dir pipeline_data/dynamic_strategy_fitting/weight_data \
  --output-dir pipeline_data/revise_human_weight/corrected_weight_data
```

8. 提取连续特征和离散特征：

```bash
PYTHONPATH=src python script/extract_features_human/run_extract_features_human.py \
  --input-dir pipeline_data/revise_human_weight/corrected_weight_data \
  --constant-dir pipeline_data/constant_data \
  --feature-output-dir pipeline_data/extract_features_human/feature_data \
  --discrete-output-dir pipeline_data/extract_features_human/discrete_feature_data
```

9. 生成 human fMRI 预处理数据和 strategy sequence：

```bash
PYTHONPATH=src python script/human_fmri_data_preprocess/run_human_fmri_data_preprocess.py \
  --raw-discrete-dir pipeline_data/extract_features_human/discrete_feature_data \
  --ghost2-discrete-dir pipeline_data/human_fmri_data_preprocess/fmri_discrete_feature_data_ghost2 \
  --ghost4-discrete-dir pipeline_data/human_fmri_data_preprocess/fmri_discrete_feature_data_ghost4 \
  --formed-ghost2-dir pipeline_data/human_fmri_data_preprocess/fmri_formed_data_ghost2 \
  --strategy-sequence-dir pipeline_data/human_fmri_data_preprocess/strategy_sequence
```

10. 生成状态依赖图：

```bash
PYTHONPATH=src python script/state_dependency_graph/run_state_dependency_graph.py \
  --input-dir pipeline_data/human_fmri_data_preprocess/strategy_sequence \
  --output-dir pipeline_data/state_dependency_graph/state_dependency_graph_data
```

11. 生成 grammar：

```bash
PYTHONPATH=src python script/generate_grammar/run_generate_grammar.py \
  --strategy-sequence-dir pipeline_data/human_fmri_data_preprocess/strategy_sequence \
  --state-graph-dir pipeline_data/state_dependency_graph/state_dependency_graph_data \
  --output-dir pipeline_data/generate_grammar/grammar \
  --quiet
```

## 运行后检查

每一步跑完后，可以用下面的命令快速检查输出文件数量：

```bash
find pipeline_data -mindepth 2 -type f -name "*.pkl" | wc -l
find pipeline_data/generate_grammar/grammar -type f | wc -l
```

如果需要重新跑某一步，建议只清理该步骤及其下游输出目录，保留上游结果。

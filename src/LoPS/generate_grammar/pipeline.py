"""generate_grammar 文件级流水线。

本模块负责把单个或多个输入文件组织为核心学习所需的数据，并输出新版本结构化结果。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from LoPS.generate_grammar.config import GenerateGrammarConfig
from LoPS.generate_grammar.data_io import (
    StrategyStateData,
    list_strategy_state_files,
    load_strategy_state_data,
    write_generate_grammar_output,
)
from LoPS.generate_grammar.grammar import GrammarLearner
from LoPS.generate_grammar.state_graph import StateDependencyGraph, load_state_dependency_graph
from LoPS.generate_grammar.structured import build_structured_output


@dataclass
class PreparedStrategyStateData:
    """保存进入 GrammarLearner 前的单文件数据。

    输入语义：由 StrategyStateData 和对应 StateDependencyGraph 预处理得到。
    输出语义：token_sequence 已删除配置指定的 removed_token；n_positions 保存被删除 token 的原始位置；
    state_features 已同步删除对应行并重新编号；其余字段保留输入文件和参与者元数据。
    关键约束：state_features 必须与 token_sequence 等长且逐行对齐，否则 grammar 学习的状态条件会错位。
    """

    input_file_name: str
    token_sequence: list[str]
    n_positions: np.ndarray
    initial_tokens: list[str]
    state_features: pd.DataFrame
    participant_file_names: list[str]
    participant_ids: list[str]
    state_dependencies: StateDependencyGraph


def prepare_strategy_state_data(
    data: StrategyStateData,
    state_dependencies: StateDependencyGraph,
    removed_token: str = "N",
) -> PreparedStrategyStateData:
    """清理单个策略状态数据并构造学习器输入。

    输入语义：data 包含原始 token 序列、状态特征和参与者信息；state_dependencies 是同名状态依赖图；
    removed_token 指定需要从学习序列中临时移除的 token。
    输出语义：返回 PreparedStrategyStateData，其中 token 序列和状态特征已经按 removed_token 删除结果重新对齐。
    关键约束：被删除 token 的原始位置必须保留，用于学习结束后的 skip-gram 检测。
    """

    # 在 grammar 学习前删除所有 removed_token，并保存其原始位置供 skip_gram 使用。
    token_array = np.array(data.token_sequence)
    n_positions = np.where(token_array == removed_token)[0]
    token_sequence = [token for token in data.token_sequence if token != removed_token]
    # state_features 与原始 seq 等长；删除 N 后必须同步删除对应状态行，否则状态与 token 会错位。
    state_features = data.state_features.reset_index(drop=True)
    state_features = state_features.drop(n_positions).reset_index(drop=True)
    return PreparedStrategyStateData(
        input_file_name=data.input_file_name,
        token_sequence=token_sequence,
        n_positions=n_positions,
        initial_tokens=list(data.initial_tokens),
        state_features=state_features,
        participant_file_names=list(data.participant_file_names),
        participant_ids=list(data.participant_ids),
        state_dependencies=state_dependencies,
    )


def process_strategy_state_file(input_file_name: str, config: GenerateGrammarConfig) -> dict[str, Any]:
    """处理单个 StrategySequence 文件并返回结构化输出对象。

    输入语义：input_file_name 是输入目录下的文件名；config 提供输入目录、状态图目录和学习参数。
    输出语义：返回可直接写入磁盘的结构化字典，不在本函数内执行文件写出。
    关键约束：StrategySequence 文件和 StateGraph 文件必须同名，且状态列名由 config.learning.state_names 指定。
    """

    # 单文件处理函数只返回内存结果，不写文件；这样测试和验证脚本都可以复用同一流程。
    strategy_state_data = load_strategy_state_data(
        config.strategy_sequence_dir / input_file_name,
        config.learning.state_names,
    )
    # StateGraph 文件名与 StrategySequence 文件名一一对应。
    state_dependencies = load_state_dependency_graph(config.state_graph_dir / input_file_name)
    prepared = prepare_strategy_state_data(
        strategy_state_data,
        state_dependencies,
        removed_token=config.learning.removed_token,
    )

    # GrammarLearner 接收显式参数和内存数据，不知道输入输出目录。
    learner = GrammarLearner(config.learning)
    grammar_result = learner.learn(
        token_sequence=prepared.token_sequence,
        initial_tokens=prepared.initial_tokens,
        state_features=prepared.state_features,
        state_dependencies=prepared.state_dependencies,
        participant_file_names=prepared.participant_file_names,
        participant_ids=prepared.participant_ids,
    )
    # skip_gram 必须在 grammar 学习完成后执行，因为它依赖最终 parsed_sequence。
    skip_gram = learner.detect_skip_gram(grammar_result, prepared.n_positions)

    # 核心 pipeline 只返回当前模块定义的结构化结果；验证适配逻辑不进入正式流程。
    return build_structured_output(input_file_name, config.learning, grammar_result, skip_gram)


def run_generate_grammar(config: GenerateGrammarConfig) -> list[Path]:
    """批量运行 generate_grammar 流程并写出结果文件。

    输入语义：config 提供输入、状态图、输出目录和学习参数。
    输出语义：返回本轮写出的输出文件路径列表，顺序与排序后的输入文件一致。
    关键约束：运行前会校验配置路径；每个输入文件独立处理并写入 config.output_dir 下的同名文件。
    """

    # 全量运行入口：校验路径、排序枚举输入文件、逐个写入 LoPS 输出目录。
    config.validate()
    output_paths = []
    for input_file_name in list_strategy_state_files(config.strategy_sequence_dir):
        output = process_strategy_state_file(input_file_name, config)
        output_path = config.output_dir / input_file_name
        write_generate_grammar_output(output, output_path)
        output_paths.append(output_path)
    return output_paths

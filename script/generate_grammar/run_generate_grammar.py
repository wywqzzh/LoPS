"""generate_grammar 命令行运行入口。

该脚本读取固定数据目录或用户传入的数据目录，运行新版本流水线并写出结构化结果。
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from LoPS.generate_grammar.config import (
    GenerateGrammarConfig,
    GrammarLearningParams,
)
from LoPS.generate_grammar.pipeline import run_generate_grammar


def parse_args() -> argparse.Namespace:
    """解析 generate_grammar 运行入口的命令行参数。

    返回值包含输入目录、状态图目录、输出目录和学习参数；默认路径指向
    仓库内 ``data/generate_grammar``，调用方可以通过命令行覆盖。
    """
    # 常用数据目录固定在 data/generate_grammar 下，因此参数提供字符串默认值。
    # 用户仍可通过命令行覆盖这些路径，便于比较其它数据集或临时输出目录。
    parser = argparse.ArgumentParser(description="Run LoPS generate_grammar refactor pipeline.")
    parser.add_argument("--strategy-sequence-dir", type=Path, default="data/generate_grammar/input/strategy_sequence")
    parser.add_argument("--state-graph-dir", type=Path, default="data/generate_grammar/input/state_graph")
    parser.add_argument("--output-dir", type=Path, default="data/generate_grammar/refactored-output/grammar")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--max-iterations", type=int, default=100000)
    return parser.parse_args()


def main() -> None:
    """执行 generate_grammar 文件级处理流程并打印输出摘要。

    函数从命令行参数构造配置对象，运行 pipeline 写出结果文件；无返回值，
    运行失败时由底层异常直接暴露给命令行调用方。
    """
    args = parse_args()
    # 单个 alpha 参数同步应用到 chunk、condition 和 skip-gram 三类学习过程。
    learning = replace(
        GrammarLearningParams(),
        chunk_alpha=args.alpha,
        condition_alpha=args.alpha,
        skip_gram_alpha=args.alpha,
        max_iterations=args.max_iterations,
    )
    # GenerateGrammarConfig 集中承载输入、输出和学习参数，pipeline 只消费这个对象。
    config = GenerateGrammarConfig(
        strategy_sequence_dir=args.strategy_sequence_dir,
        state_graph_dir=args.state_graph_dir,
        output_dir=args.output_dir,
        learning=learning,
    )
    output_paths = run_generate_grammar(config)
    # 输出简短运行结果，便于 shell 调用和验证报告记录。
    print(f"Generated {len(output_paths)} files in {config.output_dir}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from LoPS.generate_grammar.config import (
    DEFAULT_BASELINE_GRAMMAR_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_STATE_GRAPH_DIR,
    DEFAULT_STRATEGY_SEQUENCE_DIR,
    GenerateGrammarConfig,
    GrammarLearningParams,
)
from LoPS.generate_grammar.pipeline import run_generate_grammar


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LoPS generate_grammar refactor pipeline.")
    parser.add_argument("--strategy-sequence-dir", type=Path, default=DEFAULT_STRATEGY_SEQUENCE_DIR)
    parser.add_argument("--state-graph-dir", type=Path, default=DEFAULT_STATE_GRAPH_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--baseline-grammar-dir", type=Path, default=DEFAULT_BASELINE_GRAMMAR_DIR)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--max-iterations", type=int, default=100000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    learning = replace(
        GrammarLearningParams(),
        chunk_alpha=args.alpha,
        condition_alpha=args.alpha,
        skip_gram_alpha=args.alpha,
        max_iterations=args.max_iterations,
    )
    config = GenerateGrammarConfig(
        strategy_sequence_dir=args.strategy_sequence_dir,
        state_graph_dir=args.state_graph_dir,
        output_dir=args.output_dir,
        baseline_grammar_dir=args.baseline_grammar_dir,
        learning=learning,
    )
    output_paths = run_generate_grammar(config)
    print(f"Generated {len(output_paths)} files in {config.output_dir}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from LoPS.generate_grammar.config import (
    DEFAULT_BASELINE_GRAMMAR_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_STATE_GRAPH_DIR,
    DEFAULT_STRATEGY_SEQUENCE_DIR,
    GenerateGrammarConfig,
    GrammarLearningParams,
)
from LoPS.generate_grammar.pipeline import run_generate_grammar


def compare_values(old_value: Any, new_value: Any, path: str) -> list[str]:
    if isinstance(old_value, np.ndarray) or isinstance(new_value, np.ndarray):
        if not isinstance(old_value, np.ndarray) or not isinstance(new_value, np.ndarray):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        if not np.array_equal(old_value, new_value):
            return [f"{path}: ndarray mismatch"]
        return []

    if isinstance(old_value, pd.DataFrame) or isinstance(new_value, pd.DataFrame):
        if not isinstance(old_value, pd.DataFrame) or not isinstance(new_value, pd.DataFrame):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        try:
            pd.testing.assert_frame_equal(old_value, new_value, check_exact=True)
        except AssertionError as error:
            return [f"{path}: DataFrame mismatch: {error}"]
        return []

    if isinstance(old_value, Mapping) or isinstance(new_value, Mapping):
        if not isinstance(old_value, Mapping) or not isinstance(new_value, Mapping):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        differences = []
        for key, value in old_value.items():
            key_path = f"{path}.{key}"
            if key not in new_value:
                differences.append(f"{key_path}: missing key")
                continue
            differences.extend(compare_values(value, new_value[key], key_path))
        return differences

    if isinstance(old_value, (list, tuple)) or isinstance(new_value, (list, tuple)):
        if not isinstance(old_value, (list, tuple)) or not isinstance(new_value, (list, tuple)):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        if len(old_value) != len(new_value):
            return [f"{path}: length mismatch {len(old_value)} != {len(new_value)}"]
        differences = []
        for index, old_item in enumerate(old_value):
            differences.extend(compare_values(old_item, new_value[index], f"{path}[{index}]"))
        return differences

    if old_value != new_value:
        return [f"{path}: value mismatch {old_value!r} != {new_value!r}"]
    return []


def compare_legacy_dict(old: Mapping[str, Any], new: Mapping[str, Any], file_name: str) -> list[str]:
    differences = []
    for key, old_value in old.items():
        key_path = f"{file_name}.{key}"
        if key not in new:
            differences.append(f"{key_path}: missing key")
            continue
        differences.extend(compare_values(old_value, new[key], key_path))
    return differences


def validate_outputs(config: GenerateGrammarConfig) -> int:
    if config.baseline_grammar_dir is None:
        raise ValueError("baseline_grammar_dir is required for validation")

    output_paths = run_generate_grammar(config)
    differences = []
    for output_path in output_paths:
        file_name = output_path.name
        baseline_path = config.baseline_grammar_dir / file_name
        old_output = pd.read_pickle(baseline_path)
        new_output = pd.read_pickle(output_path)
        legacy_output = new_output["legacy"]
        differences.extend(compare_legacy_dict(old_output, legacy_output, file_name))

    if differences:
        print("Validation failed:")
        for difference in differences:
            print(difference)
        return 1

    print(f"Validation passed for {len(output_paths)} files.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate LoPS generate_grammar output against legacy grammar2.")
    parser.add_argument("--strategy-sequence-dir", type=Path, default=DEFAULT_STRATEGY_SEQUENCE_DIR)
    parser.add_argument("--state-graph-dir", type=Path, default=DEFAULT_STATE_GRAPH_DIR)
    parser.add_argument("--baseline-grammar-dir", type=Path, default=DEFAULT_BASELINE_GRAMMAR_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--max-iterations", type=int, default=100000)
    return parser.parse_args()


def main() -> int:
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
    return validate_outputs(config)


if __name__ == "__main__":
    sys.exit(main())

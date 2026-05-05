"""generate_grammar 一致性验证入口。

该脚本先运行新版本流水线，再通过验证适配器将结果映射为基准字段并逐项比较。
"""

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
    GenerateGrammarConfig,
    GrammarLearningParams,
)
from LoPS.generate_grammar.pipeline import run_generate_grammar

try:
    # 单元测试从项目根目录导入 script 包；优先使用包路径，避免测试环境与运行入口分叉。
    from script.generate_grammar.legacy_adapter import convert_generate_grammar_output_to_legacy
except ModuleNotFoundError:
    # 直接执行本文件时，Python 会把 script/generate_grammar/ 放入 sys.path，此时使用同目录导入。
    from legacy_adapter import convert_generate_grammar_output_to_legacy


def compare_values(old_value: Any, new_value: Any, path: str) -> list[str]:
    """递归比较两个验证值并返回差异描述列表。

    old_value 与 new_value 可以是标量、列表、元组、字典、ndarray 或 DataFrame；
    path 表示当前值在输出结构中的位置。返回空列表表示完全一致，非空列表
    中每一项都包含可定位的路径和差异类型。
    """
    # 验证目标是与 grammar 基准精确一致；不同类型分别使用最严格的比较方式。
    if isinstance(old_value, np.ndarray) or isinstance(new_value, np.ndarray):
        if not isinstance(old_value, np.ndarray) or not isinstance(new_value, np.ndarray):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        # ndarray 不使用容差；概率数组也必须逐元素完全一致。
        if not np.array_equal(old_value, new_value):
            return [f"{path}: ndarray mismatch"]
        return []

    if isinstance(old_value, pd.DataFrame) or isinstance(new_value, pd.DataFrame):
        if not isinstance(old_value, pd.DataFrame) or not isinstance(new_value, pd.DataFrame):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        try:
            # check_exact=True 明确禁止浮点容差，符合本轮“完全一致”的验证要求。
            pd.testing.assert_frame_equal(old_value, new_value, check_exact=True)
        except AssertionError as error:
            return [f"{path}: DataFrame mismatch: {error}"]
        return []

    if isinstance(old_value, Mapping) or isinstance(new_value, Mapping):
        if not isinstance(old_value, Mapping) or not isinstance(new_value, Mapping):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        differences = []
        for key, value in old_value.items():
            # 只要求基准输出已有 key 在待验输出中存在；额外字段不参与此比较。
            key_path = f"{path}.{key}"
            if key not in new_value:
                differences.append(f"{key_path}: missing key")
                continue
            differences.extend(compare_values(value, new_value[key], key_path))
        return differences

    if isinstance(old_value, (list, tuple)) or isinstance(new_value, (list, tuple)):
        if not isinstance(old_value, (list, tuple)) or not isinstance(new_value, (list, tuple)):
            return [f"{path}: type mismatch {type(old_value).__name__} != {type(new_value).__name__}"]
        # 列表长度先比较，再逐项递归，方便报告精确到 key path 和 index。
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
    """比较单个 pickle 输出字典并返回该文件内的所有差异。

    参数 old 是基准输出字典，new 是待验证输出转换后的字典，file_name 用于
    组成差异路径。函数只检查基准字典中存在的字段，便于报告稳定可读。
    """
    # 单文件比较以基准 pickle 的字段为准，逐 key 递归进入 compare_values。
    differences = []
    for key, old_value in old.items():
        key_path = f"{file_name}.{key}"
        if key not in new:
            differences.append(f"{key_path}: missing key")
            continue
        differences.extend(compare_values(old_value, new[key], key_path))
    return differences


def _render_value(value: Any, max_chars: int | None) -> str:
    """把验证值渲染为适合命令行展示的字符串。

    value 可以是普通 Python 对象、ndarray 或 DataFrame；max_chars 为
    None 时完整输出，否则超过限制后截断并标记剩余字符数。
    """
    # 比对日志需要展示旧值和新值，但部分字段是长数组或 DataFrame。
    # 默认进行字符数截断；传入 None 时输出完整 repr，便于需要精确人工检查时使用。
    if isinstance(value, pd.DataFrame):
        rendered = value.to_string()
    elif isinstance(value, np.ndarray):
        rendered = np.array2string(value, threshold=value.size)
    else:
        rendered = repr(value)

    if max_chars is not None and len(rendered) > max_chars:
        return f"{rendered[:max_chars]}... <truncated {len(rendered) - max_chars} chars>"
    return rendered


def print_subject_comparison(
    file_name: str,
    old_output: Mapping[str, Any],
    converted_output: Mapping[str, Any],
    max_value_chars: int | None,
) -> list[str]:
    """打印单个被试文件的逐字段比较结果。

    file_name 用于显示标题和差异路径；old_output 是基准字段，converted_output
    是待验输出的验证格式字段。函数返回该被试的全部差异，供总体验证汇总。
    """
    # 每个被试逐 key 输出基准值和待验值，同时返回该被试的差异列表。
    print(f"\n===== {file_name} =====")
    subject_differences = []
    for key, old_value in old_output.items():
        key_path = f"{file_name}.{key}"
        if key not in converted_output:
            print(f"[{key}] FAIL")
            print(f"  old: {_render_value(old_value, max_value_chars)}")
            print("  new: <missing>")
            subject_differences.append(f"{key_path}: missing key")
            continue

        new_value = converted_output[key]
        key_differences = compare_values(old_value, new_value, key_path)
        status = "PASS" if not key_differences else "FAIL"
        print(f"[{key}] {status}")
        print(f"  old: {_render_value(old_value, max_value_chars)}")
        print(f"  new: {_render_value(new_value, max_value_chars)}")
        subject_differences.extend(key_differences)

    if subject_differences:
        print(f"Result: FAIL ({len(subject_differences)} differences)")
    else:
        print("Result: PASS (0 differences)")
    return subject_differences


def validate_outputs(
    config: GenerateGrammarConfig,
    baseline_grammar_dir: Path,
    *,
    show_values: bool,
    max_value_chars: int | None,
) -> int:
    """运行 generate_grammar 并与基准 grammar 输出做一致性验证。

    config 指定输入和待验输出目录，baseline_grammar_dir 指定基准 pickle 目录；
    show_values 控制是否打印逐字段值，max_value_chars 控制值展示长度。返回
    0 表示全部文件一致，返回 1 表示存在差异。
    """
    # 验证脚本会先运行 pipeline，再通过脚本层适配接口转换为基准字段用于比较。
    if not baseline_grammar_dir.is_dir():
        raise FileNotFoundError(f"Baseline grammar directory not found: {baseline_grammar_dir}")
    if config.output_dir.resolve() == baseline_grammar_dir.resolve():
        raise ValueError("output_dir must not be the baseline grammar directory")
    output_paths = run_generate_grammar(config)
    differences = []
    for output_path in output_paths:
        file_name = output_path.name
        baseline_path = baseline_grammar_dir / file_name
        old_output = pd.read_pickle(baseline_path)
        new_output = pd.read_pickle(output_path)
        # pipeline 输出保持结构化形态；验证字段还原集中在统一转换接口中。
        legacy_output = convert_generate_grammar_output_to_legacy(new_output)
        if show_values:
            differences.extend(print_subject_comparison(file_name, old_output, legacy_output, max_value_chars))
        else:
            differences.extend(compare_legacy_dict(old_output, legacy_output, file_name))

    if differences:
        print("Validation failed:")
        for difference in differences:
            print(difference)
        return 1

    print(f"Validation passed for {len(output_paths)} files.")
    return 0


def parse_args() -> argparse.Namespace:
    """解析验证脚本命令行参数。

    返回值包含输入目录、状态图目录、基准目录、输出目录、学习参数和
    展示选项；参数名称和默认路径与运行入口保持一致。
    """
    # 参数与 run_generate_grammar.py 保持一致；默认值直接写 data 下的固定目录字符串。
    parser = argparse.ArgumentParser(description="Validate LoPS generate_grammar output against legacy grammar baseline.")
    parser.add_argument("--strategy-sequence-dir", type=Path, default="data/generate_grammar/input/strategy_sequence")
    parser.add_argument("--state-graph-dir", type=Path, default="data/generate_grammar/input/state_graph")
    parser.add_argument("--baseline-grammar-dir", type=Path, default="data/generate_grammar/baseline/grammar")
    parser.add_argument("--output-dir", type=Path, default="data/generate_grammar/refactored-output/grammar")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--max-iterations", type=int, default=100000)
    parser.add_argument("--quiet", action="store_true", help="Only print final validation summary.")
    parser.add_argument(
        "--value-preview-chars",
        type=int,
        default=500,
        help="Maximum characters printed for each old/new value. Use --full-values for no truncation.",
    )
    parser.add_argument("--full-values", action="store_true", help="Print complete old/new values for every key.")
    return parser.parse_args()


def main() -> int:
    """执行命令行验证流程并返回进程退出码。

    函数根据命令行参数构造学习配置，运行验证逻辑并返回 0 或 1；调用方
    可以直接把返回值传给 ``sys.exit``。
    """
    args = parse_args()
    # 验证默认 alpha=0.5，并同步应用到 chunk、condition 和 skip-gram 三处。
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
        learning=learning,
    )
    max_value_chars = None if args.full_values else args.value_preview_chars
    return validate_outputs(
        config,
        args.baseline_grammar_dir,
        show_values=not args.quiet,
        max_value_chars=max_value_chars,
    )


if __name__ == "__main__":
    sys.exit(main())

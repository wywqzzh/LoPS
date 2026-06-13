#!/usr/bin/env python3
"""验证集中 utility 输出和后续拟合输出是否匹配 golden baseline。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from LoPS.calculate_utility import Q_COLUMNS, Q_NORM_COLUMNS  # noqa: E402


DEFAULT_COMPARE_COLUMNS: tuple[str, ...] = (
    "DayTrial",
    "Step",
    "pacmanPos",
    "file",
    "game",
    "next_pacman_dir_fill",
    *Q_COLUMNS,
    *Q_NORM_COLUMNS,
)


def parse_args() -> argparse.Namespace:
    """解析集中 utility 验证参数。

    输入语义：调用方传入新 utility 目录、golden weight_data 目录和可选的新拟合输出目录。
    输出语义：返回可驱动字段比较和完整拟合比较的参数对象。
    关键约束：默认只读取已有输出，不自动运行任何数据处理脚本。
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--utility-dir",
        type=Path,
        default=PROJECT_ROOT / "pipeline_data" / "calculate_utility" / "utility_data",
        help="新 calculate_utility 生成的 utility_data 目录。",
    )
    parser.add_argument(
        "--golden-weight-dir",
        type=Path,
        default=PROJECT_ROOT / "pipeline_data_golden" / "dynamic_strategy_fitting" / "weight_data",
        help="备份中的 golden weight_data 目录。",
    )
    parser.add_argument(
        "--new-weight-dir",
        type=Path,
        default=None,
        help="可选：新拟合输出目录；提供后会与 golden weight_data 做完整比较。",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "pipeline_data" / "validation" / "calculate_utility_validation_report.json",
        help="JSON 验证报告输出路径。",
    )
    parser.add_argument("--max-files", type=int, default=0, help="只验证排序后的前 N 个文件；0 表示全部。")
    return parser.parse_args()


def scalar_is_nan(value: Any) -> bool:
    """判断单个非容器值是否为 NaN。

    输入语义：value 可以是任意 DataFrame 单元格。
    输出语义：只有标量 NaN 返回 True。
    关键约束：数组、列表和 tuple 不直接交给 pandas 转 bool。
    """

    if isinstance(value, (list, tuple, dict, np.ndarray)):
        return False
    try:
        result = pd.isna(value)
    except Exception:
        return False
    return bool(result) if isinstance(result, (bool, np.bool_)) else False


def values_equal(left: Any, right: Any) -> bool:
    """逐单元格比较两个值是否完全一致。

    输入语义：left/right 可以是标量、NaN、tuple、list 或 ndarray。
    输出语义：完全一致返回 True。
    关键约束：数组比较使用精确相等，并把双方同位置 NaN 视为一致。
    """

    if scalar_is_nan(left) and scalar_is_nan(right):
        return True
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        try:
            return bool(np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True))
        except TypeError:
            return bool(np.array_equal(np.asarray(left, dtype=object), np.asarray(right, dtype=object)))
    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        if not isinstance(left, (list, tuple)) or not isinstance(right, (list, tuple)):
            return False
        if len(left) != len(right):
            return False
        return all(values_equal(left_item, right_item) for left_item, right_item in zip(left, right))
    return bool(left == right)


def compare_dataframes(
    left: pd.DataFrame,
    right: pd.DataFrame,
    columns: tuple[str, ...] | list[str],
) -> list[str]:
    """按指定列严格比较两个 DataFrame。

    输入语义：left/right 是待比较表，columns 是需要比较的语义字段。
    输出语义：返回 mismatch 描述列表；空列表表示完全一致。
    关键约束：列顺序只按传入 columns 判断，避免无关列影响 utility 字段验证。
    """

    mismatches: list[str] = []
    if left.shape[0] != right.shape[0]:
        mismatches.append(f"row_count:{left.shape[0]}!={right.shape[0]}")
        return mismatches
    for column in columns:
        if column not in left.columns:
            mismatches.append(f"missing_left_column:{column}")
            continue
        if column not in right.columns:
            mismatches.append(f"missing_right_column:{column}")
            continue
        for row_index, (left_value, right_value) in enumerate(zip(left[column], right[column])):
            if not values_equal(left_value, right_value):
                mismatches.append(f"value:{column}:{row_index}")
                break
    return mismatches


def utility_file_to_weight_file(file_name: str) -> str:
    """把 utility 文件名转换为拟合输出文件名。

    输入语义：file_name 形如 ``*_frame_data-with_Q.pkl``。
    输出语义：返回对应的 ``*-merge_weight-dynamic-res.pkl`` 文件名。
    关键约束：该转换必须与 dynamic_strategy_fitting 的输出命名保持一致。
    """

    if not file_name.endswith(".pkl"):
        raise ValueError(f"不是 pickle 文件名：{file_name}")
    return f"{file_name[:-4]}-merge_weight-dynamic-res.pkl"


def compare_utility_against_golden_weight(
    utility_dir: Path,
    golden_weight_dir: Path,
    max_files: int = 0,
) -> dict[str, Any]:
    """比较新 utility 输出和 golden weight_data 中的 Q/Q_norm 字段。

    输入语义：utility_dir 是新阶段输出，golden_weight_dir 是备份拟合结果。
    输出语义：返回逐文件比较报告。
    关键约束：只比较拟合前关键字段，不检查 weight/contribution 等拟合结果字段。
    """

    utility_files = sorted(utility_dir.glob("*.pkl"))
    if max_files > 0:
        utility_files = utility_files[:max_files]
    if not utility_files:
        raise FileNotFoundError(f"utility 目录中没有可验证的 pickle 文件：{utility_dir}")
    failed_files: dict[str, list[str]] = {}

    for utility_path in utility_files:
        golden_path = golden_weight_dir / utility_file_to_weight_file(utility_path.name)
        if not golden_path.exists():
            failed_files[utility_path.name] = ["missing_golden_weight_file"]
            continue
        utility_data = pd.read_pickle(utility_path)
        golden_data = pd.read_pickle(golden_path)
        mismatches = compare_dataframes(utility_data, golden_data, DEFAULT_COMPARE_COLUMNS)
        if mismatches:
            failed_files[utility_path.name] = mismatches

    return {
        "kind": "utility_vs_golden_weight_q",
        "utility_dir": str(utility_dir),
        "golden_weight_dir": str(golden_weight_dir),
        "checked_files": len(utility_files),
        "failed_files": failed_files,
        "is_exact_match": len(failed_files) == 0,
    }


def compare_weight_outputs(
    new_weight_dir: Path,
    golden_weight_dir: Path,
    max_files: int = 0,
) -> dict[str, Any]:
    """比较新拟合输出和 golden weight_data 的完整 DataFrame。

    输入语义：new_weight_dir 是新拟合输出，golden_weight_dir 是备份拟合结果。
    输出语义：返回逐文件完整比较报告。
    关键约束：比较 shape、列顺序、索引和逐单元格值，不使用数值容差。
    """

    new_files = sorted(new_weight_dir.glob("*.pkl"))
    if max_files > 0:
        new_files = new_files[:max_files]
    if not new_files:
        raise FileNotFoundError(f"新拟合输出目录中没有可验证的 pickle 文件：{new_weight_dir}")
    failed_files: dict[str, list[str]] = {}

    for new_path in new_files:
        golden_path = golden_weight_dir / new_path.name
        if not golden_path.exists():
            failed_files[new_path.name] = ["missing_golden_weight_file"]
            continue
        new_data = pd.read_pickle(new_path)
        golden_data = pd.read_pickle(golden_path)
        mismatches: list[str] = []
        if new_data.shape != golden_data.shape:
            mismatches.append(f"shape:{new_data.shape}!={golden_data.shape}")
        if list(new_data.columns) != list(golden_data.columns):
            mismatches.append("columns")
        if not new_data.index.equals(golden_data.index):
            mismatches.append("index")
        if not mismatches:
            mismatches.extend(compare_dataframes(new_data, golden_data, list(new_data.columns)))
        if mismatches:
            failed_files[new_path.name] = mismatches

    return {
        "kind": "new_weight_vs_golden_weight_full",
        "new_weight_dir": str(new_weight_dir),
        "golden_weight_dir": str(golden_weight_dir),
        "checked_files": len(new_files),
        "failed_files": failed_files,
        "is_exact_match": len(failed_files) == 0,
    }


def main() -> None:
    """命令行入口：执行集中 utility 和可选拟合输出验证。"""

    args = parse_args()
    reports = [
        compare_utility_against_golden_weight(args.utility_dir, args.golden_weight_dir, max_files=args.max_files)
    ]
    if args.new_weight_dir is not None:
        reports.append(compare_weight_outputs(args.new_weight_dir, args.golden_weight_dir, max_files=args.max_files))

    final_report = {
        "reports": reports,
        "is_exact_match": all(report["is_exact_match"] for report in reports),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as file:
        json.dump(final_report, file, ensure_ascii=False, indent=2)
    print(json.dumps(final_report, ensure_ascii=False, indent=2))
    if not final_report["is_exact_match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

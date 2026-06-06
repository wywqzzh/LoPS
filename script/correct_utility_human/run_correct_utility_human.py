#!/usr/bin/env python3
"""修正人类 fMRI utility 数据中不可走方向的 Q 值。

本脚本读取每个被试的 utility pickle，根据 fMRI 迷宫邻接表判断 Pacman
当前位置四个方向是否可走，并把不可走方向对应的 Q 值改为 ``-np.inf``。
脚本是独立运行入口，不依赖旧项目代码或旧项目数据目录。
"""

from __future__ import annotations

import argparse
import ast
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIRECTION_NAMES = ("left", "right", "up", "down")
Q_COLUMNS_7 = (
    "global_Q",
    "local_Q",
    "evade_blinky_Q",
    "evade_clyde_Q",
    "approach_Q",
    "energizer_Q",
    "no_energizer_Q",
)
Q_COLUMNS_9 = (
    "global_Q",
    "local_Q",
    "evade_blinky_Q",
    "evade_clyde_Q",
    "evade_ghost3_Q",
    "evade_ghost4_Q",
    "approach_Q",
    "energizer_Q",
    "no_energizer_Q",
)


def parse_position(value: Any) -> tuple[int, int]:
    """把位置字段解析成坐标 tuple。

    输入语义：value 可以是 ``"(x, y)"`` 字符串，也可以已经是长度为 2 的 tuple/list。
    输出语义：返回 ``(x, y)`` 整数坐标。
    关键约束：不使用 ``eval``，只接受 Python 字面量形式的位置。
    """

    if isinstance(value, tuple) and len(value) == 2:
        return int(value[0]), int(value[1])
    if isinstance(value, list) and len(value) == 2:
        return int(value[0]), int(value[1])
    parsed = ast.literal_eval(str(value))
    if not isinstance(parsed, (tuple, list)) or len(parsed) != 2:
        raise ValueError(f"无法解析位置字段：{value!r}")
    return int(parsed[0]), int(parsed[1])


def read_adjacent_map(path: Path) -> dict[tuple[int, int], dict[str, tuple[int, int] | float]]:
    """读取 fMRI 迷宫邻接表。

    输入语义：path 指向包含 ``pos/left/right/up/down`` 列的 CSV。
    输出语义：返回以位置 tuple 为键、方向名到相邻位置或 ``np.nan`` 为值的字典。
    关键约束：保留旧流程对 tunnel 端点 ``(0, 18)`` 和 ``(30, 18)`` 的邻接补丁。
    """

    adjacent_frame = pd.read_csv(path)
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]] = {}
    for _, row in adjacent_frame.iterrows():
        position = parse_position(row["pos"])
        adjacent_map[position] = {}
        for direction in DIRECTION_NAMES:
            value = row[direction]
            # pandas 把空 CSV 单元读成 NaN；这表示该方向是墙或不可走。
            adjacent_map[position][direction] = np.nan if pd.isna(value) else parse_position(value)

    # tunnel 两端在旧工具函数中被显式补齐；即使 CSV 已经包含，也按固定规则覆盖。
    adjacent_map.setdefault((0, 18), {})
    adjacent_map.setdefault((30, 18), {})
    adjacent_map[(0, 18)].update({"left": (30, 18), "right": (1, 18), "up": np.nan, "down": np.nan})
    adjacent_map[(30, 18)].update({"left": (29, 18), "right": (0, 18), "up": np.nan, "down": np.nan})
    return adjacent_map


def choose_q_columns(data: pd.DataFrame) -> tuple[str, ...]:
    """根据输入表自动选择需要修正的 Q 列。

    输入语义：data 是单个 utility DataFrame。
    输出语义：若 9 个 Q 列都存在则返回 9 列，否则在 7 个基础 Q 列都存在时返回 7 列。
    关键约束：缺列情况必须明确报错，避免静默跳过某个 agent 的 Q 值修正。
    """

    columns = set(data.columns)
    if set(Q_COLUMNS_9).issubset(columns):
        return Q_COLUMNS_9
    if set(Q_COLUMNS_7).issubset(columns):
        return Q_COLUMNS_7
    missing_9 = sorted(set(Q_COLUMNS_9) - columns)
    missing_7 = sorted(set(Q_COLUMNS_7) - columns)
    raise ValueError(f"utility 数据既不满足 9 列也不满足 7 列 Q 输入；missing_9={missing_9}, missing_7={missing_7}")


def correct_utility_table(
    data: pd.DataFrame,
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
) -> tuple[pd.DataFrame, tuple[str, ...], int]:
    """修正一个 utility DataFrame 中不可走方向的 Q 值。

    输入语义：data 必须包含 ``pacmanPos`` 和 7 或 9 个 Q 列；adjacent_map 提供每个格子的四方向邻接。
    输出语义：返回修正后的 DataFrame、实际修正的 Q 列名和写入 ``-np.inf`` 的单元数量。
    关键约束：只修改 Q 数组中墙方向对应的元素，不改变行数、列顺序、索引或其它字段。
    """

    if "pacmanPos" not in data.columns:
        raise ValueError("utility 数据缺少 pacmanPos 列。")

    corrected = data.copy(deep=True)
    q_columns = choose_q_columns(corrected)
    positions = corrected["pacmanPos"].map(parse_position).tolist()
    unavailable_by_row: list[list[int]] = []
    for position in positions:
        if position not in adjacent_map:
            raise KeyError(f"邻接表中找不到 Pacman 位置：{position}")
        adjacent = adjacent_map[position]
        # 邻接表中 tuple 表示可走到相邻格；NaN/float 表示墙或不可走方向。
        unavailable_by_row.append(
            [
                direction_index
                for direction_index, direction in enumerate(DIRECTION_NAMES)
                if not isinstance(adjacent[direction], tuple)
            ]
        )

    changed_cells = 0
    for column in q_columns:
        new_values = []
        for q_value, unavailable_indices in zip(corrected[column], unavailable_by_row):
            q_array = np.array(q_value, copy=True)
            if q_array.shape[0] != len(DIRECTION_NAMES):
                raise ValueError(f"{column} 中存在长度不是 4 的 Q 数组：shape={q_array.shape}")
            for direction_index in unavailable_indices:
                if not np.isneginf(q_array[direction_index]):
                    changed_cells += 1
                q_array[direction_index] = -np.inf
            new_values.append(q_array)
        corrected[column] = new_values

    return corrected, q_columns, changed_cells


def process_directory(input_dir: Path, output_dir: Path, adjacent_map_path: Path) -> list[dict[str, Any]]:
    """批量修正目录下的 utility pickle 文件。

    输入语义：input_dir 是扁平 pickle 输入目录，adjacent_map_path 是当前仓库内的邻接表 CSV。
    输出语义：在 output_dir 下写出同名 pickle，并返回每个文件的处理摘要。
    关键约束：文件之间没有交互，排序只用于稳定日志和验证报告。
    """

    if not input_dir.is_dir():
        raise FileNotFoundError(f"输入目录不存在：{input_dir}")
    input_paths = sorted(input_dir.glob("*.pkl"))
    if not input_paths:
        raise FileNotFoundError(f"输入目录中没有 pickle 文件：{input_dir}")

    adjacent_map = read_adjacent_map(adjacent_map_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for input_path in input_paths:
        data = pd.read_pickle(input_path)
        corrected, q_columns, changed_cells = correct_utility_table(data, adjacent_map)
        output_path = output_dir / input_path.name
        corrected.to_pickle(output_path)
        summaries.append(
            {
                "input_file": input_path.name,
                "rows": int(len(corrected)),
                "q_column_count": len(q_columns),
                "q_columns": list(q_columns),
                "changed_cells": int(changed_cells),
                "output_file": str(output_path),
            }
        )
    return summaries


def values_equal(left: Any, right: Any) -> bool:
    """比较两个 DataFrame 单元格是否完全一致。

    输入语义：left/right 可以是普通标量、NaN、list、tuple 或 numpy array。
    输出语义：完全一致返回 True，否则 False。
    关键约束：数组比较使用精确相等，并把双方同位置 NaN 视为一致。
    """

    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray) or isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        return bool(np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True))
    if pd.isna(left) and pd.isna(right):
        return True
    return bool(left == right)


def compare_output_directories(output_dir: Path, baseline_dir: Path, report_path: Path) -> dict[str, Any]:
    """严格比较两个 corrected utility 输出目录。

    输入语义：output_dir 是新脚本输出，baseline_dir 是显式给定的验证基准目录。
    输出语义：返回比较报告，并把 JSON 报告写入 report_path。
    关键约束：比较文件名、shape、列顺序、索引和逐单元格值；不使用数值容差。
    """

    output_files = sorted(path.name for path in output_dir.glob("*.pkl"))
    baseline_files = sorted(path.name for path in baseline_dir.glob("*.pkl"))
    failed_files: dict[str, list[str]] = {}

    for file_name in sorted(set(output_files) | set(baseline_files)):
        output_path = output_dir / file_name
        baseline_path = baseline_dir / file_name
        if not output_path.exists():
            failed_files[file_name] = ["missing_output"]
            continue
        if not baseline_path.exists():
            failed_files[file_name] = ["extra_output"]
            continue

        output = pd.read_pickle(output_path)
        baseline = pd.read_pickle(baseline_path)
        mismatches: list[str] = []
        if output.shape != baseline.shape:
            mismatches.append("shape")
        if list(output.columns) != list(baseline.columns):
            mismatches.append("columns")
        if not output.index.equals(baseline.index):
            mismatches.append("index")
        if not mismatches:
            # object 列中包含 numpy array，pandas 的默认比较不够直接，因此逐单元格精确比较。
            for column in output.columns:
                for row_index, (left, right) in enumerate(zip(output[column], baseline[column])):
                    if not values_equal(left, right):
                        mismatches.append(f"value:{column}:{row_index}")
                        break
                if mismatches:
                    break
        if mismatches:
            failed_files[file_name] = mismatches

    report = {
        "output_dir": str(output_dir),
        "baseline_dir": str(baseline_dir),
        "output_files": len(output_files),
        "baseline_files": len(baseline_files),
        "failed_files": failed_files,
        "is_exact_match": len(failed_files) == 0,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    return report


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    输入语义：允许调用方覆盖输入、输出、邻接表和验证基准目录。
    输出语义：返回可直接驱动批处理和可选验证流程的参数对象。
    关键约束：默认路径全部位于当前 LoPS 仓库的 data 目录中。
    """

    data_root = PROJECT_ROOT / "data" / "correct_utility_human"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=data_root / "utility_data")
    parser.add_argument("--adjacent-map", type=Path, default=data_root / "constant_data" / "adjacent_map_fmri.csv")
    parser.add_argument("--output-dir", type=Path, default=data_root / "corrected_utility_data")
    parser.add_argument("--validate-against", type=Path, default=None, help="可选：与该基准目录做完全一致性比较。")
    parser.add_argument(
        "--validation-report",
        type=Path,
        default=data_root / "validation" / "correct_utility_human_validation_report.json",
    )
    return parser.parse_args()


def main() -> None:
    """命令行入口：批量修正 human utility 数据，并按需执行严格验证。"""

    args = parse_args()
    summaries = process_directory(args.input_dir, args.output_dir, args.adjacent_map)
    print(
        "correct_utility_human 完成 "
        f"input_files={len(summaries)} "
        f"rows={sum(item['rows'] for item in summaries)} "
        f"changed_cells={sum(item['changed_cells'] for item in summaries)} "
        f"output_dir={args.output_dir}"
    )

    if args.validate_against is not None:
        report = compare_output_directories(args.output_dir, args.validate_against, args.validation_report)
        print(
            "validation "
            f"exact_match={report['is_exact_match']} "
            f"failed_files={len(report['failed_files'])} "
            f"report={args.validation_report}"
        )
        if not report["is_exact_match"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()

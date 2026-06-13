"""human fMRI utility 的集中计算、修正和归一化流程。

本模块把原先分散在 hierarchical utility、correct utility 和 dynamic
strategy fitting 中的 Q 值处理集中到同一个阶段。输出数据已经包含拟合
阶段需要的 ``*_Q``、``*_Q_norm``、``file``、``game`` 和
``next_pacman_dir_fill`` 字段，后续拟合模块只负责使用这些字段。
"""

from __future__ import annotations

import ast
import copy
import pickle
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from LoPS.hierarchical_utility import (
    Q_COLUMNS,
    MapData,
    UtilityConfig,
    estimate_utility_for_dataframe,
    load_map_data_from_directory,
)


DIRECTION_NAMES: tuple[str, ...] = ("left", "right", "up", "down")
Q_NORM_COLUMNS: tuple[str, ...] = tuple(f"{column}_norm" for column in Q_COLUMNS)
PARSED_POSITION_COLUMNS: tuple[str, ...] = (
    "pacmanPos",
    "ghost1Pos",
    "ghost2Pos",
    "ghost3Pos",
    "ghost4Pos",
    "beans",
    "energizers",
)


@dataclass(frozen=True)
class CalculateUtilityConfig:
    """保存集中 utility 计算阶段的配置。

    输入语义：utility_config 控制 raw Q 的策略深度等参数。
    输出语义：配置对象被文件级和目录级处理函数共享。
    关键约束：当前阶段不引入随机拟合参数，只包装 Q 计算本身的配置。
    """

    utility_config: UtilityConfig = UtilityConfig()


def parse_literal_if_needed(value: Any) -> Any:
    """解析数据中可能以字符串保存的 Python 字面量。

    输入语义：value 可以是 ``"(x, y)"``、``"[(x, y)]"`` 等字符串，也可以已经是对象。
    输出语义：字符串使用 ``ast.literal_eval`` 解析，其它值原样返回。
    关键约束：不使用 ``eval``，避免把数据解析和代码执行混在一起。
    """

    if isinstance(value, str):
        return ast.literal_eval(value)
    return value


def parse_position(value: Any) -> tuple[int, int]:
    """把位置字段解析成整数坐标。

    输入语义：value 可以是长度为 2 的 tuple/list，也可以是字符串形式的位置。
    输出语义：返回 ``(x, y)`` 整数坐标。
    关键约束：空方向或墙方向不应传入该函数。
    """

    parsed = parse_literal_if_needed(value)
    if not isinstance(parsed, (tuple, list)) or len(parsed) != 2:
        raise ValueError(f"无法解析位置字段：{value!r}")
    return int(parsed[0]), int(parsed[1])


def load_adjacent_map(path: str | Path) -> dict[tuple[int, int], dict[str, tuple[int, int] | float]]:
    """读取 fMRI 迷宫邻接表。

    输入语义：path 指向包含 ``pos/left/right/up/down`` 列的 CSV。
    输出语义：返回位置到四方向相邻位置的字典，不可走方向用 ``np.nan`` 表示。
    关键约束：显式保留旧流程对 tunnel 两端的邻接补丁。
    """

    adjacent_frame = pd.read_csv(path)
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]] = {}
    for _, row in adjacent_frame.iterrows():
        position = parse_position(row["pos"])
        adjacent_map[position] = {}
        for direction in DIRECTION_NAMES:
            value = row[direction]
            # pandas 会把 CSV 空单元读成 NaN；这里用 float/NaN 表示墙方向。
            adjacent_map[position][direction] = np.nan if pd.isna(value) else parse_position(value)

    # tunnel 两端在旧工具函数中被额外修正；即使 CSV 内容变化，也以该规则为准。
    adjacent_map.setdefault((0, 18), {})
    adjacent_map.setdefault((30, 18), {})
    adjacent_map[(0, 18)].update({"left": (30, 18), "right": (1, 18), "up": np.nan, "down": np.nan})
    adjacent_map[(30, 18)].update({"left": (29, 18), "right": (0, 18), "up": np.nan, "down": np.nan})
    return adjacent_map


def load_calculate_utility_maps(
    constant_dir: str | Path,
) -> tuple[MapData, dict[tuple[int, int], dict[str, tuple[int, int] | float]]]:
    """读取集中 utility 阶段需要的全部地图常量。

    输入语义：constant_dir 包含 ``adjacent_map_fmri.csv`` 和 ``dij_distance_map_fmri.csv``。
    输出语义：返回 raw Q 计算使用的 MapData，以及修正/归一化使用的邻接表。
    关键约束：所有路径由调用方显式传入，本模块不内置项目数据目录。
    """

    constant_dir = Path(constant_dir)
    return load_map_data_from_directory(constant_dir), load_adjacent_map(constant_dir / "adjacent_map_fmri.csv")


def normalize_tunnel_position(position: tuple[int, int]) -> tuple[int, int]:
    """把 tunnel 边界位置映射到归一化逻辑使用的内部格子。

    输入语义：position 是 Pacman 当前坐标。
    输出语义：返回用于查邻接表的坐标。
    关键约束：该规则来自当前拟合阶段的历史实现，影响 ``evade`` 类 Q 的可走方向选择。
    """

    if position in {(-1, 18), (0, 18)}:
        return (1, 18)
    if position in {(31, 18), (30, 18)}:
        return (29, 18)
    return position


def correct_unavailable_q_values(
    data: pd.DataFrame,
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
) -> tuple[pd.DataFrame, int]:
    """把不可走方向的 raw Q 值修正为 ``-np.inf``。

    输入语义：data 是已经追加 raw ``*_Q`` 的单被试 DataFrame。
    输出语义：返回修正后的 DataFrame 和被写入 ``-np.inf`` 的单元数量。
    关键约束：只修改 Q 数组中的墙方向，不改变行数、索引和非 Q 字段。
    """

    if "pacmanPos" not in data.columns:
        raise ValueError("utility 数据缺少 pacmanPos 列。")

    corrected = data.copy(deep=True)
    missing_columns = [column for column in Q_COLUMNS if column not in corrected.columns]
    if missing_columns:
        raise ValueError(f"utility 数据缺少 Q 列：{missing_columns}")

    unavailable_by_row: list[list[int]] = []
    for value in corrected["pacmanPos"]:
        position = parse_position(value)
        if position not in adjacent_map:
            raise KeyError(f"邻接表中找不到 Pacman 位置：{position}")
        adjacent = adjacent_map[position]
        unavailable_by_row.append(
            [
                direction_index
                for direction_index, direction in enumerate(DIRECTION_NAMES)
                if not isinstance(adjacent[direction], tuple)
            ]
        )

    changed_cells = 0
    for column in Q_COLUMNS:
        new_values: list[np.ndarray] = []
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

    return corrected, changed_cells


def normalize_with_inf(values: Any) -> np.ndarray:
    """按旧拟合规则归一化可能包含 ``-inf`` 的四方向 Q 值。

    输入语义：values 是长度为 4 的数组或列表，墙方向可能为 ``-inf``。
    输出语义：返回归一化后的 numpy 数组，有限值全为 0 时保持 0。
    关键约束：最大值只从有限方向中计算，墙方向不参与归一化。
    """

    source = np.asarray(values)
    result = source.copy()
    finite_indices = np.where(~np.isinf(source))[0]
    if set(source[finite_indices]) == {0}:
        result[finite_indices] = 0
    else:
        result[finite_indices] = result[finite_indices] / np.max(result[finite_indices])
    return result


def make_evade_q_non_negative(
    q_values: np.ndarray,
    offset: float,
    position: tuple[int, int],
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
) -> np.ndarray:
    """把 evade/no_energizer 类 Q 值平移到非负尺度并归一化。

    输入语义：q_values 是单帧四方向 Q 数组，offset 是该列全局有限最小值。
    输出语义：返回归一化后的数组。
    关键约束：该函数会原地修改 q_values；这是为了复现当前 weight_data 中保存的 raw Q。
    """

    normalized_position = normalize_tunnel_position(position)
    available_indices: list[int] = []
    for direction in DIRECTION_NAMES:
        adjacent_value = adjacent_map[normalized_position][direction]
        if adjacent_value is not None and not isinstance(adjacent_value, float):
            available_indices.append(DIRECTION_NAMES.index(direction))
    q_values[available_indices] = q_values[available_indices] - offset
    return normalize_with_inf(q_values)


def add_fitting_identity_columns(data: pd.DataFrame) -> pd.DataFrame:
    """补齐拟合阶段需要的 file/game/next_pacman_dir_fill 字段。

    输入语义：data 是修正后的 utility DataFrame，至少包含 ``DayTrial`` 和 ``pacman_dir``。
    输出语义：返回按旧拟合输入顺序整理后的 DataFrame。
    关键约束：``next_pacman_dir_fill`` 按 game 分组由下一行 ``pacman_dir`` 得到。
    """

    if "DayTrial" not in data.columns or "pacman_dir" not in data.columns:
        raise ValueError("计算 utility 需要 DayTrial 和 pacman_dir 字段。")

    # 旧拟合脚本先按 DayTrial 首次出现顺序重组，使同一 trial 行连续。
    day_trials = data.DayTrial.unique()
    result = pd.concat([data[data.DayTrial == day_trial] for day_trial in day_trials]).reset_index(drop=True)

    for column in PARSED_POSITION_COLUMNS:
        if column in result.columns:
            result[column] = result[column].apply(parse_literal_if_needed)

    result["file"] = result.DayTrial
    # game 去掉 round 编号，同一 game 的不同 round 共享下一步方向 shift 边界。
    result["game"] = result.file.str.split("-").apply(lambda parts: "-".join([parts[0]] + parts[2:]))
    grouped_trials: list[pd.DataFrame] = []
    for _, group in result.groupby("game"):
        group = group.copy()
        group["next_pacman_dir_fill"] = group["pacman_dir"].shift(-1)
        grouped_trials.append(copy.deepcopy(group))
    result = pd.concat(grouped_trials)
    result.reset_index(inplace=True, drop=True)
    result["next_pacman_dir_fill"] = result.next_pacman_dir_fill.apply(
        lambda value: value if value is not None else np.nan
    )
    return result


def drop_no_move_trials(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """删除完全没有移动方向的 trial。

    输入语义：data 已包含 ``file`` 和 ``next_pacman_dir_fill``。
    输出语义：返回过滤后的 DataFrame 以及被删除的 trial 名称。
    关键约束：沿用旧拟合逻辑，方向列全是 float/NaN 的 trial 不参与拟合。
    """

    trial_records: list[pd.DataFrame] = []
    dropped_trials: list[str] = []
    for trial_name in np.unique(data.file.values):
        trial_data = data[data.file == trial_name]
        pacman_direction = trial_data.next_pacman_dir_fill
        if np.sum(pacman_direction.apply(lambda value: isinstance(value, float))) == len(pacman_direction):
            dropped_trials.append(str(trial_name))
            continue
        trial_records.append(trial_data)
    if not trial_records:
        raise ValueError("所有 trial 都没有可用移动方向，无法生成拟合用 utility 数据。")
    return pd.concat(trial_records).reset_index(drop=True), dropped_trials


def append_normalized_q_columns(
    data: pd.DataFrame,
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
) -> pd.DataFrame:
    """为修正后的 ``*_Q`` 追加 ``*_Q_norm`` 字段。

    输入语义：data 已经过不可走方向修正，并完成拟合身份字段整理。
    输出语义：返回追加 Q_norm 后的 DataFrame。
    关键约束：evade/no_energizer 类字段会按列级最小有限值平移，并同步修改 raw Q。
    """

    result = data.copy(deep=True)
    for column in Q_COLUMNS:
        if ("evade" not in column) and ("no_energizer" not in column):
            result[f"{column}_norm"] = result[column].apply(normalize_with_inf)
            continue

        flat_values = result[column].explode().values
        finite_values = flat_values[flat_values != -np.inf]
        if len(finite_values) == 0:
            raise ValueError(f"{column} 没有有限 Q 值，无法计算归一化 offset。")
        offset = np.min(finite_values)
        result[f"{column}_norm"] = result[[column, "pacmanPos"]].apply(
            lambda row: make_evade_q_non_negative(row[column], offset, row.pacmanPos, adjacent_map)
            if set(row[column]) != {0}
            else [0, 0, 0, 0],
            axis=1,
        )
    return result


def prepare_calculated_utility_dataframe(
    corrected_utility: pd.DataFrame,
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
) -> tuple[pd.DataFrame, list[str]]:
    """把修正后的 utility 表整理成拟合可直接读取的数据。

    输入语义：corrected_utility 已包含修正后的 raw ``*_Q`` 字段。
    输出语义：返回包含 ``file/game/next_pacman_dir_fill/*_Q_norm`` 的 DataFrame 和删除的 trial。
    关键约束：该函数复现原拟合阶段中会影响 Q_norm 的全部前置数据整理。
    """

    prepared = add_fitting_identity_columns(corrected_utility)
    prepared, dropped_trials = drop_no_move_trials(prepared)
    return append_normalized_q_columns(prepared, adjacent_map), dropped_trials


def calculate_utility_for_dataframe(
    frame_data: pd.DataFrame,
    map_data: MapData,
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
    config: CalculateUtilityConfig | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """对单个 corrected tile DataFrame 执行完整 utility 计算。

    输入语义：frame_data 是 human_tile_data_preprocess 之后的单被试数据。
    输出语义：返回拟合可直接消费的 utility DataFrame 和处理摘要。
    关键约束：raw Q 计算、不可走方向修正和 Q_norm 生成在同一个文件内顺序完成。
    """

    config = CalculateUtilityConfig() if config is None else config
    raw_utility = estimate_utility_for_dataframe(frame_data, map_data, config.utility_config)
    corrected_utility, changed_cells = correct_unavailable_q_values(raw_utility, adjacent_map)
    calculated_utility, dropped_trials = prepare_calculated_utility_dataframe(corrected_utility, adjacent_map)
    summary = {
        "input_rows": int(frame_data.shape[0]),
        "output_rows": int(calculated_utility.shape[0]),
        "changed_cells": int(changed_cells),
        "dropped_trials": dropped_trials,
        "column_count": int(calculated_utility.shape[1]),
    }
    return calculated_utility, summary


def process_calculate_utility_file(
    input_path: str | Path,
    output_path: str | Path,
    map_data: MapData,
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
    config: CalculateUtilityConfig | None = None,
) -> dict[str, Any]:
    """处理单个 corrected tile pickle 并保存集中 utility 输出。

    输入语义：input_path 是单被试 corrected tile 数据，output_path 是目标 pickle。
    输出语义：写出包含 ``*_Q`` 和 ``*_Q_norm`` 的 DataFrame，并返回摘要。
    关键约束：输出文件名由调用方决定，标准运行脚本使用 ``{stem}-with_Q.pkl``。
    """

    input_path = Path(input_path)
    output_path = Path(output_path)
    with input_path.open("rb") as file:
        frame_data = pickle.load(file)
    calculated_utility, summary = calculate_utility_for_dataframe(frame_data, map_data, adjacent_map, config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as file:
        pickle.dump(calculated_utility, file)
    return {
        "input_file": input_path.name,
        "output_file": output_path.name,
        **summary,
    }


def process_calculate_utility_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    map_data: MapData,
    adjacent_map: dict[tuple[int, int], dict[str, tuple[int, int] | float]],
    config: CalculateUtilityConfig | None = None,
    workers: int = 1,
) -> list[dict[str, Any]]:
    """批量处理 corrected tile 目录并生成集中 utility 数据。

    输入语义：input_dir 是扁平 `.pkl` 输入目录，output_dir 是集中 utility 输出目录。
    输出语义：每个输入文件写出一个 ``{stem}-with_Q.pkl``，返回文件摘要列表。
    关键约束：文件之间没有状态共享；排序只用于稳定输出和 seed 无关的验证。
    """

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    config = CalculateUtilityConfig() if config is None else config
    if not input_dir.is_dir():
        raise FileNotFoundError(f"输入目录不存在：{input_dir}")
    input_paths = sorted(input_dir.glob("*.pkl"))
    if not input_paths:
        raise FileNotFoundError(f"输入目录中没有 pickle 文件：{input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = [
        (input_path, output_dir / f"{input_path.stem}-with_Q.pkl", map_data, adjacent_map, config)
        for input_path in input_paths
    ]
    if workers <= 1:
        return [_process_calculate_utility_task(task) for task in tasks]
    with ProcessPoolExecutor(max_workers=min(workers, len(tasks))) as executor:
        return list(executor.map(_process_calculate_utility_task, tasks))


def _process_calculate_utility_task(
    task: tuple[
        Path,
        Path,
        MapData,
        dict[tuple[int, int], dict[str, tuple[int, int] | float]],
        CalculateUtilityConfig,
    ],
) -> dict[str, Any]:
    """执行目录级并行中的单个集中 utility 任务。

    输入语义：task 包含输入路径、输出路径、地图数据、邻接表和配置。
    输出语义：返回 ``process_calculate_utility_file`` 的摘要。
    关键约束：保持顶层函数，便于 multiprocessing pickle。
    """

    input_path, output_path, map_data, adjacent_map, config = task
    return process_calculate_utility_file(input_path, output_path, map_data, adjacent_map, config)

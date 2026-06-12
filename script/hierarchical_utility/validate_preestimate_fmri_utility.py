#!/usr/bin/env python3
"""验证新旧 fMRI hierarchical utility 输出是否完全一致。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
TEMP_ROOT = SRC_ROOT / "LoPS" / "temp"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from LoPS.hierarchical_utility import Q_COLUMNS, UtilityConfig, load_map_data_from_directory, process_utility_directory  # noqa: E402


LEGACY_RUNNER_SOURCE = r'''#!/usr/bin/env python3
"""运行临时旧版 PreEstimation_fmri，用于新旧一致性验证。"""

from __future__ import annotations

import argparse
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    """解析临时旧实现运行参数。"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--constant-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    return parser.parse_args()


def patch_numpy_array(old_module: Any) -> None:
    """为当前 NumPy 版本补齐旧代码的 ragged ghost array 行为。"""

    original_array = old_module.np.array

    def compatible_array(*args: Any, **kwargs: Any) -> Any:
        """优先使用原始 np.array，遇到 ragged array 时回退为 dtype=object。"""

        try:
            return original_array(*args, **kwargs)
        except ValueError as exc:
            if "setting an array element with a sequence" not in str(exc) or "dtype" in kwargs:
                raise
            patched_kwargs = dict(kwargs)
            patched_kwargs["dtype"] = object
            return original_array(*args, **patched_kwargs)

    old_module.np.array = compatible_array


def process_file(task: tuple[str, str, str, str]) -> dict[str, Any]:
    """处理单个输入文件并保存旧版输出。"""

    legacy_root, input_path, output_dir, constant_dir = task
    legacy_root_path = Path(legacy_root)
    if str(legacy_root_path) not in sys.path:
        sys.path.insert(0, str(legacy_root_path))

    from Utils.FileUtils_fmri import readAdjacentMap, readLocDistance, readRewardAmount, readAdjacentPath
    from Behavior_Analysis.HierarchicalModel import PreEstimation_fmri as old

    patch_numpy_array(old)
    input_path_obj = Path(input_path)
    output_dir_obj = Path(output_dir)
    constant_dir_obj = Path(constant_dir)
    adjacent_data = readAdjacentMap(str(constant_dir_obj / "adjacent_map_fmri.csv"))
    locs_df = readLocDistance(str(constant_dir_obj / "dij_distance_map_fmri.csv"))
    adjacent_path = readAdjacentPath(str(constant_dir_obj / "dij_distance_map_fmri.csv"))
    reward_amount = readRewardAmount()

    with input_path_obj.open("rb") as file:
        frame_data = pickle.load(file)
    utility_data = old._individualEstimation(
        frame_data.reset_index(drop=True),
        adjacent_data,
        locs_df,
        adjacent_path,
        reward_amount,
        str(input_path_obj),
    )
    output_dir_obj.mkdir(parents=True, exist_ok=True)
    output_path = output_dir_obj / f"{input_path_obj.stem}-with_Q.pkl"
    with output_path.open("wb") as file:
        pickle.dump(utility_data, file)
    return {"input_file": input_path_obj.name, "output_file": output_path.name, "row_count": int(utility_data.shape[0])}


def main() -> None:
    """临时旧版运行入口。"""

    args = parse_args()
    tasks = [
        (str(args.legacy_root), str(path), str(args.output_dir), str(args.constant_dir))
        for path in sorted(args.input_dir.glob("*.pkl"))
    ]
    if args.workers <= 1:
        summaries = [process_file(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            summaries = list(executor.map(process_file, tasks))
    print(json.dumps({"processed_files": len(summaries), "total_rows": sum(item["row_count"] for item in summaries)}))


if __name__ == "__main__":
    main()
'''


def parse_args() -> argparse.Namespace:
    """解析新旧一致性验证参数。

    输入语义：命令行提供当前仓库输入目录、常量目录、验证目录和旧项目根目录。
    输出语义：返回可驱动新旧两条链路运行和比较的参数对象。
    关键约束：默认输出写入当前仓库 data/hierarchical_utility/validation。
    """

    default_workers = min(34, os.cpu_count() or 1)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROJECT_ROOT / "data/hierarchical_utility/corrected_tile_data",
        help="新旧共同使用的 corrected tile 输入目录。",
    )
    parser.add_argument(
        "--constant-dir",
        type=Path,
        default=PROJECT_ROOT / "data/hierarchical_utility/constant_data",
        help="新旧共同使用的 fMRI 地图常量目录。",
    )
    parser.add_argument(
        "--validation-dir",
        type=Path,
        default=PROJECT_ROOT / "data/hierarchical_utility/validation",
        help="验证输出目录。",
    )
    parser.add_argument(
        "--legacy-root",
        type=Path,
        default=Path("/home/zzh/project/Pacman/Language-of-Problem-Solving"),
        help="旧项目 Language-of-Problem-Solving 根目录，仅用于验证。",
    )
    parser.add_argument(
        "--legacy-input-dir",
        type=Path,
        default=Path("/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/fmriCorrectedTileData"),
        help="旧输出对应的 corrected tile 输入目录，用于确认当前仓库输入是否为同一份数据。",
    )
    parser.add_argument(
        "--legacy-output-dir",
        type=Path,
        default=Path("/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/fmriUtilityData"),
        help="已有旧版完整 utility 输出目录。默认用于全量验证，避免重复运行极慢的旧实现。",
    )
    parser.add_argument(
        "--run-legacy",
        action="store_true",
        help="实际运行临时旧实现生成 legacy 输出；不设置时使用 --legacy-output-dir 中已有输出。",
    )
    parser.add_argument("--workers", type=int, default=default_workers, help="新旧链路目录级并行进程数。")
    return parser.parse_args()


def main() -> None:
    """命令行入口：运行新旧链路并生成严格一致性报告。"""

    args = parse_args()
    args.validation_dir.mkdir(parents=True, exist_ok=True)
    legacy_output_dir = args.validation_dir / "legacy_output" if args.run_legacy else args.legacy_output_dir
    current_output_dir = args.validation_dir / "current_output"
    report_path = args.validation_dir / "validation_report.json"
    legacy_log_path = args.validation_dir / "legacy_stdout.log"
    legacy_error_path = args.validation_dir / "legacy_stderr.log"

    _clean_directory(current_output_dir)
    temp_runner: Path | None = None
    try:
        if args.run_legacy:
            _clean_directory(legacy_output_dir)
            temp_runner = _write_temp_legacy_runner()
            _run_legacy_outputs(args, temp_runner, legacy_output_dir, legacy_log_path, legacy_error_path)
        _run_current_outputs(args, current_output_dir)
        report = compare_output_directories(legacy_output_dir, current_output_dir)
        report.update(
            {
                "input_dir": str(args.input_dir.resolve()),
                "constant_dir": str(args.constant_dir.resolve()),
                "legacy_input_dir": str(args.legacy_input_dir.resolve()),
                "legacy_output_dir": str(legacy_output_dir.resolve()),
                "current_output_dir": str(current_output_dir.resolve()),
                "report_path": str(report_path.resolve()),
                "legacy_mode": "rerun_temp_legacy" if args.run_legacy else "existing_legacy_output",
                "input_identity": compare_input_directories(args.legacy_input_dir, args.input_dir),
            }
        )
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default))
    finally:
        if temp_runner is not None:
            _cleanup_temp_runner(temp_runner)

    print("fMRI hierarchical utility 新旧一致性验证完成")
    print(f"检查文件数：{report['checked_files']}")
    print(f"Q 列差异文件数：{report['q_different_count']}")
    print(f"DataFrame 结构差异文件数：{report['dataframe_different_count']}")
    print(f"验证报告：{report_path.resolve()}")
    if report["q_different_count"] or report["dataframe_different_count"] or report["missing_or_extra_files"]:
        raise SystemExit(1)


def compare_input_directories(legacy_input_dir: Path, current_input_dir: Path) -> dict[str, Any]:
    """比较当前仓库输入与旧输出对应输入是否为同一份数据。

    输入语义：legacy_input_dir 是旧项目输入目录，current_input_dir 是当前仓库复制后的输入目录。
    输出语义：返回文件集合和字节级一致性摘要。
    关键约束：该检查只用于证明验证使用同输入，不读取旧输入参与正式计算。
    """

    legacy_files = {path.name: path for path in sorted(legacy_input_dir.glob("*.pkl"))}
    current_files = {path.name: path for path in sorted(current_input_dir.glob("*.pkl"))}
    common_names = sorted(set(legacy_files) & set(current_files))
    byte_different = [
        name for name in common_names if legacy_files[name].read_bytes() != current_files[name].read_bytes()
    ]
    return {
        "legacy_count": len(legacy_files),
        "current_count": len(current_files),
        "checked_files": len(common_names),
        "legacy_only": sorted(set(legacy_files) - set(current_files)),
        "current_only": sorted(set(current_files) - set(legacy_files)),
        "byte_different_count": len(byte_different),
        "byte_different_examples": byte_different[:5],
        "all_input_files_identical": (
            len(byte_different) == 0
            and not set(legacy_files) - set(current_files)
            and not set(current_files) - set(legacy_files)
        ),
    }


def compare_output_directories(legacy_dir: Path, current_dir: Path) -> dict[str, Any]:
    """比较旧版和新版输出目录。

    输入语义：legacy_dir/current_dir 分别包含同名 `{subject}-with_Q.pkl`。
    输出语义：返回文件集合、字节、DataFrame 结构和 Q 列差异报告。
    关键约束：Q 列使用 `np.array_equal`，不使用数值容差。
    """

    legacy_files = {path.name: path for path in sorted(legacy_dir.glob("*.pkl"))}
    current_files = {path.name: path for path in sorted(current_dir.glob("*.pkl"))}
    common_names = sorted(set(legacy_files) & set(current_files))
    report: dict[str, Any] = {
        "legacy_count": len(legacy_files),
        "current_count": len(current_files),
        "checked_files": len(common_names),
        "missing_or_extra_files": {
            "legacy_only": sorted(set(legacy_files) - set(current_files)),
            "current_only": sorted(set(current_files) - set(legacy_files)),
        },
        "byte_different_count": 0,
        "byte_different_files": [],
        "dataframe_different_count": 0,
        "dataframe_different_examples": [],
        "q_different_count": 0,
        "q_different_examples": [],
        "q_hashes": {},
    }

    for name in common_names:
        legacy_path = legacy_files[name]
        current_path = current_files[name]
        if legacy_path.read_bytes() != current_path.read_bytes():
            report["byte_different_count"] += 1
            report["byte_different_files"].append(name)

        legacy_df = pd.read_pickle(legacy_path)
        current_df = pd.read_pickle(current_path)
        structure_diff = _compare_dataframe_structure(name, legacy_df, current_df)
        if structure_diff is not None:
            report["dataframe_different_count"] += 1
            report["dataframe_different_examples"].append(structure_diff)
            continue

        q_diff = _compare_q_columns(name, legacy_df, current_df)
        if q_diff is not None:
            report["q_different_count"] += 1
            report["q_different_examples"].append(q_diff)
        report["q_hashes"][name] = _hash_q_columns(current_df)

    report["all_bytes_equal"] = report["byte_different_count"] == 0 and not report["missing_or_extra_files"]["legacy_only"] and not report["missing_or_extra_files"]["current_only"]
    report["all_dataframes_equal"] = report["dataframe_different_count"] == 0 and report["q_different_count"] == 0 and not report["missing_or_extra_files"]["legacy_only"] and not report["missing_or_extra_files"]["current_only"]
    report["all_q_values_equal"] = report["q_different_count"] == 0 and not report["missing_or_extra_files"]["legacy_only"] and not report["missing_or_extra_files"]["current_only"]
    return report


def _run_legacy_outputs(
    args: argparse.Namespace,
    temp_runner: Path,
    legacy_output_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> None:
    """运行临时旧版链路生成验证基准输出。

    输入语义：temp_runner 是写入 `src/LoPS/temp` 的旧版运行包装。
    输出语义：旧版输出写入 legacy_output_dir，日志写入 validation 目录。
    关键约束：这里是唯一触碰旧项目代码的地方。
    """

    command = [
        sys.executable,
        str(temp_runner),
        "--legacy-root",
        str(args.legacy_root),
        "--input-dir",
        str(args.input_dir),
        "--output-dir",
        str(legacy_output_dir),
        "--constant-dir",
        str(args.constant_dir),
        "--workers",
        str(args.workers),
    ]
    with stdout_path.open("w") as stdout_file, stderr_path.open("w") as stderr_file:
        subprocess.run(command, check=True, stdout=stdout_file, stderr=stderr_file)


def _run_current_outputs(args: argparse.Namespace, current_output_dir: Path) -> None:
    """运行当前新模块生成待比较输出。

    输入语义：args 提供当前仓库数据和常量路径。
    输出语义：新版输出写入 current_output_dir。
    关键约束：使用默认 `UtilityConfig` 复现 fMRI 目标路径。
    """

    map_data = load_map_data_from_directory(args.constant_dir)
    process_utility_directory(args.input_dir, current_output_dir, map_data, UtilityConfig(), workers=args.workers)


def _compare_dataframe_structure(name: str, legacy_df: pd.DataFrame, current_df: pd.DataFrame) -> dict[str, Any] | None:
    """比较两个输出 DataFrame 的结构和非 Q 原始列。

    输入语义：legacy_df/current_df 是同一被试的新旧输出。
    输出语义：无差异返回 None，有差异返回摘要。
    关键约束：非 Q 列必须完全一致，因为新脚本只允许追加 Q 列。
    """

    if legacy_df.shape != current_df.shape:
        return {"file": name, "reason": "shape", "legacy_shape": legacy_df.shape, "current_shape": current_df.shape}
    if list(legacy_df.columns) != list(current_df.columns):
        return {
            "file": name,
            "reason": "columns",
            "legacy_columns": list(legacy_df.columns),
            "current_columns": list(current_df.columns),
        }
    base_columns = [column for column in legacy_df.columns if column not in Q_COLUMNS]
    if not legacy_df[base_columns].equals(current_df[base_columns]):
        return {"file": name, "reason": "base_columns"}
    return None


def _compare_q_columns(name: str, legacy_df: pd.DataFrame, current_df: pd.DataFrame) -> dict[str, Any] | None:
    """逐行逐元素比较 9 个 Q 列。

    输入语义：legacy_df/current_df 已确认结构一致。
    输出语义：无差异返回 None；有差异返回第一个差异位置和新旧 Q 值。
    关键约束：使用 `np.array_equal`，不使用容差。
    """

    for column in Q_COLUMNS:
        for row_index, (legacy_value, current_value) in enumerate(zip(legacy_df[column], current_df[column])):
            if not np.array_equal(legacy_value, current_value):
                return {
                    "file": name,
                    "column": column,
                    "row_index": row_index,
                    "legacy_value": np.asarray(legacy_value).tolist(),
                    "current_value": np.asarray(current_value).tolist(),
                }
    return None


def _hash_q_columns(dataframe: pd.DataFrame) -> dict[str, str]:
    """计算每个 Q 列的内容 hash。

    输入语义：dataframe 是已经追加 Q 列的输出表。
    输出语义：返回列名到 sha256 的映射。
    关键约束：hash 只作为报告辅助，不替代逐元素比较。
    """

    hashes: dict[str, str] = {}
    for column in Q_COLUMNS:
        digest = hashlib.sha256()
        for value in dataframe[column]:
            array = np.asarray(value)
            digest.update(str(array.dtype).encode("utf-8"))
            digest.update(array.shape.__repr__().encode("utf-8"))
            digest.update(array.tobytes())
        hashes[column] = digest.hexdigest()
    return hashes


def _write_temp_legacy_runner() -> Path:
    """写入临时旧版运行包装。

    输入语义：无。
    输出语义：返回临时 runner 路径。
    关键约束：该文件属于验证临时代码，验证结束必须删除。
    """

    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    runner_path = TEMP_ROOT / "legacy_preestimation_fmri_runner.py"
    runner_path.write_text(LEGACY_RUNNER_SOURCE)
    return runner_path


def _cleanup_temp_runner(runner_path: Path) -> None:
    """删除本轮验证生成的临时旧版 runner。

    输入语义：runner_path 是 `_write_temp_legacy_runner` 创建的文件。
    输出语义：文件被删除；若 temp 目录为空则一并删除。
    关键约束：只删除本脚本创建的文件，不清理未知临时内容。
    """

    if runner_path.exists():
        runner_path.unlink()
    if TEMP_ROOT.exists() and not any(TEMP_ROOT.iterdir()):
        TEMP_ROOT.rmdir()


def _clean_directory(path: Path) -> None:
    """清空并重建一个验证输出目录。

    输入语义：path 是本轮验证可安全覆盖的输出目录。
    输出语义：目录存在且为空。
    关键约束：只用于 data/hierarchical_utility/validation 下的新旧输出目录。
    """

    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _json_default(value: Any) -> Any:
    """把 numpy 和 Path 类型转换为 JSON 可序列化对象。

    输入语义：value 来自验证报告。
    输出语义：返回 json.dumps 可处理的 Python 基础类型。
    关键约束：只用于报告输出，不参与一致性判定。
    """

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


if __name__ == "__main__":
    main()

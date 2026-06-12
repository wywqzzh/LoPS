#!/usr/bin/env python3
"""验证动态策略权重拟合新旧实现是否一致。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
TEMP_ROOT = SRC_ROOT / "LoPS" / "temp" / "dynamic_strategy_fitting"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from LoPS.dynamic_strategy_fitting import (  # noqa: E402
    DEFAULT_AGENTS,
    DynamicStrategyFittingConfig,
    process_dynamic_strategy_directory,
)


LEGACY_WORKER_SOURCE = r'''#!/usr/bin/env python3
"""运行临时旧版 FittingWeightHuman 的单文件 dynamicStrategyFitting。"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    """解析临时旧版 worker 参数。"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-script", type=Path, required=True)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--legacy-cwd", type=Path, required=True)
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--segment-workers", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    """导入临时旧脚本并运行 dynamicStrategyFitting。"""

    args = parse_args()
    os.chdir(args.legacy_cwd)
    if str(args.legacy_root) not in sys.path:
        sys.path.insert(0, str(args.legacy_root))
    np.random.seed(args.seed)

    spec = importlib.util.spec_from_file_location("legacy_fitting_weight_human_all_segments", args.legacy_script)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法导入临时旧脚本：{args.legacy_script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["legacy_fitting_weight_human_all_segments"] = module
    spec.loader.exec_module(module)

    np.random.seed(args.seed)
    module.SEGMENT_RANDOM_SEED = args.seed if args.segment_workers > 1 else None
    module.SEGMENT_WORKERS = args.segment_workers
    args.output_dir.mkdir(parents=True, exist_ok=True)
    module.dynamicStrategyFitting({"filename": str(args.input_path), "save_base": str(args.output_dir)})


if __name__ == "__main__":
    main()
'''


def parse_args() -> argparse.Namespace:
    """解析新旧一致性验证参数。

    输入语义：命令行可以选择完整输入或按 game 抽样输入，并覆盖 GA 与随机参数。
    输出语义：返回用于构造验证目录、临时旧代码和新实现配置的参数对象。
    关键约束：所有验证输入子集、输出和报告都写入当前仓库 data 目录。
    """

    data_root = PROJECT_ROOT / "data"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=data_root / "correct_utility_human" / "corrected_utility_data",
        help="新旧共同使用的 corrected utility 输入目录。",
    )
    parser.add_argument(
        "--adjacent-map",
        type=Path,
        default=data_root / "correct_utility_human" / "constant_data" / "adjacent_map_fmri.csv",
        help="新旧共同使用的 fMRI 邻接表。",
    )
    parser.add_argument(
        "--validation-dir",
        type=Path,
        default=data_root / "dynamic_strategy_fitting" / "validation",
        help="验证产物根目录。",
    )
    parser.add_argument(
        "--legacy-script",
        type=Path,
        default=Path("/home/zzh/project/Pacman/Language-of-Problem-Solving/BasicStrategy/FittingWeightHuman.py"),
        help="旧 FittingWeightHuman.py 路径，仅验证阶段读取。",
    )
    parser.add_argument(
        "--legacy-root",
        type=Path,
        default=Path("/home/zzh/project/Pacman/Language-of-Problem-Solving"),
        help="旧 Language-of-Problem-Solving 根目录，仅验证阶段用于导入 Utils。",
    )
    parser.add_argument(
        "--legacy-cwd",
        type=Path,
        default=Path("/home/zzh/project/Pacman/Language-of-Problem-Solving/BasicStrategy"),
        help="旧脚本导入时使用的工作目录。",
    )
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1), help="文件级并行进程数。")
    parser.add_argument("--segment-workers", type=int, default=1, help="单文件内部段落级并行进程数。")
    parser.add_argument("--seed", type=int, default=20260610, help="随机种子；每个文件加上排序序号。")
    parser.add_argument("--max-files", type=int, default=0, help="只验证排序后的前 N 个文件；0 表示全部。")
    parser.add_argument(
        "--file-name",
        action="append",
        default=[],
        help="指定要验证的文件名；可重复传入。若提供则忽略 --max-files。",
    )
    parser.add_argument(
        "--game-selection",
        choices=["all", "edge"],
        default="all",
        help="all 使用完整文件；edge 每个文件只取编号最小和最大的 game。",
    )
    parser.add_argument("--stay-length", type=int, default=6)
    parser.add_argument("--ga-population-size", type=int, default=100)
    parser.add_argument("--ga-iterations", type=int, default=500)
    parser.add_argument("--ga-mutation-probability", type=float, default=0.01)
    parser.add_argument("--ga-precision", type=float, default=1e-3)
    parser.add_argument("--weight-penalty", type=float, default=0.1)
    parser.add_argument("--vague-threshold", type=float, default=0.51)
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> DynamicStrategyFittingConfig:
    """把验证参数转换为新实现配置。

    输入语义：args 是 parse_args 的返回值。
    输出语义：返回 DynamicStrategyFittingConfig。
    关键约束：该配置也会被写入报告，方便复现实验。
    """

    return DynamicStrategyFittingConfig(
        agents=DEFAULT_AGENTS,
        stay_length=args.stay_length,
        ga_population_size=args.ga_population_size,
        ga_iterations=args.ga_iterations,
        ga_mutation_probability=args.ga_mutation_probability,
        ga_precision=args.ga_precision,
        weight_penalty=args.weight_penalty,
        vague_accuracy_threshold=args.vague_threshold,
        random_seed=args.seed,
        segment_workers=args.segment_workers,
        use_segment_seed=args.segment_workers > 1,
    )


def read_pickle(path: Path) -> Any:
    """读取 pickle 文件。

    输入语义：path 指向 pickle 文件。
    输出语义：返回反序列化对象。
    关键约束：验证阶段不修改源输入文件。
    """

    with path.open("rb") as file:
        return pickle.load(file)


def write_pickle(obj: Any, path: Path) -> None:
    """写出 pickle 文件并创建父目录。

    输入语义：obj 是待保存对象，path 是输出路径。
    输出语义：在 path 写出 pickle。
    关键约束：只写当前仓库 data 下的验证输入子集。
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        pickle.dump(obj, file)


def game_id_from_daytrial(value: Any) -> str:
    """从 DayTrial 中提取 game 编号。

    输入语义：DayTrial 形如 ``1-1-subject``，第一个字段是 game 编号。
    输出语义：返回第一个连字符前的字符串。
    关键约束：只用于验证抽样，不进入正式拟合逻辑。
    """

    return str(value).split("-")[0]


def game_sort_key(game_id: str) -> tuple[int, int | str]:
    """生成 game 编号排序键。

    输入语义：game_id 是字符串。
    输出语义：数字编号按整数排序，非数字编号放在后面按字符串排序。
    关键约束：用于 edge 抽样时选择编号最小和最大的 game。
    """

    if game_id.isdigit():
        return (0, int(game_id))
    return (1, game_id)


def ordered_unique(values: list[str]) -> list[str]:
    """按首次出现顺序去重。

    输入语义：values 是字符串列表。
    输出语义：返回稳定去重后的列表。
    关键约束：用于保留 edge 抽样的首尾顺序。
    """

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def select_input_files(input_dir: Path, args: argparse.Namespace) -> list[Path]:
    """选择本次验证使用的输入文件。

    输入语义：input_dir 是 corrected utility 目录，args 提供文件过滤参数。
    输出语义：返回排序后的输入文件路径。
    关键约束：显式文件名优先于 max-files。
    """

    if args.file_name:
        files = [input_dir / name for name in args.file_name]
    else:
        files = sorted(input_dir.glob("*.pkl"))
        if args.max_files > 0:
            files = files[: args.max_files]
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"验证输入文件不存在：{missing}")
    if not files:
        raise FileNotFoundError(f"没有选择任何验证输入文件：{input_dir}")
    return files


def prepare_validation_inputs(input_paths: list[Path], run_dir: Path, game_selection: str) -> tuple[Path, list[dict[str, Any]]]:
    """准备新旧共同使用的验证输入目录。

    输入语义：input_paths 是源 corrected utility 文件，game_selection 控制是否抽样。
    输出语义：返回验证输入目录和每个文件的抽样摘要。
    关键约束：即使是完整验证，也复制到 validation/input，保证验证产物边界清晰。
    """

    validation_input_dir = run_dir / "input"
    validation_input_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for input_path in input_paths:
        data = read_pickle(input_path)
        if game_selection == "edge":
            if "DayTrial" not in data.columns:
                raise KeyError(f"{input_path} 缺少 DayTrial，无法按 game 抽样。")
            game_ids = ordered_unique(data["DayTrial"].map(game_id_from_daytrial).tolist())
            sorted_game_ids = sorted(game_ids, key=game_sort_key)
            selected_games = ordered_unique([sorted_game_ids[0], sorted_game_ids[-1]])
            mask = data["DayTrial"].map(game_id_from_daytrial).isin(selected_games)
            output_data = data.loc[mask].copy()
        else:
            selected_games = ["all"]
            output_data = data.copy()
        output_path = validation_input_dir / input_path.name
        write_pickle(output_data, output_path)
        summaries.append(
            {
                "filename": input_path.name,
                "source_rows": int(data.shape[0]),
                "validation_rows": int(output_data.shape[0]),
                "selected_games": selected_games,
            }
        )
    return validation_input_dir, summaries


def patch_legacy_source(source: str, args: argparse.Namespace) -> str:
    """生成用于验证的临时旧脚本源码。

    输入语义：source 是旧 FittingWeightHuman.py 原文，args 提供恢复全段落拟合和参数补丁。
    输出语义：返回只用于验证的临时旧源码。
    关键约束：只做 seed 外围可控、全段落拟合恢复和参数同步，不改变核心拟合公式。
    """

    patched = source
    patched = patched.replace(
        'adjacent_data = readAdjacentMap("../ConstantData/adjacent_map_fmri.csv")',
        f'adjacent_data = readAdjacentMap(r"{args.adjacent_map}")',
    )
    patched = patched.replace(
        "stay_length = 6",
        f"stay_length = {args.stay_length}\nSEGMENT_RANDOM_SEED = None\nSEGMENT_WORKERS = 1",
    )
    patched = patched.replace(
        "warnings.filterwarnings(\"ignore\")",
        "warnings.filterwarnings(\"ignore\")\n"
        "_ORIGINAL_SET_START_METHOD = multiprocessing.set_start_method\n"
        "def _lops_safe_set_start_method(method, force=False):\n"
        "    try:\n"
        "        _ORIGINAL_SET_START_METHOD(method, force=force)\n"
        "    except RuntimeError as exc:\n"
        "        if 'context has already been set' not in str(exc):\n"
        "            raise\n"
        "multiprocessing.set_start_method = _lops_safe_set_start_method",
    )
    patched = patched.replace(
        "def fitting_weight_ga_parallelize(idx, cutoff_pts, is_nan, df_monkey, suffix, agents):\n    prev = cutoff_pts[idx][0]",
        "def fitting_weight_ga_parallelize(idx, cutoff_pts, is_nan, df_monkey, suffix, agents):\n"
        "    if SEGMENT_RANDOM_SEED is not None:\n"
        "        np.random.seed(SEGMENT_RANDOM_SEED + idx)\n"
        "    prev = cutoff_pts[idx][0]",
    )
    old_results = """results = [fitting_weight_ga_parallelize(idxs[0], cutoff_pts=cutoff_pts, is_nan=is_nan, df_monkey=df_monkey,
                                             suffix=suffix, agents=agents)]"""
    new_results = """if SEGMENT_WORKERS > 1:
        with multiprocessing.Pool(processes=SEGMENT_WORKERS) as pool:
            results = pool.map(
                partial(fitting_weight_ga_parallelize, cutoff_pts=cutoff_pts, is_nan=is_nan, df_monkey=df_monkey,
                        suffix=suffix, agents=agents), idxs)
    else:
        results = [fitting_weight_ga_parallelize(idx, cutoff_pts=cutoff_pts, is_nan=is_nan, df_monkey=df_monkey,
                                                 suffix=suffix, agents=agents) for idx in idxs]"""
    if old_results not in patched:
        raise RuntimeError("无法定位旧脚本中的单段调试拟合语句，不能安全生成临时旧实现。")
    patched = patched.replace(old_results, new_results)
    patched = patched.replace(
        "size_pop=100, max_iter=500, prob_mut=0.01, lb=[0] * len(agents)",
        f"size_pop={args.ga_population_size}, max_iter={args.ga_iterations}, "
        f"prob_mut={args.ga_mutation_probability}, lb=[0] * len(agents)",
    )
    patched = patched.replace("precision=1e-3)", f"precision={args.ga_precision})")
    patched = patched.replace("weight, loss = ga.run(500)", f"weight, loss = ga.run({args.ga_iterations})")
    patched = patched.replace("0.1 * np.sum(np.abs(agent_weight))", f"{args.weight_penalty} * np.sum(np.abs(agent_weight))")
    patched = patched.replace("if cr_ <= 0.51:", f"if cr_ <= {args.vague_threshold}:")
    return patched


def write_temp_legacy_files(args: argparse.Namespace) -> tuple[Path, Path]:
    """写出临时旧脚本副本和 worker。

    输入语义：args 指向旧脚本路径和验证参数。
    输出语义：返回临时旧脚本路径和 worker 路径。
    关键约束：这些文件位于 src/LoPS/temp 下，验证结束必须删除。
    """

    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    source = args.legacy_script.read_text(encoding="utf-8")
    legacy_script_path = TEMP_ROOT / "FittingWeightHuman_all_segments.py"
    legacy_worker_path = TEMP_ROOT / "legacy_dynamic_strategy_worker.py"
    legacy_script_path.write_text(patch_legacy_source(source, args), encoding="utf-8")
    legacy_worker_path.write_text(LEGACY_WORKER_SOURCE, encoding="utf-8")
    return legacy_script_path, legacy_worker_path


def run_legacy_outputs(
    validation_input_dir: Path,
    legacy_output_dir: Path,
    run_dir: Path,
    args: argparse.Namespace,
    legacy_script_path: Path,
    legacy_worker_path: Path,
) -> list[dict[str, Any]]:
    """并行运行临时旧实现并生成 legacy 输出。

    输入语义：validation_input_dir 是新旧共同输入，legacy_output_dir 是旧输出目录。
    输出语义：返回每个子进程任务摘要。
    关键约束：每个文件独立子进程运行，避免旧脚本导入期 chdir 和全局变量互相影响。
    """

    legacy_output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    tasks: list[dict[str, Any]] = []
    for file_index, input_path in enumerate(sorted(validation_input_dir.glob("*.pkl"))):
        tasks.append(
            {
                "input_path": input_path,
                "seed": args.seed + file_index,
                "log_path": logs_dir / f"{input_path.stem}.legacy.log",
            }
        )

    pending = list(tasks)
    running: list[tuple[subprocess.Popen[bytes], Any, dict[str, Any]]] = []
    completed: list[dict[str, Any]] = []
    max_workers = max(1, min(args.workers, len(tasks)))
    while pending or running:
        while pending and len(running) < max_workers:
            task = pending.pop(0)
            log_file = task["log_path"].open("wb")
            command = [
                sys.executable,
                str(legacy_worker_path),
                "--legacy-script",
                str(legacy_script_path),
                "--legacy-root",
                str(args.legacy_root),
                "--legacy-cwd",
                str(args.legacy_cwd),
                "--input-path",
                str(task["input_path"]),
                "--output-dir",
                str(legacy_output_dir),
                "--seed",
                str(task["seed"]),
                "--segment-workers",
                str(args.segment_workers),
            ]
            process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            task["pid"] = process.pid
            task["started_at"] = time.time()
            running.append((process, log_file, task))

        next_running: list[tuple[subprocess.Popen[bytes], Any, dict[str, Any]]] = []
        for process, log_file, task in running:
            return_code = process.poll()
            if return_code is None:
                next_running.append((process, log_file, task))
                continue
            log_file.close()
            task["return_code"] = return_code
            task["elapsed_seconds"] = round(time.time() - task["started_at"], 3)
            completed.append(task)
            if return_code != 0:
                log_tail = Path(task["log_path"]).read_text(errors="replace")[-5000:]
                raise RuntimeError(f"旧实现任务失败：{task['input_path'].name}\n{log_tail}")
        running = next_running
        if running:
            time.sleep(1)

    return [
        {
            "input_file": task["input_path"].name,
            "seed": task["seed"],
            "pid": task["pid"],
            "return_code": task["return_code"],
            "elapsed_seconds": task["elapsed_seconds"],
            "log_path": str(task["log_path"]),
        }
        for task in completed
    ]


def run_current_outputs(
    validation_input_dir: Path,
    current_output_dir: Path,
    args: argparse.Namespace,
    config: DynamicStrategyFittingConfig,
) -> list[dict[str, Any]]:
    """运行当前新实现并生成输出。

    输入语义：validation_input_dir 与旧实现完全相同，current_output_dir 是新输出目录。
    输出语义：返回当前实现文件处理摘要。
    关键约束：配置中的 seed 与旧实现按同一 file_index 派生。
    """

    if current_output_dir.exists():
        shutil.rmtree(current_output_dir)
    return process_dynamic_strategy_directory(
        input_dir=validation_input_dir,
        output_dir=current_output_dir,
        adjacent_map_path=args.adjacent_map,
        config=config,
        workers=args.workers,
    )


def sha256_file(path: Path) -> str:
    """计算文件字节级 sha256。

    输入语义：path 指向输出 pickle。
    输出语义：返回十六进制 sha256。
    关键约束：hash 只作为额外诊断，硬判定以 DataFrame 逐值比较为准。
    """

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scalar_is_nan(value: Any) -> bool:
    """判断单个非容器值是否为 NaN。

    输入语义：value 可以是任意 DataFrame 单元格。
    输出语义：只有标量 NaN 返回 True。
    关键约束：列表和数组不能直接传给 pd.isna 后转换 bool。
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
    关键约束：数组使用精确相等；双方同位置 NaN 视为一致，不使用数值容差。
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
        return all(values_equal(left_value, right_value) for left_value, right_value in zip(left, right))
    return left == right


def first_dataframe_difference(left: pd.DataFrame, right: pd.DataFrame) -> dict[str, Any] | None:
    """返回两个 DataFrame 的第一个差异。

    输入语义：left 是旧输出，right 是新输出。
    输出语义：完全一致返回 None，否则返回第一个差异的位置和值。
    关键约束：列顺序、索引、dtype 和逐单元格值都要求完全一致。
    """

    if left.shape != right.shape:
        return {"type": "shape", "legacy_shape": list(left.shape), "current_shape": list(right.shape)}
    if list(left.columns) != list(right.columns):
        return {"type": "columns", "legacy_columns": list(left.columns), "current_columns": list(right.columns)}
    if not left.index.equals(right.index):
        return {"type": "index", "legacy_index_head": list(left.index[:10]), "current_index_head": list(right.index[:10])}
    legacy_dtypes = [str(dtype) for dtype in left.dtypes]
    current_dtypes = [str(dtype) for dtype in right.dtypes]
    if legacy_dtypes != current_dtypes:
        return {"type": "dtypes", "legacy_dtypes": legacy_dtypes, "current_dtypes": current_dtypes}

    for row_position in range(left.shape[0]):
        for column in left.columns:
            legacy_value = left.iloc[row_position][column]
            current_value = right.iloc[row_position][column]
            if not values_equal(legacy_value, current_value):
                return {
                    "type": "cell",
                    "row_position": int(row_position),
                    "index_label": repr(left.index[row_position]),
                    "column": str(column),
                    "legacy_value": repr(legacy_value),
                    "current_value": repr(current_value),
                }
    return None


def compare_output_directories(legacy_output_dir: Path, current_output_dir: Path) -> dict[str, Any]:
    """比较旧输出目录和新输出目录。

    输入语义：两个目录都包含动态拟合输出 pickle。
    输出语义：返回文件级比较报告和全局 all_equal。
    关键约束：文件集合、结构和逐值都必须完全一致。
    """

    legacy_files = sorted(path.name for path in legacy_output_dir.glob("*.pkl"))
    current_files = sorted(path.name for path in current_output_dir.glob("*.pkl"))
    reports: list[dict[str, Any]] = []
    for filename in sorted(set(legacy_files) | set(current_files)):
        legacy_path = legacy_output_dir / filename
        current_path = current_output_dir / filename
        if not legacy_path.exists() or not current_path.exists():
            reports.append(
                {
                    "filename": filename,
                    "equal": False,
                    "missing_legacy": not legacy_path.exists(),
                    "missing_current": not current_path.exists(),
                }
            )
            continue
        legacy_sha256 = sha256_file(legacy_path)
        current_sha256 = sha256_file(current_path)
        if legacy_sha256 == current_sha256:
            reports.append(
                {
                    "filename": filename,
                    "equal": True,
                    "legacy_sha256": legacy_sha256,
                    "current_sha256": current_sha256,
                    "sha256_equal": True,
                    "first_difference": None,
                }
            )
            continue
        legacy_data = read_pickle(legacy_path)
        current_data = read_pickle(current_path)
        first_difference = first_dataframe_difference(legacy_data, current_data)
        reports.append(
            {
                "filename": filename,
                "equal": first_difference is None,
                "shape": list(legacy_data.shape),
                "legacy_sha256": legacy_sha256,
                "current_sha256": current_sha256,
                "sha256_equal": False,
                "first_difference": first_difference,
            }
        )
    return {
        "legacy_file_count": len(legacy_files),
        "current_file_count": len(current_files),
        "all_equal": all(report.get("equal", False) for report in reports),
        "file_reports": reports,
    }


def main() -> None:
    """命令行入口：生成临时旧实现、运行新旧链路、比较输出并清理临时代码。"""

    args = parse_args()
    config = build_config(args)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.validation_dir / f"run_{timestamp}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    legacy_output_dir = run_dir / "legacy_output"
    current_output_dir = run_dir / "current_output"
    report_path = run_dir / "validation_report.json"

    legacy_script_path: Path | None = None
    try:
        input_paths = select_input_files(args.input_dir, args)
        validation_input_dir, input_summary = prepare_validation_inputs(input_paths, run_dir, args.game_selection)
        legacy_script_path, legacy_worker_path = write_temp_legacy_files(args)
        legacy_tasks = run_legacy_outputs(
            validation_input_dir,
            legacy_output_dir,
            run_dir,
            args,
            legacy_script_path,
            legacy_worker_path,
        )
        current_tasks = run_current_outputs(validation_input_dir, current_output_dir, args, config)
        comparison = compare_output_directories(legacy_output_dir, current_output_dir)
        report = {
            "target": "dynamicStrategyFitting_all_segments",
            "run_dir": str(run_dir),
            "input_dir": str(args.input_dir),
            "validation_input_dir": str(validation_input_dir),
            "adjacent_map": str(args.adjacent_map),
            "legacy_script": str(args.legacy_script),
            "game_selection": args.game_selection,
            "workers": args.workers,
            "config": asdict(config),
            "input_summary": input_summary,
            "legacy_tasks": legacy_tasks,
            "current_tasks": current_tasks,
            "comparison": comparison,
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(json.dumps({"report_path": str(report_path), "all_equal": comparison["all_equal"]}, ensure_ascii=False))
    finally:
        if TEMP_ROOT.exists():
            shutil.rmtree(TEMP_ROOT)


if __name__ == "__main__":
    main()

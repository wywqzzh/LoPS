#!/usr/bin/env python3
"""运行 fMRI hierarchical utility 预计算。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from LoPS.hierarchical_utility import (  # noqa: E402
    UtilityConfig,
    load_map_data_from_directory,
    process_utility_directory,
)


def parse_args() -> argparse.Namespace:
    """解析 fMRI hierarchical utility 运行参数。

    输入语义：命令行可覆盖输入、输出、常量目录、并行数和核心策略参数。
    输出语义：返回可直接构造 `UtilityConfig` 和批处理调用的参数对象。
    关键约束：默认路径只存在于脚本层，正式模块不内置任何数据目录。
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROJECT_ROOT / "data/hierarchical_utility/corrected_tile_data",
        help="corrected tile 输入目录。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data/hierarchical_utility/utility_data",
        help="追加 Q 列后的 utility 输出目录。",
    )
    parser.add_argument(
        "--constant-dir",
        type=Path,
        default=PROJECT_ROOT / "data/hierarchical_utility/constant_data",
        help="包含 adjacent_map_fmri.csv 和 dij_distance_map_fmri.csv 的常量目录。",
    )
    parser.add_argument("--workers", type=int, default=1, help="目录级并行进程数。")
    parser.add_argument(
        "--row-chunk-size",
        type=int,
        default=0,
        help="大于 0 时按行块并行处理，适合 workers 大于文件数的高核数环境。",
    )
    parser.add_argument("--randomness-coeff", type=float, default=0.0, help="Q 随机扰动系数。")
    parser.add_argument("--laziness-coeff", type=float, default=0.0, help="沿用上一方向的惰性系数。")
    parser.add_argument("--global-depth", type=int, default=15, help="Global 策略深度参数。")
    parser.add_argument("--global-ignore-depth", type=int, default=10, help="Global 远距离 bean 过滤深度。")
    parser.add_argument("--local-depth", type=int, default=10, help="Local 路径树深度。")
    parser.add_argument("--evade-depth", type=int, default=10, help="Evade 路径树深度。")
    parser.add_argument("--approach-depth", type=int, default=10, help="Approach 路径树深度。")
    parser.add_argument("--energizer-depth", type=int, default=10, help="Energizer 路径树深度。")
    parser.add_argument("--no-energizer-depth", type=int, default=8, help="NoEnergizer 路径树深度。")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> UtilityConfig:
    """根据命令行参数构造 utility 配置。

    输入语义：args 来自 `parse_args()`。
    输出语义：返回 `UtilityConfig`，未暴露的阈值沿用 fMRI 目标路径默认值。
    关键约束：默认随机和惰性系数均为 0，保证复现实验输出时没有随机影响。
    """

    return UtilityConfig(
        randomness_coeff=args.randomness_coeff,
        laziness_coeff=args.laziness_coeff,
        global_depth=args.global_depth,
        global_ignore_depth=args.global_ignore_depth,
        local_depth=args.local_depth,
        evade_depth=args.evade_depth,
        approach_depth=args.approach_depth,
        energizer_depth=args.energizer_depth,
        no_energizer_depth=args.no_energizer_depth,
    )


def main() -> None:
    """命令行入口：批量生成 fMRI hierarchical utility 数据。"""

    args = parse_args()
    map_data = load_map_data_from_directory(args.constant_dir)
    summaries = process_utility_directory(
        args.input_dir,
        args.output_dir,
        map_data,
        build_config(args),
        workers=args.workers,
        row_chunk_size=args.row_chunk_size if args.row_chunk_size > 0 else None,
    )
    print("fMRI hierarchical utility 预计算完成")
    print(f"输入目录：{args.input_dir.resolve()}")
    print(f"输出目录：{args.output_dir.resolve()}")
    print(f"处理文件数：{len(summaries)}")
    print(f"总行数：{sum(item['row_count'] for item in summaries)}")


if __name__ == "__main__":
    main()

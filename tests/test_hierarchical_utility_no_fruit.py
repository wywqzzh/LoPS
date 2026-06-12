"""hierarchical_utility 去除 fruit 字段后的等价性测试。"""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from LoPS.hierarchical_utility import (
    Q_COLUMNS,
    estimate_utility_for_dataframe,
    load_map_data_from_directory,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class HierarchicalUtilityNoFruitTest(unittest.TestCase):
    """验证当前 fMRI 数据不依赖 fruitPos/fruitType 字段。"""

    def test_utility_q_values_match_baseline_without_fruit_columns(self) -> None:
        """删除空 fruit 列后，单帧 utility Q 值应与既有基准输出完全一致。"""

        input_path = (
            PROJECT_ROOT
            / "data/hierarchical_utility/corrected_tile_data/031222-401-03-Dec-2022-1.pkl"
        )
        baseline_path = (
            PROJECT_ROOT
            / "data/hierarchical_utility/utility_data/031222-401-03-Dec-2022-1-with_Q.pkl"
        )
        constant_dir = PROJECT_ROOT / "data/hierarchical_utility/constant_data"

        # 真实数据中的 fruit 列全为空；这里显式删除这两列，验证新解析路径不再依赖它们。
        frame_data = pd.read_pickle(input_path).head(1).drop(columns=["fruitPos", "fruitType"])
        baseline = pd.read_pickle(baseline_path).head(1)
        map_data = load_map_data_from_directory(constant_dir)

        result = estimate_utility_for_dataframe(frame_data, map_data)

        for column in Q_COLUMNS:
            np.testing.assert_array_equal(result.at[0, column], baseline.at[0, column])


if __name__ == "__main__":
    unittest.main()

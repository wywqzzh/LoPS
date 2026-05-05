"""状态依赖图读取和条件状态索引转换。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StateDependencyGraph:
    """保存每个状态对应的条件状态下标列表。

    输入语义：由 load_state_dependency_graph() 从邻接矩阵中按行提取。
    输出语义：conditions_by_state[i] 表示第 i 个状态依赖的状态下标列表。
    关键约束：下标顺序来自矩阵列顺序，后续评分逻辑依赖该顺序展开条件变量。
    """

    # conditions_by_state[i] 表示状态图 G 的第 i 行中取值为 1 的依赖状态下标。
    conditions_by_state: list[list[int]]


def load_state_dependency_graph(path: Path) -> StateDependencyGraph:
    """读取 StateGraph pickle 并提取条件状态索引。

    输入语义：path 指向包含 G 字段的 pandas pickle，G 是状态依赖邻接矩阵。
    输出语义：返回 StateDependencyGraph，其中每行取值为 1 的列被转换为条件状态下标。
    关键约束：矩阵必须支持二维索引；只有精确等于 1 的位置会被视为依赖关系。
    """

    # StateGraph pickle 中的 G 是用于约束状态条件的邻接矩阵。
    result = pd.read_pickle(path)
    graph = result["G"]
    conditions = []
    for index in range(len(graph)):
        # 矩阵行中值为 1 的列才作为该状态的条件，其他权重或空值会被忽略。
        conditions.append(list(np.where(graph[index, :] == 1)[0]))
    return StateDependencyGraph(conditions_by_state=conditions)

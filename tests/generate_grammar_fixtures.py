"""generate_grammar 测试数据路径。

本模块集中定义测试使用的仓库内数据目录，避免测试文件重复拼接路径。
"""

from __future__ import annotations

from pathlib import Path


# 测试只读取 LoPS 仓库内已经迁移的数据，保证测试环境不依赖仓库外部路径。
DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "generate_grammar"
STRATEGY_SEQUENCE_DIR = DATA_ROOT / "input" / "strategy_sequence"
STATE_GRAPH_DIR = DATA_ROOT / "input" / "state_graph"
BASELINE_GRAMMAR_DIR = DATA_ROOT / "baseline" / "grammar"

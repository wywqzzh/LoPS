from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from LoPS.generate_grammar.config import (
    DEFAULT_STATE_NAMES,
    GenerateGrammarConfig,
)
from LoPS.generate_grammar.data_io import load_strategy_state_data
from LoPS.generate_grammar.pipeline import prepare_strategy_state_data, process_strategy_state_file
from LoPS.generate_grammar.state_graph import load_state_dependency_graph
from tests.generate_grammar_fixtures import STATE_GRAPH_DIR, STRATEGY_SEQUENCE_DIR


class GenerateGrammarPipelineTest(unittest.TestCase):
    # pipeline 测试覆盖文件级编排：删除 N、对齐状态、输出新版本结构化结果。
    def test_prepare_strategy_state_data_removes_n_and_aligns_state_features(self) -> None:
        # prepare 阶段必须保证 token_sequence 与 state_features 等长，否则后续状态条件会错位。
        record = load_strategy_state_data(
            STRATEGY_SEQUENCE_DIR / "031222-401.pkl",
            DEFAULT_STATE_NAMES,
        )
        state_dependencies = load_state_dependency_graph(STATE_GRAPH_DIR / "031222-401.pkl")

        prepared = prepare_strategy_state_data(record, state_dependencies)

        self.assertNotIn("N", prepared.token_sequence)
        self.assertEqual(len(prepared.token_sequence), len(prepared.state_features))
        self.assertTrue(len(prepared.n_positions) > 0)

    def test_process_strategy_state_file_returns_structured_output_only(self) -> None:
        # 单文件处理不写真实输出目录，使用临时目录配置只验证内存结果结构。
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GenerateGrammarConfig(
                strategy_sequence_dir=STRATEGY_SEQUENCE_DIR,
                state_graph_dir=STATE_GRAPH_DIR,
                output_dir=Path(temp_dir),
            )

            output = process_strategy_state_file("031222-401.pkl", config)

        # 核心 pipeline 不再返回 legacy 字段；旧格式转换只允许在验证脚本适配层完成。
        self.assertEqual(set(output.keys()), {"source", "parameters", "grammar", "parsed", "skip_gram"})
        structured = output
        self.assertEqual(set(structured.keys()), {"source", "parameters", "grammar", "parsed", "skip_gram"})
        self.assertIn("participant_file_names", structured["source"])
        self.assertIn("participant_ids", structured["source"])
        self.assertIn("original_sequence", structured["parsed"])
        self.assertTrue(structured["grammar"])


if __name__ == "__main__":
    unittest.main()

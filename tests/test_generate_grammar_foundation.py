from __future__ import annotations

import unittest

from LoPS.generate_grammar.config import (
    DEFAULT_STATE_NAMES,
    DEFAULT_STATE_GRAPH_DIR,
    DEFAULT_STRATEGY_SEQUENCE_DIR,
    GenerateGrammarConfig,
)
from LoPS.generate_grammar.data_io import load_strategy_state_data
from LoPS.generate_grammar.state_graph import load_state_dependency_graph
from LoPS.generate_grammar.token import (
    combine_tokens,
    format_token,
    split_token,
    token_length,
    tokens_share_base_token,
)


class GenerateGrammarFoundationTest(unittest.TestCase):
    def test_token_helpers(self) -> None:
        self.assertEqual(split_token("G"), ["G"])
        self.assertEqual(split_token("G-L-E-A"), ["G", "L", "E", "A"])
        self.assertEqual(format_token(["G", "L"]), "G-L")
        self.assertEqual(combine_tokens("G-L", "E-A"), "G-L-E-A")
        self.assertEqual(token_length("G-L-E-A"), 4)
        self.assertTrue(tokens_share_base_token("G-L", "L-E"))
        self.assertFalse(tokens_share_base_token("G-L", "E-A"))

    def test_default_config_validates_external_readonly_inputs(self) -> None:
        config = GenerateGrammarConfig()
        config.validate()
        self.assertTrue(config.output_dir.exists())

    def test_load_strategy_state_data(self) -> None:
        record = load_strategy_state_data(
            DEFAULT_STRATEGY_SEQUENCE_DIR / "031222-401.pkl",
            DEFAULT_STATE_NAMES,
        )
        self.assertEqual(record.input_file_name, "031222-401.pkl")
        self.assertIsInstance(record.token_sequence, list)
        self.assertIsInstance(record.initial_tokens, list)
        self.assertEqual(list(record.state_features.columns), list(DEFAULT_STATE_NAMES))
        self.assertTrue(record.participant_file_names[0].endswith(".pkl"))
        self.assertFalse(record.participant_ids[0].endswith(".pkl"))

    def test_load_state_dependency_graph(self) -> None:
        graph = load_state_dependency_graph(DEFAULT_STATE_GRAPH_DIR / "031222-401.pkl")
        self.assertTrue(graph.conditions_by_state)
        self.assertIsInstance(graph.conditions_by_state[0], list)


if __name__ == "__main__":
    unittest.main()

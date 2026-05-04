from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from LoPS.generate_grammar.config import (
    DEFAULT_STATE_GRAPH_DIR,
    DEFAULT_STATE_NAMES,
    DEFAULT_STRATEGY_SEQUENCE_DIR,
    GenerateGrammarConfig,
)
from LoPS.generate_grammar.data_io import load_strategy_state_data
from LoPS.generate_grammar.legacy import LEGACY_FIELD_ORDER
from LoPS.generate_grammar.pipeline import prepare_strategy_state_data, process_strategy_state_file
from LoPS.generate_grammar.state_graph import load_state_dependency_graph


class GenerateGrammarPipelineTest(unittest.TestCase):
    def test_prepare_strategy_state_data_removes_n_and_aligns_state_features(self) -> None:
        record = load_strategy_state_data(
            DEFAULT_STRATEGY_SEQUENCE_DIR / "031222-401.pkl",
            DEFAULT_STATE_NAMES,
        )
        state_dependencies = load_state_dependency_graph(DEFAULT_STATE_GRAPH_DIR / "031222-401.pkl")

        prepared = prepare_strategy_state_data(record, state_dependencies)

        self.assertNotIn("N", prepared.token_sequence)
        self.assertEqual(len(prepared.token_sequence), len(prepared.state_features))
        self.assertTrue(len(prepared.n_positions) > 0)

    def test_process_strategy_state_file_returns_legacy_and_structured_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GenerateGrammarConfig(output_dir=Path(temp_dir))

            output = process_strategy_state_file("031222-401.pkl", config)

        self.assertEqual(set(output.keys()), {"legacy", "structured"})
        legacy = output["legacy"]
        structured = output["structured"]
        for field in LEGACY_FIELD_ORDER:
            self.assertIn(field, legacy)
        self.assertEqual(list(legacy.keys()), list(LEGACY_FIELD_ORDER))
        self.assertTrue(legacy["fileNames"][0].endswith(".pkl"))
        self.assertEqual(set(structured.keys()), {"source", "parameters", "grammar", "parsed", "skip_gram"})
        self.assertIn("participant_file_names", structured["source"])
        self.assertIn("participant_ids", structured["source"])
        self.assertTrue(structured["grammar"])


if __name__ == "__main__":
    unittest.main()

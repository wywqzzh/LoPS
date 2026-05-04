from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from LoPS.generate_grammar.config import DEFAULT_BASELINE_GRAMMAR_DIR, GenerateGrammarConfig
from LoPS.generate_grammar.pipeline import process_strategy_state_file
from script.validate_generate_grammar import compare_legacy_dict, compare_values


class GenerateGrammarValidationTest(unittest.TestCase):
    def test_compare_values_accepts_equal_list_array_and_dataframe(self) -> None:
        old_value = [
            "sets",
            np.array([1, 2, 3]),
            pd.DataFrame({"state": [1, 2]}),
        ]
        new_value = [
            "sets",
            np.array([1, 2, 3]),
            pd.DataFrame({"state": [1, 2]}),
        ]

        self.assertEqual(compare_values(old_value, new_value, "root"), [])

    def test_compare_values_reports_path_for_different_values(self) -> None:
        differences = compare_values({"pro": [1.0]}, {"pro": [2.0]}, "031222-401.pkl")

        self.assertTrue(differences)
        self.assertIn("031222-401.pkl.pro[0]", differences[0])

    def test_compare_legacy_dict_reports_missing_key(self) -> None:
        differences = compare_legacy_dict({"sets": [], "pro": []}, {"sets": []}, "031222-401.pkl")

        self.assertEqual(differences, ["031222-401.pkl.pro: missing key"])

    def test_representative_output_contains_all_legacy_baseline_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GenerateGrammarConfig(output_dir=Path(temp_dir))
            output = process_strategy_state_file("031222-401.pkl", config)

        old_output = pd.read_pickle(DEFAULT_BASELINE_GRAMMAR_DIR / "031222-401.pkl")
        legacy = output["legacy"]
        for key in old_output.keys():
            self.assertIn(key, legacy)


if __name__ == "__main__":
    unittest.main()

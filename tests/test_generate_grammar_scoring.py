from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

LEGACY_ROOT = Path("/home/zzh/project/Pacman/2.Pac-man/structre-learning")
if str(LEGACY_ROOT) not in sys.path:
    sys.path.insert(0, str(LEGACY_ROOT))

from src.Utils import count as legacy_count  # noqa: E402
from src.bayesianScore import BDscore as legacy_bd_score  # noqa: E402
from src.bayesianScore import learnBayesNetBlock  # noqa: E402

from LoPS.generate_grammar.config import DEFAULT_STATE_GRAPH_DIR, DEFAULT_STATE_NAMES, DEFAULT_STRATEGY_SEQUENCE_DIR
from LoPS.generate_grammar.data_io import load_strategy_state_data
from LoPS.generate_grammar.scoring import bd_score, count_state_combinations, learn_state_condition_links
from LoPS.generate_grammar.state_graph import load_state_dependency_graph


def _build_real_condition_link_inputs() -> tuple[np.ndarray, np.ndarray, dict[int, list[int]], int, int, int, list[list[int]]]:
    record = load_strategy_state_data(
        DEFAULT_STRATEGY_SEQUENCE_DIR / "031222-401.pkl",
        DEFAULT_STATE_NAMES,
    )
    sequence = "".join(record.token_sequence)
    index_n = np.where(np.array(list(sequence)) == "N")[0]
    sequence = sequence.replace("N", "")

    state = record.state_features.reset_index(drop=True)
    state = state.drop(index_n).reset_index(drop=True)

    data_parent = {token: np.ones(len(sequence) - 1) for token in record.initial_tokens}
    data_policy_condition = {state_name: np.ones(len(sequence) - 1) for state_name in state.columns}

    for index in range(1, len(sequence)):
        data_parent[sequence[index - 1]][index - 1] = 2
        for state_name in state.columns:
            data_policy_condition[state_name][index - 1] = state[state_name].iloc[index - 1] + 1

    data_parent_frame = pd.DataFrame(data_parent, dtype=int)
    data_policy_condition_frame = pd.DataFrame(data_policy_condition, dtype=int)
    data = pd.concat([data_policy_condition_frame, data_parent_frame], axis=1).values.T
    data = np.array(data, dtype=int)
    nstates = np.max(data, axis=1).T.astype(int)
    casual_num = data_policy_condition_frame.shape[1]
    effect_num = data_parent_frame.shape[1]
    block_message = {index: [index] for index in range(casual_num)}
    graph = load_state_dependency_graph(DEFAULT_STATE_GRAPH_DIR / "031222-401.pkl")
    return data, nstates, block_message, casual_num, len(block_message), effect_num, graph.conditions_by_state


class GenerateGrammarScoringTest(unittest.TestCase):
    def test_count_state_combinations_matches_legacy_count(self) -> None:
        data = np.array(
            [
                [1, 2, 1, 2, 2, 1],
                [1, 1, 2, 2, 1, 2],
            ],
            dtype=int,
        )
        nstates = np.array([2, 2], dtype=int)

        expected = legacy_count(data, nstates)
        actual = count_state_combinations(data, nstates)

        np.testing.assert_array_equal(actual, expected)

    def test_bd_score_matches_legacy_bd_score(self) -> None:
        data_v = np.array([1, 2, 1, 2, 2, 1], dtype=int)
        data_parents = np.array(
            [
                [1, 1, 2, 2, 1, 2],
                [2, 1, 2, 1, 1, 2],
            ],
            dtype=int,
        )
        nstates_v = 2
        nstates_parents = np.array([2, 2], dtype=int)
        alpha = 0.5 / (np.prod(nstates_v) * np.prod(nstates_parents))

        expected_score, expected_posterior = legacy_bd_score(
            data_v,
            data_parents,
            nstates_v,
            nstates_parents,
            alpha,
        )
        actual_score, actual_posterior = bd_score(data_v, data_parents, nstates_v, nstates_parents, alpha)

        self.assertEqual(actual_score, expected_score)
        np.testing.assert_array_equal(actual_posterior, expected_posterior)

    def test_learn_state_condition_links_matches_legacy_learn_bayes_net_block(self) -> None:
        data, nstates, block_message, casual_num, block_num, effect_num, conditions = _build_real_condition_link_inputs()

        expected_adjacency, _, _, _ = learnBayesNetBlock(
            data=data,
            nstates=nstates,
            blockMessage=block_message,
            casualNum=casual_num,
            blockNum=block_num,
            effectNum=effect_num,
            alpha=0.5,
            conditions=conditions,
        )
        actual_adjacency, _, _, _ = learn_state_condition_links(
            data=data,
            nstates=nstates,
            block_message=block_message,
            casual_num=casual_num,
            block_num=block_num,
            effect_num=effect_num,
            alpha=0.5,
            conditions=conditions,
        )

        np.testing.assert_array_equal(actual_adjacency, expected_adjacency)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from LoPS.generate_grammar.config import GrammarLearningParams
from LoPS.generate_grammar.grammar import GrammarLearningResult, SkipGramResult
from LoPS.generate_grammar.token import split_token


def build_structured_output(
    input_file_name: str,
    params: GrammarLearningParams,
    result: GrammarLearningResult,
    skip_gram: SkipGramResult,
) -> dict[str, Any]:
    grammar_items = []
    for index, token in enumerate(result.grammar_tokens):
        grammar_items.append(
            {
                "token": token,
                "base_tokens": split_token(token),
                "probability": result.probabilities[index],
                "frequency": result.frequencies[index],
                "time_probability": result.time_probabilities[index],
                "components": result.components[index],
            }
        )

    return {
        "source": {
            "input_file_name": input_file_name,
            "participant_file_names": result.participant_file_names,
            "participant_ids": result.participant_ids,
        },
        "parameters": asdict(params),
        "grammar": grammar_items,
        "parsed": {
            "sequence": result.parsed_sequence,
            "state_features": result.parsed_state_features,
            "position_grammar": result.position_grammar,
        },
        "skip_gram": {
            "target": params.skip_gram_target,
            "found": skip_gram.found,
            "count": skip_gram.count,
        },
    }

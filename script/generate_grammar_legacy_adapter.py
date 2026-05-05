from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from LoPS.generate_grammar.token import token_length


LEGACY_FIELD_ORDER = (
    # 旧 pickle 字段顺序固定在适配层中，避免正式新模块为了验证需求携带旧格式知识。
    "sets",
    "pro",
    "gram",
    "sequence",
    "time_pro",
    "frequency",
    "seq",
    "state",
    "S",
    "fileNames",
    "components",
    "skipGram",
    "skipGramNum",
)


def _legacy_places() -> list[str]:
    # 旧实现为复合 grammar 分配 ASCII 占位符；该规则只用于验证适配，不进入核心学习流程。
    place_set = [chr(index) for index in range(32, 126)]
    for token in ("e", "G", "L", "E", "A", "1", "2", "3", "4", "S", "V", "N"):
        place_set.remove(token)
    return place_set


def _legacy_token(token: str) -> str:
    # 新结构使用 "G-L" 这类清晰 token；旧格式比较时需要还原为无分隔符的 "GL"。
    return token.replace("-", "")


def _legacy_symbol_by_token(tokens: list[str]) -> dict[str, str]:
    # 基础 token 在旧格式中仍使用自身，复合 token 才按旧占位符序列映射。
    places = _legacy_places()
    symbol_by_token: dict[str, str] = {}
    place_index = 0
    for token in tokens:
        if token_length(token) == 1:
            symbol_by_token[token] = token
        else:
            symbol_by_token[token] = places[place_index]
            place_index += 1
    return symbol_by_token


def convert_generate_grammar_output_to_legacy(output: Mapping[str, Any]) -> dict[str, Any]:
    # 统一的新旧格式转换接口：输入必须是新版本 pipeline 直接输出的结构化字典。
    # 该函数是验证适配层，负责把新结构映射到旧 pickle 字段，供 validate 脚本逐值比较。
    grammar_items = list(output["grammar"])
    parsed = output["parsed"]
    source = output["source"]
    skip_gram = output["skip_gram"]

    grammar_tokens = [item["token"] for item in grammar_items]
    symbol_by_token = _legacy_symbol_by_token(grammar_tokens)

    legacy_output: dict[str, Any] = {}
    # 以下字段按旧 pickle 顺序写入，便于人工检查，也避免 pandas pickle 比较时出现顺序歧义。
    legacy_output["sets"] = [_legacy_token(token) for token in grammar_tokens]
    legacy_output["pro"] = [item["probability"] for item in grammar_items]
    legacy_output["gram"] = [_legacy_token(token) for token in parsed["position_grammar"]]
    legacy_output["sequence"] = "".join(parsed["original_sequence"])
    # time_pro 在旧格式中是 ndarray；从新结构 grammar 项按顺序恢复为相同数组形态。
    legacy_output["time_pro"] = np.array([item["time_probability"] for item in grammar_items])
    legacy_output["frequency"] = [item["frequency"] for item in grammar_items]
    legacy_output["seq"] = "".join(symbol_by_token[token] for token in parsed["sequence"])
    legacy_output["state"] = parsed["state_features"]
    legacy_output["S"] = [symbol_by_token[token] for token in grammar_tokens]
    legacy_output["fileNames"] = source["participant_file_names"]
    legacy_output["components"] = [
        [_legacy_token(item["components"][0]), _legacy_token(item["components"][1])]
        for item in grammar_items
    ]
    legacy_output["skipGram"] = skip_gram["found"]
    legacy_output["skipGramNum"] = skip_gram["count"]
    return legacy_output

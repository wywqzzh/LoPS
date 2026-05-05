"""generate_grammar 验证格式适配器。

本模块只服务一致性验证，把新版本结构化输出映射为基准文件使用的字段集合。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from LoPS.generate_grammar.token import token_length


LEGACY_FIELD_ORDER = (
    # 基准 pickle 字段顺序固定在适配层中，便于验证脚本按稳定顺序检查输出。
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
    """生成验证格式中可用于表示复合 grammar 的 ASCII 占位符。

    返回值是删除基础 token 后的单字符列表；该列表只服务于验证格式转换，
    不参与正式 grammar 学习流程，也不承载业务语义。
    """
    # 验证格式使用单字符占位符表示复合 token，因此先构造可打印 ASCII 范围。
    place_set = [chr(index) for index in range(32, 126)]
    # 基础 token 必须保留原字符，不能被分配为复合 token 占位符。
    for token in ("e", "G", "L", "E", "A", "1", "2", "3", "4", "S", "V", "N"):
        place_set.remove(token)
    return place_set


def _legacy_token(token: str) -> str:
    """把内部 token 表示转换为验证格式中的连续字符串。

    参数 token 使用正式模块中的连字符分隔表示，例如 ``G-L``；返回值去除
    连字符，用于写入基准字段中的 grammar 文本。
    """
    # 验证字段中的复合 token 不携带分隔符，转换时只改变展示形式。
    return token.replace("-", "")


def _legacy_symbol_by_token(tokens: list[str]) -> dict[str, str]:
    """为 grammar token 构造验证格式的序列符号映射。

    输入 tokens 按 grammar 顺序排列；返回字典把基础 token 映射到自身，
    把复合 token 映射到稳定的单字符占位符。调用方必须保证复合 token
    数量不超过可用占位符数量。
    """
    places = _legacy_places()
    symbol_by_token: dict[str, str] = {}
    place_index = 0
    for token in tokens:
        # 基础 token 保持可读的原始符号；复合 token 使用顺序占位符压缩为单字符。
        if token_length(token) == 1:
            symbol_by_token[token] = token
        else:
            symbol_by_token[token] = places[place_index]
            place_index += 1
    return symbol_by_token


def _legacy_position_grammar(parsed_sequence: list[str], grammar_tokens: list[str]) -> list[str]:
    """从新结构解析序列重建验证格式需要的旧 gram 序列。

    输入语义：parsed_sequence 是正式输出中的最终解析 token 序列；grammar_tokens 是 grammar 顺序。
    输出语义：返回旧字段 `gram` 所需的 token 序列，重复次数沿用旧 parse_pro 的最后一个 grammar token 长度。
    关键约束：该重建逻辑只存在于验证适配器，不能反向污染正式结构化输出。
    """

    # 旧 gram 字段不是正式输出语义；它按最后一个 grammar token 的基础长度固定重复每个解析 token。
    if len(grammar_tokens) == 0:
        return []
    repeat_count = token_length(grammar_tokens[-1])
    position_grammar = []
    for token in parsed_sequence:
        position_grammar.extend([token] * repeat_count)
    return position_grammar


def convert_generate_grammar_output_to_legacy(output: Mapping[str, Any]) -> dict[str, Any]:
    """把 generate_grammar 结构化输出转换为基准 pickle 字段。

    参数 output 必须是 pipeline 直接产出的结构化字典，包含 ``grammar``、
    ``parsed``、``source`` 和 ``skip_gram`` 等分区。返回值按
    ``LEGACY_FIELD_ORDER`` 写入验证字段，供 validate 脚本做逐值一致性检查。
    """
    grammar_items = list(output["grammar"])
    parsed = output["parsed"]
    source = output["source"]
    skip_gram = output["skip_gram"]

    grammar_tokens = [item["token"] for item in grammar_items]
    symbol_by_token = _legacy_symbol_by_token(grammar_tokens)

    legacy_output: dict[str, Any] = {}
    # 以下字段按基准 pickle 顺序写入，便于人工检查，也避免 pandas pickle 比较时出现顺序歧义。
    legacy_output["sets"] = [_legacy_token(token) for token in grammar_tokens]
    legacy_output["pro"] = [item["probability"] for item in grammar_items]
    legacy_output["gram"] = [_legacy_token(token) for token in _legacy_position_grammar(parsed["sequence"], grammar_tokens)]
    legacy_output["sequence"] = "".join(parsed["original_sequence"])
    # time_pro 是按 grammar 顺序排列的概率数组，转换时保持 ndarray 形态用于精确比较。
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

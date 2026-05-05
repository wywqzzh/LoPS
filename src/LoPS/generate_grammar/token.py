"""grammar token 的拆分、格式化、组合和基础动作检查工具。"""

from __future__ import annotations

from collections.abc import Sequence


TOKEN_SEPARATOR = "-"


def split_token(token: str) -> list[str]:
    """把 token 字符串拆成基础动作列表。

    输入语义：token 是基础动作或使用 TOKEN_SEPARATOR 连接的复合动作。
    输出语义：返回基础动作列表；空字符串返回空列表。
    关键约束：函数只按分隔符拆分，不校验基础动作名称是否合法。
    """

    # 复合 grammar 统一写成 "G-L-E-A" 形式，空字符串表示没有第二个组成项。
    if token == "":
        return []
    return token.split(TOKEN_SEPARATOR)


def format_token(base_tokens: Sequence[str]) -> str:
    """把基础动作序列格式化为统一 token 字符串。

    输入语义：base_tokens 是按顺序排列的基础动作名称。
    输出语义：返回使用 TOKEN_SEPARATOR 拼接后的 token。
    关键约束：空序列会生成空字符串，调用方需要根据业务语义处理该边界。
    """

    # 所有复合 token 都通过同一个分隔符生成，避免算法依赖字符串字符位置。
    return TOKEN_SEPARATOR.join(base_tokens)


def combine_tokens(parent_token: str, child_token: str) -> str:
    """按基础动作顺序组合 parent token 和 child token。

    输入语义：parent_token 与 child_token 均为可由 split_token() 解析的 token 字符串。
    输出语义：返回两者基础动作列表拼接后的复合 token。
    关键约束：不会去重或检查重叠，是否允许组合由调用方的候选筛选逻辑决定。
    """

    # 组合前先拆成基础动作列表，再统一格式化，保证单 token 和复合 token 处理一致。
    return format_token(split_token(parent_token) + split_token(child_token))


def token_length(token: str) -> int:
    """计算 token 包含的基础动作数量。

    输入语义：token 是基础动作或复合动作字符串。
    输出语义：返回基础动作数量，例如 "E-A" 的长度是 2。
    关键约束：长度基于 split_token() 的拆分结果，不等同于字符串字符数。
    """

    # token 长度是基础动作数量，不是字符串长度；例如 "E-A" 的长度是 2。
    return len(split_token(token))


def tokens_share_base_token(left: str, right: str) -> bool:
    """判断两个 token 是否包含相同基础动作。

    输入语义：left 和 right 是两个待比较的 token 字符串。
    输出语义：任一基础动作重叠时返回 True，否则返回 False。
    关键约束：比较基于集合交集，重复基础动作不会改变返回结果。
    """

    # 共享基础动作的 token 组合会形成自重叠 chunk，候选筛选阶段需要识别该情况。
    return bool(set(split_token(left)) & set(split_token(right)))

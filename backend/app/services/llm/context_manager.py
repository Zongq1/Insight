"""上下文管理器

Token 估算、文本截断、上下文预算管理。
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 粗略的 token 估算比率（中文约 1.5 token/字，英文约 0.75 token/word）
CHARS_PER_TOKEN_ZH = 1.5
CHARS_PER_TOKEN_EN = 0.75
DEFAULT_MAX_INPUT_TOKENS = 12000
DEFAULT_MAX_TOTAL_TOKENS = 16000


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量

    使用混合比率估算：中文字符用中文比率，其他用英文比率。

    Args:
        text: 输入文本

    Returns:
        估算的 token 数
    """
    if not text:
        return 0

    zh_chars = sum(1 for c in text if '一' <= c <= '鿿')
    other_chars = len(text) - zh_chars

    tokens = int(zh_chars * CHARS_PER_TOKEN_ZH + other_chars * CHARS_PER_TOKEN_EN)
    return max(tokens, 1)


def truncate_to_budget(
    texts: list[str],
    max_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
    strategy: str = "tail_cut",
) -> list[str]:
    """按 token 预算截断文本列表

    Args:
        texts: 文本列表
        max_tokens: 最大 token 数
        strategy: 截断策略
            - "tail_cut": 从末尾截断每个文本
            - "drop_later": 从后往前丢弃整个文本
            - "proportional": 按比例截断每个文本

    Returns:
        截断后的文本列表
    """
    if not texts:
        return texts

    total_tokens = sum(estimate_tokens(t) for t in texts)

    if total_tokens <= max_tokens:
        return texts

    logger.info(
        f"Context truncation: {total_tokens} tokens > {max_tokens} budget, "
        f"strategy={strategy}"
    )

    if strategy == "drop_later":
        return _drop_later(texts, max_tokens)
    elif strategy == "proportional":
        return _proportional_cut(texts, max_tokens)
    else:  # tail_cut
        return _tail_cut(texts, max_tokens)


def _tail_cut(texts: list[str], max_tokens: int) -> list[str]:
    """从末尾截断每个文本"""
    result = []
    remaining = max_tokens

    for text in texts:
        tokens = estimate_tokens(text)
        if tokens <= remaining:
            result.append(text)
            remaining -= tokens
        else:
            # 按比例截断
            ratio = remaining / tokens if tokens > 0 else 0
            cut_len = int(len(text) * ratio)
            if cut_len > 100:
                result.append(text[:cut_len] + "\n\n[文本已截断]")
            remaining = 0
            break

    return result


def _drop_later(texts: list[str], max_tokens: int) -> list[str]:
    """从后往前丢弃整个文本"""
    result = []
    remaining = max_tokens

    for text in texts:
        tokens = estimate_tokens(text)
        if tokens <= remaining:
            result.append(text)
            remaining -= tokens
        else:
            break

    return result


def _proportional_cut(texts: list[str], max_tokens: int) -> list[str]:
    """按比例截断每个文本"""
    total_tokens = sum(estimate_tokens(t) for t in texts)
    if total_tokens == 0:
        return texts

    ratio = max_tokens / total_tokens
    result = []

    for text in texts:
        cut_len = int(len(text) * ratio)
        if cut_len >= len(text):
            result.append(text)
        elif cut_len > 100:
            result.append(text[:cut_len] + "\n\n[文本已截断]")
        else:
            result.append("")  # 太短则丢弃

    return [t for t in result if t]


def build_context(
    raw_texts: list[str],
    max_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
    separator: str = "\n\n---\n\n",
) -> str:
    """构建上下文字符串

    将多个文本拼接成一个上下文字符串，确保不超过 token 限制。

    Args:
        raw_texts: 原始文本列表
        max_tokens: 最大 token 数
        separator: 文本分隔符

    Returns:
        拼接后的上下文字符串
    """
    if not raw_texts:
        return ""

    # 先截断
    truncated = truncate_to_budget(raw_texts, max_tokens)

    # 拼接
    context = separator.join(truncated)

    # 最终检查
    final_tokens = estimate_tokens(context)
    if final_tokens > max_tokens:
        logger.warning(f"Context still over budget after truncation: {final_tokens} tokens")
        # 强制截断
        ratio = max_tokens / final_tokens
        cut_len = int(len(context) * ratio)
        context = context[:cut_len] + "\n\n[上下文已截断]"

    logger.info(f"Built context: {len(truncated)} texts, ~{estimate_tokens(context)} tokens")
    return context

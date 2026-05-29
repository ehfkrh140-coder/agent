from __future__ import annotations

from typing import Iterable

from src.schemas.agent_response import AgentResponse

UNSAFE_TRADE_TERMS = [
    "매수",
    "매도",
    "전송",
    "출금",
    "이체",
    "주문",
    "자동매매",
    "실행",
    "즉시 실행",
    "전량",
    "수익 확정",
    "확정 수익",
    "선물",
    "헤지",
    "hedge",
    "hedging",
    "buy",
    "sell",
    "transfer",
    "execute",
    "execution",
    "API integration",
]

UNVERIFIED_MARKET_ASSUMPTION_TERMS = [
    "수수료 0",
    "유동성 풍부",
    "대량 거래 가능",
    "실질 수익 가능성이 높음",
    "확실한 수익",
    "guaranteed",
    "immediate profit",
]

MISSING_MARKET_DATA_TERMS = ["없", "아직", "정보는 아직", "정보가 없", "정보 부족", "미제공", "제공되지"]
MARKET_DATA_FIELDS = ["수수료", "호가", "호가 깊이", "체결량", "타임스탬프", "유동성"]


def _iter_response_text(response: AgentResponse) -> Iterable[str]:
    yield response.summary or ""
    yield from (response.key_points or [])
    yield from (response.concerns or [])
    yield from (response.questions or [])
    yield from (response.suggested_next_steps or [])


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = (text or "").lower()
    return any(term.lower() in lowered for term in terms)


def _input_mentions_missing_market_data(user_input: str) -> bool:
    text = user_input or ""
    return any(field in text for field in MARKET_DATA_FIELDS) and any(term in text for term in MISSING_MARKET_DATA_TERMS)


def validate_agent_response_safety(response: AgentResponse, user_input: str) -> list[str]:
    warnings: list[str] = []
    response_text = "\n".join(_iter_response_text(response))

    if _contains_any(response_text, UNSAFE_TRADE_TERMS):
        warnings.append("unsafe_trade_suggestion")

    missing_market_data = _input_mentions_missing_market_data(user_input)
    if missing_market_data and (
        _contains_any(response_text, UNVERIFIED_MARKET_ASSUMPTION_TERMS)
        or response.confidence >= 0.8
    ):
        warnings.append("unverified_market_assumption")

    return warnings


def add_warnings_to_concerns(response: AgentResponse, warnings: Iterable[str]) -> AgentResponse:
    concerns = list(response.concerns or [])
    for warning in warnings:
        if warning not in concerns:
            concerns.append(warning)
    response.concerns = concerns
    return response

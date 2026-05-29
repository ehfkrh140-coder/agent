from __future__ import annotations

import re
from typing import Iterable

from src.schemas.agent_response import AgentResponse

UNSAFE_TRADE_PATTERNS = [
    r"거래소\s*\S+\s*에서\s*매수.*(?:전송|이체).*(?:매도)",
    r"매수\s*후.*(?:전송|이체)?.*매도",
    r"즉시\s*(?:매수|매도|주문|실행)",
    r"전량\s*매도",
    r"주문\s*실행",
    r"실제\s*실행",
    r"자동매매\s*실행",
    r"(?:선물|헤지)\s*포지션\s*진입",
    r"execute\s+the\s+trade",
    r"buy\s+on\s+.+\s+and\s+sell\s+on",
    r"transfer\s+.+\s+then\s+sell",
    r"api\s+integration",
]

SUGGESTED_STEP_UNSAFE_PATTERNS = [
    *UNSAFE_TRADE_PATTERNS,
    r"(?:매수|매도|주문|전송|이체|출금)\s*(?:하세요|한다|합니다|수행|진입)",
    r"(?:buy|sell|transfer|execute)\s+(?:now|immediately)",
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


def _iter_context_text(response: AgentResponse) -> Iterable[str]:
    yield response.summary or ""
    yield from (response.key_points or [])
    yield from (response.concerns or [])
    yield from (response.questions or [])


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = (text or "").lower()
    return any(term.lower() in lowered for term in terms)


def _matches_any_pattern(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text or "", flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def _input_mentions_missing_market_data(user_input: str) -> bool:
    text = user_input or ""
    return any(field in text for field in MARKET_DATA_FIELDS) and any(term in text for term in MISSING_MARKET_DATA_TERMS)


def _has_unsafe_trade_suggestion(response: AgentResponse) -> bool:
    context_text = "\n".join(_iter_context_text(response))
    if _matches_any_pattern(context_text, UNSAFE_TRADE_PATTERNS):
        return True

    for step in response.suggested_next_steps or []:
        if _matches_any_pattern(step, SUGGESTED_STEP_UNSAFE_PATTERNS):
            return True
    return False


def validate_agent_response_safety(response: AgentResponse, user_input: str) -> list[str]:
    warnings: list[str] = []
    response_text = "\n".join([
        response.summary or "",
        *(response.key_points or []),
        *(response.concerns or []),
        *(response.questions or []),
        *(response.suggested_next_steps or []),
    ])

    if _has_unsafe_trade_suggestion(response):
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

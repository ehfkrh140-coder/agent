from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from src.market_data.adapters.base import MarketDataAdapterError


@dataclass(frozen=True)
class HttpJsonResponse:
    data: dict[str, Any]
    elapsed_ms: int
    url: str


class ReadOnlyHttpClient:
    """Small stdlib-only JSON HTTP client for public read-only GET endpoints."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 10,
        max_retries: int = 2,
        user_agent: str = "agent-council-market-data-v1",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = user_agent

    def get_json(self, base_url: str, path: str, params: dict[str, Any] | None = None) -> HttpJsonResponse:
        if not path.startswith("/"):
            raise MarketDataAdapterError("HTTP path must be absolute and read-only")
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
        url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        if query:
            url = f"{url}?{query}"
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        request = urllib.request.Request(url, headers=headers, method="GET")
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    status = getattr(response, "status", response.getcode())
                    body = response.read().decode("utf-8", errors="replace")
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                if status < 200 or status >= 300:
                    raise MarketDataAdapterError(f"HTTP status {status} for {url}")
                try:
                    data = json.loads(body)
                except json.JSONDecodeError as exc:
                    raise MarketDataAdapterError(f"Invalid JSON response from {url}") from exc
                if not isinstance(data, dict):
                    raise MarketDataAdapterError(f"JSON response root is not an object from {url}")
                return HttpJsonResponse(data=data, elapsed_ms=elapsed_ms, url=url)
            except urllib.error.HTTPError as exc:
                last_error = MarketDataAdapterError(f"HTTP status {exc.code} for {url}")
            except urllib.error.URLError as exc:
                last_error = MarketDataAdapterError(f"Network error for {url}: {exc.reason}")
            except TimeoutError as exc:
                last_error = MarketDataAdapterError(f"Timeout fetching {url}")
            except MarketDataAdapterError as exc:
                last_error = exc
            if attempt < self.max_retries:
                continue
        if last_error is None:
            raise MarketDataAdapterError(f"Unknown HTTP error for {url}")
        raise MarketDataAdapterError(str(last_error)) from last_error

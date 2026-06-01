from __future__ import annotations

import urllib.error
import unittest
from unittest.mock import patch

from src.market_data.adapters.base import MarketDataAdapterError
from src.market_data.http_client import ReadOnlyHttpClient


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.body

    def getcode(self):
        return self.status


class ReadOnlyHttpClientTests(unittest.TestCase):
    def test_get_json_uses_get_without_auth_headers(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["method"] = request.get_method()
            captured["headers"] = dict(request.header_items())
            captured["url"] = request.full_url
            return FakeResponse(b'{"retCode":0,"result":{}}')

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            response = ReadOnlyHttpClient(timeout_seconds=1, max_retries=0).get_json(
                "https://api.bybit.com",
                "/v5/market/tickers",
                {"category": "linear", "symbol": "BTCUSDT"},
            )
        self.assertEqual(response.data["retCode"], 0)
        self.assertEqual(captured["method"], "GET")
        self.assertIn("category=linear", captured["url"])
        header_keys = {key.lower() for key in captured["headers"]}
        self.assertNotIn("authorization", header_keys)
        self.assertNotIn("x-bapi-api-key", header_keys)
        self.assertNotIn("x-bapi-sign", header_keys)

    def test_invalid_json_raises_adapter_error(self):
        with patch("urllib.request.urlopen", return_value=FakeResponse(b'not json')):
            with self.assertRaises(MarketDataAdapterError):
                ReadOnlyHttpClient(max_retries=0).get_json("https://api.bybit.com", "/v5/market/tickers", {})

    def test_network_error_is_wrapped(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
            with self.assertRaises(MarketDataAdapterError):
                ReadOnlyHttpClient(max_retries=0).get_json("https://api.bybit.com", "/v5/market/tickers", {})


if __name__ == "__main__":
    unittest.main()

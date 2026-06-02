from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml

SCHEMA_VERSION = "usdt_krw_public_probe_v0"
REPORT_SCHEMA_VERSION = "usdt_krw_public_probe_report_v0"
NEXT_RECOMMENDED_STEP = "review_probe_results_before_experimental_scaffolding"
FX_HARDENING_NEXT_STEP = "review_harden_fx_source_candidates"
FX_READY_NEXT_STEP = "review_fx_probe_results_before_experimental_scaffolding"
ALLOWED_ROLES = {"domestic_usdt_krw", "global_usdt_reference", "fx_reference"}
PUBLIC_HEADERS = {
    "User-Agent": "agent-council-usdt-krw-public-probe-v0",
    "Accept": "application/json",
}
PRIVATE_HEADER_FRAGMENTS = ("authorization", "api-key", "apikey", "secret", "token", "x-api")


@dataclass(frozen=True)
class ProbeHttpResponse:
    data: Any
    http_status: int | None
    latency_ms: int | None
    url: str


HttpGetJson = Callable[..., ProbeHttpResponse]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_probe_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("Probe config must be a mapping")
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Probe config must contain a sources list")
    _assert_config_has_no_credentials(data)
    return data


def run_probe_report(
    *,
    config_path: str | Path = "configs/usdt_krw_probe_sources.yaml",
    include_disabled: bool = False,
    timeout_seconds: float = 10.0,
    max_retries: int = 1,
    http_get_json: HttpGetJson | None = None,
    now_fn: Callable[[], str] | None = None,
) -> dict[str, Any]:
    config = load_probe_config(config_path)
    created_at = (now_fn or utc_now_iso)()
    getter = http_get_json or default_http_get_json
    results: list[dict[str, Any]] = []
    for source in config.get("sources", []):
        if not isinstance(source, dict):
            continue
        if not include_disabled and not bool(source.get("enabled_for_probe", False)):
            continue
        results.append(
            probe_source(
                source,
                http_get_json=getter,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                created_at_utc=created_at,
            )
        )
    summary = summarize_results(results)
    next_step = FX_READY_NEXT_STEP if not summary.get("fx_unresolved", True) else FX_HARDENING_NEXT_STEP
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "created_at_utc": created_at,
        "results": results,
        "summary": summary,
        "next_recommended_step": next_step,
    }


def probe_source(
    source: dict[str, Any],
    *,
    http_get_json: HttpGetJson | None = None,
    timeout_seconds: float = 10.0,
    max_retries: int = 1,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    created_at = created_at_utc or utc_now_iso()
    source_id = str(source.get("source_id") or "unknown")
    role = str(source.get("role") or "unknown")
    notes = [str(note) for note in source.get("notes", []) if note is not None]
    result = empty_probe_result(source_id=source_id, role=role, created_at_utc=created_at, notes=notes)
    result["requires_api_key"] = _coerce_optional_bool(source.get("requires_api_key"))

    if role not in ALLOWED_ROLES:
        result.update(status="unknown", error=f"Unsupported role: {role}")
        result["notes"].append("Unsupported role; no probe attempted.")
        return result
    if not bool(source.get("no_private_api", False)):
        result.update(status="skipped", error="Source is not explicitly marked no_private_api=true")
        result["notes"].append("Skipped because the source is not explicitly public/no-private.")
        return result
    if role == "fx_reference" and result["requires_api_key"] is True:
        result.update(status="skipped", pair_availability="unknown")
        result["notes"].append("Skipped because this FX source is marked requires_api_key=true.")
        return result
    if not bool(source.get("safe_public_probe", False)):
        result.update(status="skipped", pair_availability="unknown")
        result["notes"].append("Skipped because no safe public endpoint candidate is configured.")
        return result

    endpoints = source.get("endpoints") if isinstance(source.get("endpoints"), dict) else {}
    if not endpoints:
        result.update(status="skipped", pair_availability="unknown")
        result["notes"].append("Skipped because endpoint candidates are empty.")
        return result

    getter = http_get_json or default_http_get_json
    pair_candidates = [str(candidate) for candidate in source.get("pair_candidates", [])]
    responses: list[tuple[str, ProbeHttpResponse]] = []
    errors: list[str] = []
    for endpoint_name in ("market_list", "ticker", "orderbook"):
        endpoint = endpoints.get(endpoint_name)
        if not isinstance(endpoint, dict):
            continue
        url = build_url(str(source.get("base_url") or ""), endpoint)
        if not url:
            continue
        response = _request_with_retries(
            getter,
            url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        if isinstance(response, Exception):
            errors.append(f"{endpoint_name}: {response}")
            continue
        responses.append((endpoint_name, response))

    if not responses:
        result.update(status="error" if errors else "unknown", error="; ".join(errors) if errors else None)
        result["notes"].append("No public response was collected from configured endpoint candidates.")
        return result

    data_by_endpoint = {name: response.data for name, response in responses}
    result["http_status"] = _first_not_none(response.http_status for _, response in responses)
    result["latency_ms"] = sum(response.latency_ms or 0 for _, response in responses)
    pair_found = any(_contains_any_pair(data, pair_candidates) for data in data_by_endpoint.values())
    market_list_checked = "market_list" in data_by_endpoint
    ticker_detected = any(_detect_ticker_shape(data) for name, data in data_by_endpoint.items() if name in {"ticker", "market_list"})
    orderbook_detected = any(_detect_orderbook_shape(data) for name, data in data_by_endpoint.items() if name == "orderbook")
    timestamp_detected = any(_detect_timestamp(data) for data in data_by_endpoint.values())

    result["public_ticker_shape_detected"] = ticker_detected
    result["public_orderbook_shape_detected"] = orderbook_detected
    result["timestamp_detected"] = timestamp_detected
    result["pair_availability"] = _pair_availability(
        role=role,
        pair_found=pair_found,
        ticker_detected=ticker_detected,
        orderbook_detected=orderbook_detected,
        market_list_checked=market_list_checked,
    )
    if role == "fx_reference":
        _apply_fx_detection(result, data_by_endpoint.values(), source=source)
    result["status"] = "ok" if not errors else "error"
    result["error"] = "; ".join(errors) if errors else None
    if result["pair_availability"] == "available":
        result["notes"].append("Public response clearly indicated candidate pair availability.")
    elif result["pair_availability"] == "unavailable":
        result["notes"].append("Public market-list response was checked but did not clearly include the candidate pair.")
    else:
        result["notes"].append("Pair availability remains unknown; no false-positive availability assertion was made.")
    return result


def empty_probe_result(*, source_id: str, role: str, created_at_utc: str, notes: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": created_at_utc,
        "source_id": source_id,
        "role": role,
        "status": "unknown",
        "pair_availability": "unknown",
        "public_ticker_shape_detected": None,
        "public_orderbook_shape_detected": None,
        "timestamp_detected": None,
        "latency_ms": None,
        "http_status": None,
        "error": None,
        "notes": notes or [],
        "fx_rate_detected": None,
        "fx_pair_detected": None,
        "fx_timestamp_detected": None,
        "fx_date_or_time_value": None,
        "requires_api_key": None,
        "suitable_for_mode_b_candidate": None,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    def count_role(role: str) -> int:
        return sum(1 for result in results if result.get("role") == role)

    available_pairs = [
        {"source_id": result.get("source_id"), "role": result.get("role")}
        for result in results
        if result.get("pair_availability") == "available"
    ]
    unknown_pairs = [
        {"source_id": result.get("source_id"), "role": result.get("role"), "status": result.get("status")}
        for result in results
        if result.get("pair_availability") in {"unknown", "unavailable"}
    ]
    errors = [
        {"source_id": result.get("source_id"), "error": result.get("error")}
        for result in results
        if result.get("status") == "error"
    ]
    fx_suitable_candidates = [
        {
            "source_id": result.get("source_id"),
            "fx_pair_detected": result.get("fx_pair_detected"),
            "fx_date_or_time_value": result.get("fx_date_or_time_value"),
        }
        for result in results
        if result.get("role") == "fx_reference" and result.get("suitable_for_mode_b_candidate") is True
    ]
    fx_unresolved = not bool(fx_suitable_candidates)
    return {
        "domestic_sources_checked": count_role("domestic_usdt_krw"),
        "global_sources_checked": count_role("global_usdt_reference"),
        "fx_sources_checked": count_role("fx_reference"),
        "available_pairs": available_pairs,
        "unknown_pairs": unknown_pairs,
        "errors": errors,
        "fx_suitable_candidates": fx_suitable_candidates,
        "fx_unresolved": fx_unresolved,
        "fx_blocker_reason": (
            "No no-key public USD/KRW FX source exposed both rate and timestamp/freshness metadata."
            if fx_unresolved
            else None
        ),
    }


def write_probe_report(report: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_http_get_json(url: str, *, timeout_seconds: float, headers: dict[str, str] | None = None) -> ProbeHttpResponse:
    public_headers = dict(PUBLIC_HEADERS)
    if headers:
        public_headers.update(headers)
    _assert_public_headers(public_headers)
    started = time.monotonic()
    request = urllib.request.Request(url, headers=public_headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = int(exc.code)
    latency_ms = int((time.monotonic() - started) * 1000)
    data = json.loads(raw.decode("utf-8")) if raw else None
    return ProbeHttpResponse(data=data, http_status=status, latency_ms=latency_ms, url=url)


def build_url(base_url: str, endpoint: dict[str, Any]) -> str | None:
    if not base_url or base_url.startswith("placeholder"):
        return None
    path = str(endpoint.get("path") or "")
    symbol = endpoint.get("symbol")
    if symbol is not None:
        path = path.replace("{symbol}", urllib.parse.quote(str(symbol), safe=""))
    params = endpoint.get("params") if isinstance(endpoint.get("params"), dict) else {}
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return url


def _request_with_retries(
    getter: HttpGetJson,
    url: str,
    *,
    timeout_seconds: float,
    max_retries: int,
) -> ProbeHttpResponse | Exception:
    attempts = max(1, max_retries + 1)
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return getter(url, timeout_seconds=timeout_seconds, headers=dict(PUBLIC_HEADERS))
        except Exception as exc:
            last_error = exc
    return last_error or RuntimeError("unknown probe error")


def _pair_availability(
    *,
    role: str,
    pair_found: bool,
    ticker_detected: bool,
    orderbook_detected: bool,
    market_list_checked: bool,
) -> str:
    if pair_found and (ticker_detected or orderbook_detected or role == "fx_reference"):
        return "available"
    if market_list_checked and not pair_found:
        return "unavailable"
    return "unknown"


def _contains_any_pair(data: Any, pair_candidates: Iterable[str]) -> bool:
    normalized_candidates = {_normalize_pair(candidate) for candidate in pair_candidates if candidate}
    if not normalized_candidates:
        return False
    for value in _walk_values(data):
        if isinstance(value, str):
            normalized_value = _normalize_pair(value)
            if normalized_value in normalized_candidates:
                return True
    return False


def _normalize_pair(value: str) -> str:
    return value.upper().replace("-", "").replace("_", "").replace("/", "").replace(" ", "")


def _detect_ticker_shape(data: Any) -> bool:
    keys = {key.lower() for key in _walk_keys(data)}
    ticker_keys = {
        "trade_price",
        "opening_price",
        "closing_price",
        "bid_price",
        "ask_price",
        "bidprice",
        "askprice",
        "lastprice",
        "last_price",
        "price",
        "bidpx",
        "askpx",
        "rates",
    }
    if keys & ticker_keys:
        return True
    return _has_success_status(data) and any(key in keys for key in {"data", "result", "list"})


def _detect_orderbook_shape(data: Any) -> bool:
    keys = {key.lower() for key in _walk_keys(data)}
    return bool(keys & {"orderbook_units", "bids", "asks", "bid", "ask", "units"})


def _detect_timestamp(data: Any) -> bool:
    keys = {key.lower() for key in _walk_keys(data)}
    timestamp_keys = {"timestamp", "timestamp_utc", "trade_timestamp", "time", "date", "updated_at", "server_time"}
    return bool(keys & timestamp_keys)


def _apply_fx_detection(result: dict[str, Any], payloads: Iterable[Any], *, source: dict[str, Any]) -> None:
    combined_payloads = list(payloads)
    rate_detected, pair_detected = _detect_fx_rate(combined_payloads)
    timestamp_detected, date_or_time_value = _detect_fx_timestamp_value(combined_payloads)
    result["fx_rate_detected"] = rate_detected
    result["fx_pair_detected"] = pair_detected
    result["fx_timestamp_detected"] = timestamp_detected
    result["fx_date_or_time_value"] = date_or_time_value
    requires_api_key = result.get("requires_api_key")
    no_key_public = bool(source.get("no_private_api")) and requires_api_key is False
    suitable = bool(rate_detected and timestamp_detected and no_key_public)
    result["suitable_for_mode_b_candidate"] = suitable
    result["pair_availability"] = "available" if suitable else "unknown"
    if suitable:
        result["notes"].append("FX response exposed a no-key public USD/KRW rate plus timestamp/freshness metadata.")
    elif rate_detected and not timestamp_detected:
        result["notes"].append("FX rate was detected, but timestamp/freshness metadata was missing; not suitable for Mode B.")
    else:
        result["notes"].append("FX response did not prove a suitable USD/KRW rate plus timestamp/freshness shape.")


def _detect_fx_rate(payloads: Iterable[Any]) -> tuple[bool, str | None]:
    for payload in payloads:
        for path, value in _walk_paths(payload):
            normalized_path = ".".join(path).lower()
            if _is_numeric_like(value) and (
                path and path[-1].upper() == "KRW"
                or "usdkrw" in normalized_path.replace("_", "").replace("/", "")
                or normalized_path.endswith("rate") and "krw" in json.dumps(payload).lower()
            ):
                return True, "USD/KRW"
            if isinstance(value, str) and _normalize_pair(value) == "USDKRW":
                return True, "USD/KRW"
    return False, None


def _detect_fx_timestamp_value(payloads: Iterable[Any]) -> tuple[bool, str | None]:
    timestamp_keys = {"date", "timestamp", "time", "updated_at", "as_of", "asof", "effective_date"}
    for payload in payloads:
        for path, value in _walk_paths(payload):
            if path and path[-1].lower() in timestamp_keys and value not in (None, ""):
                return True, str(value)
    return False, None


def _is_numeric_like(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _coerce_optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _walk_paths(data: Any, prefix: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    if isinstance(data, dict):
        for key, value in data.items():
            path = prefix + (str(key),)
            yield path, value
            yield from _walk_paths(value, path)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            yield from _walk_paths(item, prefix + (str(index),))
    else:
        yield prefix, data


def _has_success_status(data: Any) -> bool:
    if isinstance(data, dict):
        status = data.get("status") or data.get("retCode") or data.get("code")
        return status in ("0000", 0, "0", "OK", "ok", "success")
    return False


def _walk_values(data: Any) -> Iterable[Any]:
    if isinstance(data, dict):
        for key, value in data.items():
            yield key
            yield from _walk_values(value)
    elif isinstance(data, list):
        for item in data:
            yield from _walk_values(item)
    else:
        yield data


def _walk_keys(data: Any) -> Iterable[str]:
    if isinstance(data, dict):
        for key, value in data.items():
            yield str(key)
            yield from _walk_keys(value)
    elif isinstance(data, list):
        for item in data:
            yield from _walk_keys(item)


def _first_not_none(values: Iterable[Any]) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _assert_config_has_no_credentials(config: dict[str, Any]) -> None:
    forbidden_keys = {"api_key", "apikey", "secret", "token", "credential", "credentials", "authorization", "password"}
    for key in _walk_keys(config):
        normalized = key.lower().replace("-", "_")
        if normalized in forbidden_keys:
            raise ValueError(f"Probe config contains forbidden credential-like key: {key}")


def _assert_public_headers(headers: dict[str, str]) -> None:
    for key in headers:
        lowered = key.lower()
        if any(fragment in lowered for fragment in PRIVATE_HEADER_FRAGMENTS):
            raise ValueError(f"Private/auth-like header is forbidden for public probe: {key}")

# Spot-Futures Basis Adapter / Registry Integration Planning v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 parser/readiness가 완료된 뒤 live/public-read-only collect path로 연결하기 전 integration boundary를 정의하는 docs-only planning handoff다.

Purpose:

- Parser/readiness가 완료된 `spot_futures_basis_v0`를 live/public-read-only collect path로 연결하기 전 adapter / registry / OpportunityPacket / collect smoke 경계를 정의한다.
- Adapter, registry/config, OpportunityPacket, collect smoke를 한 PR에 몰아넣지 않기 위한 planning이다.
- 현재 behavior는 유지한다.
- `NO_TRADE_ONLY`를 유지한다.
- 이번 PR에서는 code, tests, config, registry, adapter, OpportunityPacket, runtime behavior를 구현하지 않는다.

## 2. Current implementation recap

Current state:

- Deterministic mocked fixture files exist under `tests/fixtures/market_data/spot_futures_basis`.
- Parser helper exists: `src/market_data/parsers/spot_futures_basis.py`.
- Readiness helper exists: `src/strategy/spot_futures_basis_readiness.py`.
- Parser consumes dict payloads only.
- Readiness consumes parser source bundle only.
- Parser/readiness tests are mocked/unit-test only.
- No adapter/live collect path exists yet.
- No OpportunityPacket creation exists yet for `spot_futures_basis_v0`.
- No registry/config integration exists yet.
- No active promotion exists.
- Binance is the first reference venue only, not a Binance-only strategy commitment.

## 3. Proposed adapter identity

Future adapter candidate, planning-only:

- `adapter_id`: `live_binance_spot_futures_basis_btcusdt`
- `strategy_family`: `spot_futures_basis`
- `strategy_id`: `spot_futures_basis_v0`
- `source_venue_id`: `binance`
- `spot_market`: Binance Spot `BTCUSDT`
- `perp_market`: Binance USDⓈ-M Futures `BTCUSDT`
- `comparison_type`: `same_exchange_spot_perp_basis`
- `status`: experimental / non-active / `NO_TRADE_ONLY`

Boundaries:

- This `adapter_id` is a candidate only and is not registered in this PR.
- Do not create a Binance-specific strategy class.
- Binance is the first reference venue only.
- Future Bybit / OKX source mappings should satisfy the same normalized contract and avoid duplicating strategy logic.

## 4. Proposed public endpoint call set

Future adapter public endpoint candidates, planning-only:

### Binance Spot candidates

- `GET /api/v3/ticker/bookTicker`
  - Role: spot top-of-book bid/ask context.
- `GET /api/v3/depth`
  - Role: spot depth / future VWAP context.
- `GET /api/v3/exchangeInfo`
  - Role: spot symbol metadata, filters, tick/step/min-notional-style rules.

### Binance USDⓈ-M Futures candidates

- `GET /fapi/v1/ticker/bookTicker`
  - Role: perp top-of-book bid/ask context.
- `GET /fapi/v1/depth`
  - Role: perp depth / future VWAP context.
- `GET /fapi/v1/premiumIndex`
  - Role: mark/index/funding context, not executable price.
- `GET /fapi/v1/exchangeInfo`
  - Role: futures symbol metadata, margin/contract/rule fields.

Endpoint guardrails:

- These are public no-key endpoint candidates.
- This PR does not call any endpoint.
- Future adapter PR must add safe diagnostics around each public call.
- Future adapter PR must not use private endpoints or credentials.

## 5. Adapter implementation boundary

Future adapter implementation PR should:

- Call only public no-key endpoints.
- Collect raw public payloads.
- Build safe diagnostics for each public GET.
- Pass dict payloads to the existing parser helper.
- Pass source bundle to the existing readiness helper.
- Return analysis-only source bundle / readiness summary or a future OpportunityPacket candidate according to the next planning step.
- Preserve `NO_TRADE_ONLY` metadata and assumptions.
- Preserve generated JSON commit ban.
- Preserve source/runtime safety: no execution, no alert, no Council auto-call.

Future adapter implementation PR must not:

- Use private API.
- Use credentials, API keys, secrets, or tokens.
- Access account/balance/position.
- Place/cancel orders.
- Trigger alert, Council auto-call, or execution.
- Mark the strategy active.
- Silently convert `WATCH` into a trade signal.
- Commit generated sampling JSON.
- Hide venue-specific endpoint/status/timestamp/unit semantics.

## 6. OpportunityPacket boundary

`spot_futures_basis_v0` does not have OpportunityPacket creation yet. Options:

### Option A: source bundle + readiness collect smoke first

- First live adapter returns source bundle/readiness only.
- No OpportunityPacket yet.
- Simpler smoke path.
- Later OpportunityPacket planning PR.
- Risk: source bundle shape may drift from packet shape if planning is delayed.

### Option B: OpportunityPacket candidate mapping planning first

- Before live adapter, define packet observation/candidate mapping.
- Safer long-term.
- Keeps source bundle, readiness, candidate fields, assumptions, warnings, and no-trade metadata aligned.
- More planning before live smoke.

### Option C: minimal OpportunityPacket implementation with adapter

- Faster integration.
- Larger PR and higher coupling risk.
- Harder to review because adapter, packet, and readiness boundaries change together.

Recommended direction:

- Prefer Option B next: OpportunityPacket mapping planning for `spot_futures_basis_v0` before live adapter implementation.
- Reason: beginner safety and existing project patterns benefit from explicit packet/candidate mapping before live collection.
- Keep Option A as fallback if the team wants an even smaller smoke-only path, but still document how source bundle/readiness maps to later packet fields.
- Do not choose Option C yet; adapter + packet implementation in one PR is larger and riskier.
- This PR implements none of these options.

## 7. Registry/config planning

Future registry/config PR principles:

- Strategy remains non-active.
- Adapter may be present only as experimental / disabled / `NO_TRADE_ONLY`.
- Active strategy remains `cross_exchange_spot_spread_v1`.
- Config entry must not enable auto execution.
- Registry entry must not imply Council auto-call.
- Registry/config wording must clearly say analysis-only and public-read-only.
- Generated JSON commit remains forbidden.
- Rollback, if a later registry/config entry is added, is removing that entry and re-running tests.
- Registry/config planning should be a separate PR or at least separate from first adapter implementation.

## 8. Proposed next PR sequence

Recommended sequence:

1. PR 1: Adapter / registry integration planning v0.
2. PR 2: OpportunityPacket mapping planning for `spot_futures_basis_v0`.
3. PR 3: First public-read-only adapter implementation, mocked/unit tests only, no registry activation.
4. PR 4: Registry/config planning, no activation.
5. PR 5: User-local public-read-only collect smoke.
6. PR 6: Docs-only collect evidence.
7. PR 7: 3-sample sampling support.
8. PR 8: 3-sample sampling evidence.
9. PR 9: 30-sample extended evidence.

Sequencing guardrails:

- Do not combine adapter + OpportunityPacket + registry in one PR.
- Do not enable live runtime behavior before mocked/unit tests cover source diagnostics, parser output, readiness output, and no-trade assumptions.
- Do not commit generated smoke JSON at any stage.

## 9. Risk assessment

Key risks to manage:

- Bundling adapter + packet + registry in one PR increases review and rollback risk.
- `WATCH` can be misunderstood as a trade signal if no-trade wording is not preserved.
- Source bundle and OpportunityPacket boundaries can blur if packet mapping is not planned first.
- Binance first reference venue can accidentally become a Binance-only strategy if venue-specific logic leaks into common strategy code.
- Public endpoint live shape may differ from mocked fixtures.
- Top-of-book liquidity can be mistaken for fill feasibility.
- Registry/config entries can be misread as active strategy activation.
- Mark/index/funding context can be mistaken for executable basis if OpportunityPacket fields are not labeled clearly.
- Generated user-local smoke JSON can be accidentally committed unless every PR rechecks generated paths.

## 10. No-trade compliance

This docs-only integration planning PR preserves no-trade posture:

- Active strategy promotion: no
- `spot_futures_basis_v0` active promotion: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Council auto-call: no
- Alert: no
- Execution: no
- Config/registry change: no
- Source/runtime behavior change: no
- Live endpoint call: no
- Adapter implementation: no
- OpportunityPacket implementation: no
- Generated JSON usage: no
- `NO_TRADE_ONLY` preserved: yes

## 11. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR:

- Does not add generated JSON.
- Does not change `data/market_samples`.
- Does not change `data/generated_packets`.
- Does not perform live collection.

## 12. Rollback plan

Rollback path:

1. Revert this docs-only integration planning PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_adapter_registry_integration_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is required.

## 13. Next PR candidates

Recommended order:

1. OpportunityPacket mapping planning for `spot_futures_basis_v0`
2. First public-read-only adapter implementation, mocked/unit tests only
3. Registry/config planning, no activation
4. User-local public-read-only collect smoke
5. 3-sample sampling evidence
6. 30-sample extended evidence

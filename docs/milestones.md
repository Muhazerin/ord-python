# Milestones

Tracks progress against the first-milestone checklist in [`python-plugin-handoff.md`](../python-plugin-handoff.md) §6.

Each step is a discrete, independently-landable unit. Status legend:

- `[x]` — done, merged
- `[~]` — in progress
- `[ ]` — not started

When a step lands, add the merge commit + PR link in the same edit.

---

## Step 1 — Bootstrap the repo `[x]`

Merged in [PR #1](https://github.com/Muhazerin/ord-python/pull/1) (merge commit `0686200`).

Original scope: "`pyproject.toml`, `src/ord/` skeleton, `pytest`, `ruff`, basic CI."

Actually shipped:

- [x] `pyproject.toml` with hatchling build, Pydantic v2 dep, optional `[fastapi]` / `[fastmcp]` extras, dev tools (`pytest`, `pytest-cov`, `ruff`), placeholder `[tool.ord]` section.
- [x] `src/ord/{core,adapters,auth}/` package skeleton with empty `__init__.py` modules.
- [x] `tests/test_smoke.py` verifying the test harness end-to-end.
- [x] Branch coverage with a 90% `--cov-fail-under` gate, enforced via `pyproject.toml` addopts and an explicit CI flag.
- [x] GitHub Actions CI: ruff + pytest, matrix initially `[3.11, 3.12]`, later pinned to `[3.12]` to match local dev.
- [x] Codecov: coverage upload (`codecov-action@v4`) and Test Analytics (`test-results-action@v1`) per matrix job, fail-on-error.
- [x] `codecov.yml` pinning 90% project + patch targets with carryforward.
- [x] `README.md`, `.gitignore`, project-level `CLAUDE.md` (tests-first TDD rule).
- [x] Branch protection on `main`: PR-only, required check `test (3.12)`, enforce-for-admins, force-push + delete blocked, conversation resolution required.

## Step 2 — Build `core/` ORD model `[x]`

Merged in [PR #3](https://github.com/Muhazerin/ord-python/pull/3).

Minimal vertical slice: just the four models needed to emit a valid
single-apiResource ORD document. Package, Product, ConsumptionBundle,
EventResource, EntityType, and IntegrationDependency are deferred until
later steps need them.

- [x] `AccessStrategy` (type, customType).
- [x] `ResourceDefinition` (type, customType, mediaType, url, accessStrategies — non-empty).
- [x] `APIResource` with all 9 spec-required fields (ordId regex-validated, visibility/releaseStatus enums); `partOfPackage` stored as a string ordId reference, Package model deferred.
- [x] `ORDDocument` with `openResourceDiscovery` constrained to spec versions 1.0–1.15 (defaults to "1.15").
- [x] `_ORDModel` base class with `alias_generator=to_camel`, `populate_by_name=True`, `extra="forbid"`, plus `to_ord_dict()` / `to_ord_json()` helpers that default to `by_alias=True, exclude_none=True`.
- [x] Re-exports from `ord.core` package.

## Step 3 — JSON serialization + schema validation `[x]`

Merged in [PR #5](https://github.com/Muhazerin/ord-python/pull/5).

- [x] Vendored the official ORD JSON Schema at `src/ord/_spec/Document.schema.json` (Draft 7, ~440 KB). Source: <https://open-resource-discovery.org/spec-v1/interfaces/Document.schema.json>. Bundled into the wheel automatically by hatchling.
- [x] `scripts/refresh_spec.py` to re-fetch the schema; `docs/vendored-schema.md` documents the source URL, license, and refresh procedure.
- [x] `jsonschema>=4.21,<5` runtime dependency.
- [x] `validate_ord_document(data)` and `ORDValidationError` in `ord.core`. Errors are collected (not first-error-and-bail), each with a JSON-Pointer-shaped `path` and a human-readable `message`.
- [x] `ORDDocument.validate_against_spec()` convenience method that round-trips through `to_ord_dict()`.
- [x] Validation is opt-in — model construction stays cheap, no auto-validation in `__init__`.
- [x] Reconciled `ResourceDefinition.media_type` to required; the spec demands it so consumers know which parser to apply.

## Step 4 — FastAPI adapter (MVP) `[ ]`

Given a `FastAPI` instance, emit one `apiProtocol: "rest"` apiResource pointing at `/openapi.json`. Test against an `examples/fastapi_app/`.

## Step 5 — `server.py` discovery endpoints `[ ]`

FastAPI router that mounts `/.well-known/open-resource-discovery` and `/ord/v1/documents/ord-document`.

## Step 6 — CLI `[ ]`

`ord build --for <module>` equivalent of `cds build --for ord`. Generates JSON + companion artifacts into `gen/ord/`.

## Step 7 — FastMCP adapter `[ ]`

`apiProtocol: "mcp"` apiResource. Decide between omitting `resourceDefinitions` vs `type: "custom"` with our own MCP schema. Document the decision.

## Step 8 — A2A apiResource support `[ ]`

Detect/configure A2A agent cards. Add example in `examples/`.

## Step 9 — DAMN-specific demo `[ ]`

End-to-end example showing all three apiResources (REST + MCP + Agent Document Card schema) for a DAMN-shaped service.

## Step 10 — Auth strategies `[ ]`

Port `open` first, then `basic`, then mTLS. Mirror cap-js/ord config shape under `[tool.ord]` in `pyproject.toml`.

## Step 11 — Seed `docs/upstream-parity.md` `[ ]`

Matrix mapping cap-js/ord features → ported / TODO / not-applicable. Drives roadmap decisions.

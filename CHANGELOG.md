# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- FastAPI adapter: `ord.adapters.fastapi.apiresource_from_fastapi(app, *, ord_id, title, short_description, description, part_of_package, version, visibility, release_status, openapi_url=None)` returns an ORD `APIResource` with `apiProtocol="rest"` and a single `openapi-v3` `resourceDefinitions` entry pointing at the URL the FastAPI app actually serves (`app.openapi_url` or the `openapi_url` override). Raises `ValueError` if both are absent. `fastapi` is an optional install extra; `pip install ord-python[fastapi]`. Working end-to-end demo lives in `examples/fastapi_app/`. ([#7](https://github.com/Muhazerin/ord-python/pull/7))
- JSON Schema validation against the official ORD spec. New: `ord.core.validate_ord_document(data)` and `ORDDocument.validate_against_spec()`, both raising `ORDValidationError` (in `ord.core`) with every violation collected (path + message). The spec is vendored at `src/ord/_spec/Document.schema.json` and refreshable via `scripts/refresh_spec.py`. Validation is opt-in — model construction stays cheap. ([#5](https://github.com/Muhazerin/ord-python/pull/5))
- PEP 561 `py.typed` marker so type checkers (mypy, pyright, IDEs) treat `ord.*` as a typed package and resolve types through to user code. ([#4](https://github.com/Muhazerin/ord-python/pull/4))
- Core ORD models in `ord.core` (`AccessStrategy`, `ResourceDefinition`, `APIResource`, `ORDDocument`) as Pydantic v2 BaseModels. Python attributes are snake_case; spec-shaped JSON output is produced via `to_ord_dict()` / `to_ord_json()` helpers (camelCase aliases, `None` values stripped). `APIResource.ordId` is regex-validated against the spec; `visibility`, `releaseStatus`, and the document `openResourceDiscovery` version are constrained to spec enum values. ([#3](https://github.com/Muhazerin/ord-python/pull/3))
- Project scaffolding: `pyproject.toml` (Pydantic v2, optional `fastapi` / `fastmcp` extras, dev tools), `src/ord/{core,adapters,auth}/` package skeleton, smoke test, README, `.gitignore`, project-level `CLAUDE.md`, handoff doc. ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- GitHub Actions CI on Python 3.12: ruff lint + pytest with 90% branch coverage gate (enforced via `pyproject.toml` addopts and an explicit CI flag). ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- Codecov integration: coverage upload (`codecov/codecov-action@v4`) and Test Analytics (`codecov/test-results-action@v1`), with `codecov.yml` pinning 90% project + patch targets and carryforward. ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- Branch protection on `main`: PR-only, required `test (3.12)` status check, enforce-for-admins, force-push + delete blocked, conversation resolution required. ([#1](https://github.com/Muhazerin/ord-python/pull/1))

### Changed

- Bumped Pydantic floor from `>=2.6` to `>=2.11` and replaced `populate_by_name=True` with `validate_by_name=True` + `validate_by_alias=True` on `_ORDModel`. Pydantic recommends the new pair as of v2.11; `populate_by_name` is slated for deprecation in v3. No user-visible behavior change — both snake_case attribute names and camelCase aliases still validate. ([#6](https://github.com/Muhazerin/ord-python/pull/6))
- `ResourceDefinition.media_type` is now required, matching the ORD spec — emitted documents would have failed JSON Schema validation without it. ([#5](https://github.com/Muhazerin/ord-python/pull/5))

[Unreleased]: https://github.com/Muhazerin/ord-python/compare/0686200...HEAD

# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- PEP 561 `py.typed` marker so type checkers (mypy, pyright, IDEs) treat `ord.*` as a typed package and resolve types through to user code. ([#4](https://github.com/Muhazerin/ord-python/pull/4))
- Core ORD models in `ord.core` (`AccessStrategy`, `ResourceDefinition`, `APIResource`, `ORDDocument`) as Pydantic v2 BaseModels. Python attributes are snake_case; spec-shaped JSON output is produced via `to_ord_dict()` / `to_ord_json()` helpers (camelCase aliases, `None` values stripped). `APIResource.ordId` is regex-validated against the spec; `visibility`, `releaseStatus`, and the document `openResourceDiscovery` version are constrained to spec enum values. ([#3](https://github.com/Muhazerin/ord-python/pull/3))
- Project scaffolding: `pyproject.toml` (Pydantic v2, optional `fastapi` / `fastmcp` extras, dev tools), `src/ord/{core,adapters,auth}/` package skeleton, smoke test, README, `.gitignore`, project-level `CLAUDE.md`, handoff doc. ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- GitHub Actions CI on Python 3.12: ruff lint + pytest with 90% branch coverage gate (enforced via `pyproject.toml` addopts and an explicit CI flag). ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- Codecov integration: coverage upload (`codecov/codecov-action@v4`) and Test Analytics (`codecov/test-results-action@v1`), with `codecov.yml` pinning 90% project + patch targets and carryforward. ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- Branch protection on `main`: PR-only, required `test (3.12)` status check, enforce-for-admins, force-push + delete blocked, conversation resolution required. ([#1](https://github.com/Muhazerin/ord-python/pull/1))

[Unreleased]: https://github.com/Muhazerin/ord-python/compare/0686200...HEAD

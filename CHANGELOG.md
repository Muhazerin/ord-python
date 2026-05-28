# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffolding: `pyproject.toml` (Pydantic v2, optional `fastapi` / `fastmcp` extras, dev tools), `src/ord/{core,adapters,auth}/` package skeleton, smoke test, README, `.gitignore`, project-level `CLAUDE.md`, handoff doc. ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- GitHub Actions CI on Python 3.12: ruff lint + pytest with 90% branch coverage gate (enforced via `pyproject.toml` addopts and an explicit CI flag). ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- Codecov integration: coverage upload (`codecov/codecov-action@v4`) and Test Analytics (`codecov/test-results-action@v1`), with `codecov.yml` pinning 90% project + patch targets and carryforward. ([#1](https://github.com/Muhazerin/ord-python/pull/1))
- Branch protection on `main`: PR-only, required `test (3.12)` status check, enforce-for-admins, force-push + delete blocked, conversation resolution required. ([#1](https://github.com/Muhazerin/ord-python/pull/1))

[Unreleased]: https://github.com/Muhazerin/ord-python/compare/0686200...HEAD

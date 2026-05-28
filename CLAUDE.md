# ord-python — project instructions

## TDD (tests-first, pragmatic)

Follow test-driven development for this repo:

- **New features and bug fixes: write the test first.** The test should fail for the right reason before you write the implementation. Then write the minimum code to pass, then refactor.
- **Bug fixes need a regression test** that fails on the current code and passes after the fix. No fix without a test that would have caught it.
- **Spikes and prototypes are allowed without tests**, but tests must be in place before the work is proposed as done (PR-ready, merged, or marked complete).
- **Don't mark a task complete with failing or skipped tests.** If you can't finish, leave the task in progress and say what's blocking.
- When changing existing behavior, update or add tests in the same change — never silently loosen assertions to make a test pass.

Stack: `pytest` for tests. Aim for fast unit tests on `core/` (framework-agnostic) and integration tests for adapters (`fastapi`, `fastmcp`) using real framework instances in `examples/`.

## CHANGELOG

Every PR must update `CHANGELOG.md` under the `[Unreleased]` section as part of the same change.

- Use the standard [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) sections — `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` — and pick the one that matches the user-facing impact. Create the section under `[Unreleased]` if it doesn't exist yet.
- Write entries from the perspective of someone consuming the library, not the implementer. "Added FastAPI adapter that emits `apiProtocol: rest`", not "refactored adapter base class".
- One bullet per logical change. If a PR genuinely does two unrelated things (rare — prefer two PRs), give each its own bullet.
- **Link the PR at the end of every entry**: `... ([#12](https://github.com/Muhazerin/ord-python/pull/12))`. Gives one click to the diff and discussion, which is more useful than a bare entry date.
- **Don't put per-entry dates under `[Unreleased]`** — git history is authoritative. Dates belong on version headings (`## [1.2.0] — 2026-05-22`) when a release is cut.
- Pure-internal changes that ship no observable difference (renames in private modules, test-only refactors, CI tweaks that don't affect users) can be omitted. When in doubt, write the entry — it's cheaper than someone wondering later.
- Don't move entries out of `[Unreleased]` in a feature PR. Versioned release sections are cut separately when a release is tagged.

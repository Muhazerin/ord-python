# ord-python — project instructions

## TDD (tests-first, pragmatic)

Follow test-driven development for this repo:

- **New features and bug fixes: write the test first.** The test should fail for the right reason before you write the implementation. Then write the minimum code to pass, then refactor.
- **Bug fixes need a regression test** that fails on the current code and passes after the fix. No fix without a test that would have caught it.
- **Spikes and prototypes are allowed without tests**, but tests must be in place before the work is proposed as done (PR-ready, merged, or marked complete).
- **Don't mark a task complete with failing or skipped tests.** If you can't finish, leave the task in progress and say what's blocking.
- When changing existing behavior, update or add tests in the same change — never silently loosen assertions to make a test pass.

Stack: `pytest` for tests. Aim for fast unit tests on `core/` (framework-agnostic) and integration tests for adapters (`fastapi`, `fastmcp`) using real framework instances in `examples/`.

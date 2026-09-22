# Map: Testing cp2 Test Harness & Safety Net

Label: `wayfinder:map`

## Destination

A fully functional test suite for `cp2` using `pytest` and `pytest-django` that verifies account management flows, `demoinfo` synchronization signals, API proxy communication via `api_post`, and page error/resilience behavior under mocked external states without modifying production business logic.

## Notes

- **Domain**: IPOL Control Panel 2 (`cp2`), Django 5.2 application on Python 3.12 managed with `uv`.
- **Skills & Tooling**: `pytest`, `pytest-django`, `pytest-env`, `responses`.
- **Key Invariant**: Django `User` model mutations trigger `pre_save` and `post_delete` signals communicating with external `demoinfo` via `utils.api_post` to keep databases in lockstep.
- **Scope Boundary**: Option A (Pure Test Harness & Suite) — test existing behavior as-is via mocks, no production code refactoring in this effort.
- **Testing Approach**: Focus on happy paths and gracefully handled branches; unhandled 500 error paths deferred until refactoring effort.
- **Tracker**: Local markdown tracker located at `cp2/.wayfinder/`.

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance, then zoom the link for the detail the ticket holds -->

- [Test infrastructure and runner configuration](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/001-test-infrastructure-and-runner-configuration.md) — Configured `pytest`, `pytest-django`, `responses`, and `pytest-env` in `pyproject.toml` and `pytest.ini` with `test_settings.py` for in-memory SQLite and env injection.
- [User sync signals and test fixture architecture](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/002-user-sync-signals-and-test-fixture-architecture.md) — Established 3-layer fixture architecture: global `responses` blocking, `mute_user_signals` context manager for general fixtures, and explicit `demoinfo_mocks` for signal sync assertions.
- [Account management flow test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/003-account-management-flow-test-specification.md) — Implemented 24 test cases in `test_account.py` covering login, remember-me, signout, logout, password reset outbox delivery, profile, and save_profile with baseline error documentation.
- [API proxy and external communication test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/004-api-proxy-and-external-communication-test-specification.md) — Implemented 17 test cases in `test_utils.py` verifying all HTTP verbs, timeout/error absorption to 502, and `user_can_edit_demo` permission logic.
- [View-level error handling and parameter validation contract](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/005-view-level-error-handling-and-parameter-validation-contract.md) — Decided to test happy paths and graceful branches now, deferring unhandled 500 crashes until future refactoring.
- [Core demo management views test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/006-core-demo-management-views-test-specification.md) — Implemented 20 test cases in `test_demo_views.py` covering status, demo editors, demo creation/deletion, showDemo with fallbacks, DDL view/save, edit_demo, and ddl_history.
- [Blob and template management views test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/007-blob-and-template-management-views-test-specification.md) — Implemented 21 test cases in `test_blob_views.py` covering templates, template addition/deletion, blob creation and upload, detailsBlob parsing, VR removal, and showBlobsDemo.
- [Extras and archive views test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/008-extras-and-archive-views-test-specification.md) — Implemented 16 test cases in `test_archive_views.py` covering demoExtras metadata and file upload, template-demo linking, blob demo edits, and paginated archive and experiment inspection.
- [CI integration workflow for automated test execution](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/009-ci-integration-workflow.md) — Configured GitHub Actions workflow in `python.yaml` with Python 3.12, `astral-sh/setup-uv`, and `cd cp2 && uv run pytest`.

## Not yet specified

*(All in-scope fog has been completely resolved and implemented)*

## Out of scope

<!-- see "Out of scope": work ruled beyond the destination; closed, never graduates -->

- Production code refactoring to fix architectural defects, clean up legacy code, or eliminate 500 crashes (ruled out under Option A).
- Live end-to-end integration tests requiring real running `core` / `demoinfo` microservices.
- Browser-based UI / E2E testing (Selenium, Cypress, Playwright).

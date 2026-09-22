# Test infrastructure and runner configuration

Label: `wayfinder:research`  
Status: `closed`  
Assignee: `Test Infrastructure Researcher`  
Blocked by: none  

## Question

How should `pytest`, `pytest-django`, and `responses` be configured in `cp2/pyproject.toml` and `cp2/ControlPanel/pytest.ini` so that Django settings, required environment variables (`IPOL_HOST`, `IPOL_URL`), database isolation, and `uv` runner execution operate cleanly without disrupting the existing environment?

## Resolution

1. **Dependency Management**: Add PEP 735 `[dependency-groups]` to `cp2/pyproject.toml` with `dev = ["pytest>=8.3.0", "pytest-django>=4.9.0", "pytest-env>=1.1.5", "responses>=0.25.6"]` matching `modules/core/pyproject.toml` conventions.
2. **Settings & Env Injection**: Create `ControlPanel/test_settings.py` that sets fallback defaults for `IPOL_HOST` and `IPOL_URL`, inherits from `ControlPanel.settings`, configures `DATABASES["default"]["NAME"] = ":memory:"`, sets `MD5PasswordHasher` (fast hashing), and uses `locmem.EmailBackend`. Also declare fallback environment defaults via `pytest-env` in `pytest.ini` and `pyproject.toml`.
3. **Python Path**: Configure `pythonpath = ["ControlPanel"]` (from `cp2/`) and `pythonpath = .` (from `cp2/ControlPanel/`) so imports like `from ControlPanel.account import *` resolve without error.
4. **Migrations**: SQLite in-memory runs standard migrations in <0.3s for Django contrib auth/sessions tables.
5. **Execution**: `uv run pytest` runs cleanly from both `cp2/` and `cp2/ControlPanel/`.

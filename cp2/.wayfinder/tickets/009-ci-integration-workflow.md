# CI integration workflow for automated test execution

Label: `wayfinder:task`  
Status: `closed`  
Assignee: `Antigravity`  
Blocked by: none  

## Question

How should a GitHub Actions CI workflow (e.g. `.github/workflows/cp2-tests.yml`) be configured to install `uv`, cache Python 3.12 dependencies, and run `uv run pytest` on pull requests and pushes touching `cp2/`?

## Resolution

Configured in [`.github/workflows/python.yaml`](file:///Users/hectormacias/Code/IPOL/ipolDevel/.github/workflows/python.yaml) by adding a dedicated `test-cp2` job:
1. Checked out the repository on `ubuntu-latest`.
2. Set up Python 3.12 (matching `cp2`'s strict `requires-python = "==3.12.*"`).
3. Configured `astral-sh/setup-uv@v6` with `version: "0.9.3"`.
4. Executed `cd cp2 && uv run pytest` to automatically install all dependencies into the project virtualenv and run the test suite.

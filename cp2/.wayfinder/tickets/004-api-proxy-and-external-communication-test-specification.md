# API proxy and external communication test specification

Label: `wayfinder:prototype`  
Status: `closed`  
Assignee: `Antigravity`  
Blocked by: [Test infrastructure and runner configuration](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/001-test-infrastructure-and-runner-configuration.md)  

## Question

How should `ControlPanel.utils.api_post` and `user_can_edit_demo` be tested across all supported HTTP verbs (GET, POST, PUT, PATCH, DELETE), malformed responses, network timeouts, 502 Bad Gateway errors, and permission rules (superuser/staff vs normal user email matching)?

## Resolution

Implemented in [`cp2/ControlPanel/tests/test_utils.py`](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/ControlPanel/tests/test_utils.py) with 17 dedicated test cases across 3 test suites (all passing):
1. **HTTP Verbs & Return Shape Contracts**:
   - `get`, `post`, and `patch` return parsed JSON dictionaries `(dict, status_code)`.
   - `put` and `delete` return raw `requests.Response` instances `(Response, status_code)`.
   - Forwarding of query `params`, `json` payload, and HTTP headers was verified.
2. **Resilience & Fault Tolerance**:
   - Non-JSON / HTML responses (e.g. 502 HTML pages) return `({}, status_code)`.
   - Network connection errors (`requests.exceptions.ConnectionError`) and timeouts (`requests.exceptions.Timeout`) are caught and return `({}, 502)`.
   - Unsupported verbs (e.g. `head`) trigger `assert False` which is caught by the generic `except Exception` handler and returns `({}, 502)`.
3. **Authorization & Permission Rules (`user_can_edit_demo`)**:
   - Superusers and staff users are authorized immediately without firing any network requests.
   - Non-staff users are granted edit permission if their email matches one of the demo editors returned by `/api/demoinfo/demos/{id}/editors`.
   - Non-staff users are denied when their email is absent, when the list is empty, or when the upstream API returns an error status (e.g. 502).
   - Documented baseline defect: If the editors endpoint returns a dictionary (e.g. `{"error": ...}`) instead of a list, iterating the dictionary keys causes `AttributeError: 'str' object has no attribute 'get'`.

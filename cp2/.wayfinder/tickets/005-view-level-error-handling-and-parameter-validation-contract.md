# View-level error handling and parameter validation contract

Label: `wayfinder:grilling`  
Status: `closed`  
Assignee: `Antigravity`  
Blocked by: [Account management flow test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/003-account-management-flow-test-specification.md), [API proxy and external communication test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/004-api-proxy-and-external-communication-test-specification.md)  

## Question

Given that views in `ControlPanel/view.py` and `account.py` currently raise unhandled 500 errors (such as `KeyError` or `TypeError`) when query parameters or expected API response keys are absent, how should our test suite treat these cases: should tests assert the exact existing unhandled exception as a baseline regression assertion, or should we define expected HTTP error contract boundaries?

## Resolution

**Decision**: Focus on happy path testing and gracefully handled branches for now. Defer testing unhandled 500 crash paths (such as missing `demo_id` query params or malformed API responses causing `KeyError`/`TypeError`) until an upcoming refactoring effort hardens error handling across the views.

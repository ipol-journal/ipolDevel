# Account management flow test specification

Label: `wayfinder:prototype`  
Status: `closed`  
Assignee: `Antigravity`  
Blocked by: [Test infrastructure and runner configuration](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/001-test-infrastructure-and-runner-configuration.md), [User sync signals and test fixture architecture](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/002-user-sync-signals-and-test-fixture-architecture.md)  

## Question

What is the complete matrix of test cases, input payloads, session assertions, email mocks, and API synchronization verifications required to test `loginPage`, `signout`, `logout`, `password_reset`, `profile`, and `save_profile` as a prototype test module?

## Resolution

Implemented in [`cp2/ControlPanel/tests/test_account.py`](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/ControlPanel/tests/test_account.py) with 24 dedicated test cases across 5 test suites (all passing):
1. **Login Flow (`loginPage`)**: Form rendering, successful session creation and redirection, remember-me flag browser-close session vs standard expiry, invalid credentials flash messaging, empty submission handling.
2. **Signout & Logout (`signout`, `logout`)**: Enforced `@login_required` redirects, template rendering on signout, session flush and login redirection on logout.
3. **Password Reset (`password_reset`)**: Token generation and outbox email verification, plus baseline assertions documenting production defects:
   - Nonexistent email falls through to re-rendering an empty form with 200 OK.
   - Malformed email input obliterates error state because form is overwritten with an unbound form on line 99.
   - `SMTPException` triggers `TypeError` due to missing string format specifier in `logger.warning("...", e)` on line 94.
4. **Profile View (`profile`)**: Authentication requirement and user context rendering (username, email, firstName, lastName).
5. **Save Profile (`save_profile`)**: Authentication enforcement, empty email validation warning, 502 external API error warning, duplicate email in demoinfo warning, successful profile updates, and baseline regression assertion for unhandled `KeyError` when required form keys are omitted.

# Core demo management views test specification

Label: `wayfinder:prototype`  
Status: `closed`  
Assignee: `Antigravity`  
Blocked by: none  

## Question

What are the happy-path test specifications, request mocks, and permission fixtures required to test core demo management views (`status`, `demo_editors`, `add_demo_editor`, `remove_demo_editor`, `showDemo`, `ajax_show_DDL`, `ajax_save_DDL`, `edit_demo`) in `test_demo_views.py` adhering to the decision in Ticket 005?

## Resolution

Implemented in [`cp2/ControlPanel/tests/test_demo_views.py`](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/ControlPanel/tests/test_demo_views.py) with 20 dedicated test cases across 4 test suites (all passing):
1. **Status & General**: Verified unauthenticated redirect and authenticated 200 OK rendering `status.html`.
2. **Demo Editors Management**: Verified `demo_editors` rendering with alphabetical sorting of available editors; verified `add_demo_editor` redirection on success and JSON KO on error; verified `remove_demo_editor` JSON OK on success, and captured baseline defect assertion when deletion API returns non-204 (calling `.get("error")` on a raw `requests.Response` raises `AttributeError`).
3. **Demo Creation & Deletion**: Verified `ajax_add_demo` integer validation (400 on non-int) and complete creation flow (creating demo in demoinfo, looking up creator editor ID, linking editor to demo, redirecting to `showDemo`); verified staff demo deletion via `ajax_delete_demo`.
4. **Show Demo & DDL Flow**: Verified `showDemo` loads DDL, SSH keys, editors, available editors, and metadata; verified graceful fallbacks when DDL or SSH keys fail; verified `ajax_show_DDL`, authorized vs 401 unauthorized `ajax_save_DDL`, `ajax_user_can_edit_demo`, `edit_demo` multi-service coordination, `ddl_history` rendering, and `reset_ssh_key`.

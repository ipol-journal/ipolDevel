# Extras and archive views test specification

Label: `wayfinder:prototype`  
Status: `closed`  
Assignee: `Antigravity`  
Blocked by: [Core demo management views test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/006-core-demo-management-views-test-specification.md)  

## Question

What are the happy-path test specifications, request mocks, and response fixtures required to test `demoExtras`, `ajax_add_demo_extras`, `show_archive`, and `show_experiment` in `test_archive_views.py`?

## Resolution

Implemented in [`cp2/ControlPanel/tests/test_archive_views.py`](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/ControlPanel/tests/test_archive_views.py) with 16 dedicated test cases across 3 test suites (all passing):
1. **Demo Extras**: Authentication enforcement on `demoExtras`, metadata extraction (size, unquoted URL filename, datetime from timestamp), file upload in `ajax_add_demo_extras` (200 success and 500 on error), and `ajax_delete_demo_extras` (redirect on 204 vs `error.html` on 404).
2. **Template-Demo Linking & Demo Blob Editing**: Authorized template linking (`ajax_add_template_to_demo`), unauthorized redirection to homepage, template unlinking (`ajax_remove_template_to_demo` 204), and demo blob editing (`ajax_edit_blob_demo` 200 OK).
3. **Archive & Experiments**: Paginated experiment listing in `show_archive`, experiment detail rendering in `show_experiment`, graceful `error.html` (404) rendering when experiment is not found, and experiment deletion (`ajax_delete_experiment` OK vs KO).

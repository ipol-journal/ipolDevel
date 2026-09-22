# Blob and template management views test specification

Label: `wayfinder:prototype`  
Status: `closed`  
Assignee: `Antigravity`  
Blocked by: [Core demo management views test specification](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/.wayfinder/tickets/006-core-demo-management-views-test-specification.md)  

## Question

What are the happy-path test specifications, request mocks, and response fixtures required to test template and blob views (`templates`, `showTemplate`, `CreateBlob`, `detailsBlob`, `ajax_add_blob_demo`, `ajax_remove_blob_from_demo`) in `test_blob_views.py`?

## Resolution

Implemented in [`cp2/ControlPanel/tests/test_blob_views.py`](file:///Users/hectormacias/Code/IPOL/ipolDevel/cp2/ControlPanel/tests/test_blob_views.py) with 21 dedicated test cases across 4 test suites (all passing):
1. **Templates Views**: Authentication enforcement on `templates`, list rendering of available templates, `ajax_add_template` 200 vs 401 unauthorized, `showTemplate` details and superuser `can_edit` flag, `ajax_delete_template` JSON OK vs KO.
2. **Blob Creation & Upload**: Context preparation in demo mode vs template mode in `CreateBlob`, `ajax_add_blob_demo` authorized multipart upload via `SimpleUploadedFile` forwarding to API, unauthorized non-staff rendering homepage.
3. **Blob Details & Editing**: `detailsBlob` parsing nested blob dictionary for demo mode and template mode, missing blob index returning 404 with error message, `ajax_edit_blob_template` PUT metadata update.
4. **Blob Removal & VR Management**: `ajax_remove_blob_from_template` DELETE returning OK, `ajax_remove_blob_from_demo` unauthorized 403-style KO vs authorized staff OK, `showBlobsDemo` loading owned blobs, demo templates, and template list; `ajax_remove_vr` 200 OK vs 404 error.

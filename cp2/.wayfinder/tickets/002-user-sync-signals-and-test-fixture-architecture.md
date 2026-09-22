# User sync signals and test fixture architecture

Label: `wayfinder:research`  
Status: `closed`  
Assignee: `User Signals Researcher`  
Blocked by: none  

## Question

What is the exact contract between `ControlPanel/models.py` user signals (`pre_save`, `post_delete`) and external `demoinfo` endpoints (`/api/demoinfo/editor`), and how should test fixtures and mocks be designed so tests can create and manipulate test users without accidental live HTTP requests or breaking signal expectations?

## Resolution

1. **Signal HTTP Contract**:
   - `pre_save` (`user_created_handler`):
     - If `email` is empty/newly created in admin, returns early (0 calls).
     - When email is set/changed: calls `GET /api/demoinfo/editor?email={new}` and `GET /api/demoinfo/editor?email={old}`. If both are absent, calls `POST /api/demoinfo/editor` (expects 201). If old exists and new is free, calls `PATCH /api/demoinfo/editor` (expects 201). If new email is already in use, raises `ValidationError`.
     - *Known Production Gotcha*: Creating a user with email directly in one step (e.g. `User.objects.create_user(email="...")`) triggers `User.DoesNotExist` because `old_editor = User.objects.get(username=...)` runs in `pre_save` before DB commit.
   - `post_delete` (`delete_profile`):
     - Calls `GET /api/demoinfo/editor?email={instance.email}`.
     - If editor found: calls `DELETE /api/demoinfo/editor/{editor_id}` (expects 204).
     - *Known Production Gotcha*: Line 89 does `editor_id = editor_info["id"]` before `if editor_info:`. If editor is not found or API returns 502, raises `TypeError`.
2. **3-Layer Fixture Architecture**:
   - **Layer 1: Global Network Isolation**: Auto-use `responses.RequestsMock` to intercept and prevent any leaked outbound HTTP calls.
   - **Layer 2: Safe Fixture User Factory (`mute_user_signals`)**: Disconnect `pre_save` and `post_delete` signals during user setup for general tests (auth, permissions, view rendering).
   - **Layer 3: Demoinfo Mock Helpers**: Dedicated mock helpers (`demoinfo_mocks`) with explicit endpoints for testing the signal synchronization behavior itself, asserting sync payloads and testing edge cases (duplicate email, API 502, user deletion).

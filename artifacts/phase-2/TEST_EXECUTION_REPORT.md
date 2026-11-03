# OptiGuide — Phase 2 Test Execution Report

**Date:** November 3, 2026  
**Execution Environment:** Windows 11 PowerShell 5.1  
**Python Runtime:** Python 3.13.14 (Virtualenv at `backend/.venv`)  
**Test Framework:** Pytest 8.4.2  
**Result:** 65 passed, 0 failed, 0 errors in 1.58s  

---

## 1. Test Execution Command
```powershell
& "backend/.venv/Scripts/python" -m pytest backend/tests -v
```

## 2. Test Execution Output
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.4.2, pluggy-1.7.0 -- C:\Users\sugud\OneDrive\Documents\optiguide\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\sugud\OneDrive\Documents\optiguide\backend
configfile: pyproject.toml
plugins: anyio-4.16.0, asyncio-0.26.0
asyncio: mode=Mode.AUTO, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 65 items

backend\tests\api\test_auth_api.py::test_register_success PASSED         [  1%]
backend\tests\api\test_auth_api.py::test_register_duplicate_email PASSED [  3%]
backend\tests\api\test_auth_api.py::test_register_weak_password PASSED   [  4%]
backend\tests\api\test_auth_api.py::test_register_invalid_email PASSED   [  6%]
backend\tests\api\test_auth_api.py::test_login_success PASSED            [  7%]
backend\tests\api\test_auth_api.py::test_login_incorrect_password PASSED [  9%]
backend\tests\api\test_auth_api.py::test_login_nonexistent_email PASSED  [ 10%]
backend\tests\api\test_auth_api.py::test_refresh_token_lifecycle_and_reuse_detection PASSED [ 12%]
backend\tests\api\test_auth_api.py::test_refresh_token_invalid PASSED    [ 13%]
backend\tests\api\test_auth_api.py::test_refresh_token_expired PASSED    [ 15%]
backend\tests\api\test_auth_api.py::test_logout_single_session PASSED    [ 16%]
backend\tests\api\test_auth_api.py::test_logout_all_sessions PASSED      [ 18%]
backend\tests\api\test_auth_api.py::test_get_me_endpoint PASSED          [ 20%]
backend\tests\api\test_errors_api.py::test_404_not_found PASSED          [ 21%]
backend\tests\api\test_errors_api.py::test_405_method_not_allowed PASSED [ 23%]
backend\tests\api\test_errors_api.py::test_validation_error_envelope PASSED [ 24%]
backend\tests\api\test_errors_api.py::test_500_internal_server_error_sanitization PASSED [ 26%]
backend\tests\api\test_root_api.py::test_root_endpoint_identification PASSED [ 27%]
backend\tests\api\test_root_api.py::test_root_health_endpoint PASSED     [ 29%]
backend\tests\api\test_root_api.py::test_swagger_disabled_when_debug_false PASSED [ 30%]
backend\tests\api\test_root_api.py::test_swagger_enabled_when_debug_true PASSED [ 32%]
backend\tests\api\test_users_api.py::test_get_users_me PASSED            [ 33%]
backend\tests\api\test_users_api.py::test_update_users_me PASSED         [ 35%]
backend\tests\api\test_users_api.py::test_list_user_sessions PASSED      [ 36%]
backend\tests\api\test_users_api.py::test_admin_update_status_forbidden_for_patient PASSED [ 38%]
backend\tests\api\test_users_api.py::test_admin_deactivate_user_and_revoke_sessions PASSED [ 40%]
backend\tests\api\test_v1_health_api.py::test_api_v1_health_connected PASSED [ 41%]
backend\tests\api\test_v1_health_api.py::test_api_v1_health_database_connected PASSED [ 43%]
backend\tests\api\test_v1_health_api.py::test_api_v1_health_db_alias PASSED [ 44%]
backend\tests\api\test_v1_health_api.py::test_api_v1_health_degraded_when_db_down PASSED [ 46%]
backend\tests\api\test_v1_health_api.py::test_api_v1_health_database_error_when_db_down PASSED [ 47%]
backend\tests\api\test_v1_health_api.py::test_db_error_security_credential_leak_prevention PASSED [ 49%]
backend\tests\api\test_v1_health_api.py::test_check_db_connectivity_sanitizes_raw_exceptions PASSED [ 50%]
backend\tests\integration\test_auth_integration.py::test_user_persistence_and_query PASSED [ 52%]
backend\tests\integration\test_auth_integration.py::test_session_cascade_deletion_on_user_delete PASSED [ 53%]
backend\tests\integration\test_auth_integration.py::test_token_rotation_integration PASSED [ 55%]
backend\tests\integration\test_db_integration.py::test_db_connectivity_live PASSED [ 56%]
backend\tests\integration\test_db_integration.py::test_db_session_lifecycle PASSED [ 58%]
backend\tests\integration\test_db_integration.py::test_session_local_direct_instantiation PASSED [ 60%]
backend\tests\integration\test_db_integration.py::test_engine_dialect PASSED [ 61%]
backend\tests\integration\test_db_isolation.py::test_postgres_url_does_not_affect_tests_or_leak PASSED [ 63%]
backend\tests\unit\test_config.py::test_settings_defaults PASSED         [ 64%]
backend\tests\unit\test_config.py::test_settings_cors_origins_json_list PASSED [ 66%]
backend\tests\unit\test_config.py::test_settings_cors_origins_comma_separated PASSED [ 67%]
backend\tests\unit\test_config.py::test_settings_custom_values PASSED    [ 69%]
backend\tests\unit\test_exceptions.py::test_custom_exceptions PASSED     [ 70%]
backend\tests\unit\test_logging.py::test_sanitize_dict_flat_and_case_insensitive PASSED [ 72%]
backend\tests\unit\test_logging.py::test_sanitize_dict_nested_and_lists PASSED [ 73%]
backend\tests\unit\test_logging.py::test_sanitize_log_message_credentials_in_url PASSED [ 75%]
backend\tests\unit\test_logging.py::test_sanitize_log_message_bearer_token PASSED [ 76%]
backend\tests\unit\test_logging.py::test_sanitizing_filter_in_logger PASSED [ 78%]
backend\tests\unit\test_schemas.py::test_app_info_schema PASSED          [ 80%]
backend\tests\unit\test_schemas.py::test_health_response_schema PASSED   [ 81%]
backend\tests\unit\test_schemas.py::test_database_health_response_schema PASSED [ 83%]
backend\tests\unit\test_schemas.py::test_error_envelope_schema PASSED    [ 84%]
backend\tests\unit\test_schemas.py::test_paginated_response_schema PASSED [ 86%]
backend\tests\unit\test_schemas.py::test_invalid_health_schema_raises PASSED [ 87%]
backend\tests\unit\test_security_auth.py::test_argon2id_password_hashing_and_verification PASSED [ 89%]
backend\tests\unit\test_security_auth.py::test_password_strength_validation PASSED [ 90%]
backend\tests\unit\test_security_auth.py::test_refresh_token_generation_and_hashing PASSED [ 92%]
backend\tests\unit\test_security_auth.py::test_jwt_creation_and_decoding PASSED [ 93%]
backend\tests\unit\test_security_auth.py::test_jwt_expired_token_rejection PASSED [ 95%]
backend\tests\unit\test_security_auth.py::test_jwt_invalid_signature_rejection PASSED [ 96%]
backend\tests\unit\test_security_auth.py::test_jwt_wrong_type_rejection PASSED [ 98%]
backend\tests\unit\test_security_auth.py::test_rate_limiter_exceeded PASSED [100%]

======================= 65 passed, 15 warnings in 1.58s =======================
```

# Tasks: v20-integration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250 - 300 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Foundation (v20_decryptor.py)

- [x] 1.1 Create `chrome_v20_decryption/v20_decryptor.py`.
- [x] 1.2 Define Win32 `ctypes` structures for `TOKEN_PRIVILEGES`, `LUID_AND_ATTRIBUTES`, `LUID`.
- [x] 1.3 Define `ctypes` function signatures for `advapi32.dll` (`OpenProcessToken`, `DuplicateTokenEx`, `ImpersonateLoggedOnUser`, `RevertToSelf`, `LookupPrivilegeValueW`, `AdjustTokenPrivileges`).
- [x] 1.4 Define `ctypes` function signatures for `ncrypt.dll` (`NCryptOpenStorageProvider`, `NCryptOpenKey`, `NCryptDecrypt`, `NCryptFreeObject`).
- [x] 1.5 Create `TokenManager` context manager to handle `SeDebugPrivilege`, duplicate `winlogon.exe` (or `lsass.exe`) token, and safely `RevertToSelf` on exit.

## Phase 2: Core Implementation (Key Derivation)

- [x] 2.1 Implement `parse_key_blob(blob_data)` in `v20_decryptor.py` to extract flag, iv, ciphertext, tag, and encrypted AES key.
- [x] 2.2 Implement `decrypt_with_cng(input_data)` in `v20_decryptor.py` calling `NCryptDecrypt` twice as SYSTEM.
- [x] 2.3 Implement `get_v20_key(encrypted_key)` that uses `TokenManager`, performs double DPAPI (SYSTEM, then User), and derives the AES-GCM master key depending on the flag (1, 2, or 3).

## Phase 3: Integration (main.py)

- [x] 3.1 Update `main.py` (`ChromiumDecryptor.get_key()`) to detect `app_bound_encrypted_key` in Local State.
- [x] 3.2 If `app_bound_encrypted_key` exists, import `chrome_v20_decryption.v20_decryptor` dynamically.
- [x] 3.3 Call `get_v20_key()` and return the master key. Handle `ImportError` or `Exception` to fail gracefully.
- [x] 3.4 Update `ChromiumDecryptor.decrypt()` to parse `v20` prefixes, returning `[Admin Required for v20]` or `[Error AES-GCM]` if key extraction failed.

## Phase 4: Testing

- [x] 4.1 Update `tests/test_decryptor.py` to mock `ctypes.windll.advapi32` and verify `RevertToSelf` is called even when `ImpersonateLoggedOnUser` raises an exception.
- [x] 4.2 Add unit test for `get_v20_key` providing a static blob and mock DPAPI/CNG returns to verify XOR logic.

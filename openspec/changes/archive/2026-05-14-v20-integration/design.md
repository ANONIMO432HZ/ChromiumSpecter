# Design: v20-integration

## Technical Approach

We will isolate the heavy Windows API interactions in a new module `chrome_v20_decryption/v20_decryptor.py`. `main.py` will dynamically import this module when a v20 blob is encountered or during the master key extraction phase. The `v20_decryptor.py` module will use `ctypes` exclusively to avoid external dependencies, wrapping the necessary functions from `advapi32.dll` and `ncrypt.dll`.

## Architecture Decisions

### Decision: Native ctypes vs Dependency

**Choice**: Native `ctypes.windll` wrapper.
**Alternatives considered**: Importing the `windows` pip package (PythonForWindows).
**Rationale**: ChromiumSpecter is meant to be compiled into a standalone, stealthy binary. Adding a heavy dependency increases the binary size and potential for AV/EDR flags. Building a strict subset of `ctypes` structures keeps the footprint minimal.

### Decision: Impersonation Target

**Choice**: `winlogon.exe` (fallback to `lsass.exe`).
**Alternatives considered**: Target `lsass.exe` directly as per the PoC.
**Rationale**: Accessing `lsass.exe` is heavily monitored by EDRs (Credential Dumping). `winlogon.exe` also runs as `SYSTEM` but is generally less sensitive to `PROCESS_QUERY_INFORMATION` and `PROCESS_DUP_HANDLE` requests.

## Data Flow

    ChromiumDecryptor (main.py)
         │ (1) Extract Local State
         ▼
    Extract app_bound_encrypted_key
         │ (2) Call v20_decryptor.py
         ▼
    TokenManager: Impersonate SYSTEM (winlogon.exe)
         │ (3) CryptUnprotectData (SYSTEM)
         ▼
    TokenManager: RevertToSelf()
         │ (4) CryptUnprotectData (User)
         ▼
    CNGExtractor: NCryptDecrypt (if Flag == 3)
         │ (5) XOR key derivation
         ▼
    Return AES-GCM Master Key

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `chrome_v20_decryption/v20_decryptor.py` | Create | Contains Win32 `ctypes` structures, `TokenManager` context manager, and `decrypt_with_cng` logic. |
| `main.py` | Modify | Update `ChromiumDecryptor.get_key()` to handle the double DPAPI/CNG flow if `win32crypt` is available and the key is App-Bound. Update `ChromiumDecryptor.decrypt()` to parse `v20` headers. |
| `tests/test_decryptor.py` | Modify | Add mocks for `ctypes.windll.advapi32` and `ncrypt` to test the logic flow safely. |

## Interfaces / Contracts

```python
# v20_decryptor.py interface
class TokenManager:
    def __enter__(self):
        # Enable SeDebugPrivilege
        # Duplicate winlogon.exe token
        # Impersonate
        pass
    def __exit__(self, exc_type, exc_val, exc_tb):
        # RevertToSelf()
        pass

def get_v20_key(encrypted_key: bytes) -> bytes | None:
    """Handles the double DPAPI unprotect and CNG decryption. Returns raw AES key."""
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Token Impersonation flow | Mock `advapi32.dll` to ensure `RevertToSelf` is ALWAYS called even if `ImpersonateLoggedOnUser` raises an exception. |
| Unit | Key Derivation | Provide a static, hardcoded App-Bound blob and mock the DPAPI/CNG return values to ensure the final AES XOR math is correct. |

## Migration / Rollout

No migration required. The logic acts as a fallback/extension for Chrome 127+ profiles. Older profiles will gracefully fall back to the legacy `v10` flow.

## Open Questions

- None. The API surface is clear.

# Proposal: v20-integration

## Intent

Implement support for Chrome v20 (App-Bound Encryption) decryption in ChromiumSpecter. Since Chrome 127, keys are bound to the app identity, requiring SYSTEM privileges and CNG API (`ncrypt.dll`) interaction to extract the master key. This change restores credential recovery capabilities for modern Chrome versions.

## Scope

### In Scope
- Build a native `ctypes` bridge for `ncrypt.dll` (CNG) and `advapi32.dll` (Token management).
- Impersonate a SYSTEM process (preferably `winlogon.exe`) to access the `Google Chromekey1` stored in MS KSP.
- Implement the double-DPAPI decryption flow for `app_bound_encrypted_key`.
- Derive the final AES-GCM master key using v20 flags (1, 2, and 3).
- Update `main.py` (`ChromiumDecryptor`) to seamlessly support `v20` blobs alongside `v10/v11`.

### Out of Scope
- External dependencies (e.g., `windows` pip package).
- EDR evasion techniques beyond using `winlogon.exe` and `RevertToSelf`.
- Mac/Linux App-Bound Encryption bypass (Windows only).

## Capabilities

### New Capabilities
- `v20-decryption`: Support for decrypting Chrome v20+ App-Bound Encryption blobs via SYSTEM impersonation and CNG.

### Modified Capabilities
- None

## Approach

Use a **Native ctypes Bridge**. Create `v20_decryptor.py` containing `TokenManager` (handles `SeDebugPrivilege` and impersonation) and `CNGExtractor` (handles `NCrypt` calls). `main.py` will conditionally import or use this module if running as Admin, keeping the core lightweight and free of heavy dependencies. We will target `winlogon.exe` for impersonation to reduce EDR noise compared to `lsass.exe`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `chrome_v20_decryption/v20_decryptor.py` | New | Module for token and CNG operations |
| `main.py` | Modified | Update `ChromiumDecryptor` to parse v20 and call `v20_decryptor` |
| `tests/test_decryptor.py` | Modified | Add tests and mocks for `v20` logic |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| EDR Detection (SYSTEM Impersonation) | High | Target `winlogon.exe`, minimize time spent impersonated (`RevertToSelf`). |
| Process Crash during Impersonation | Low | Wrap impersonation in a context manager (`try/finally`) to guarantee reversion. |

## Rollback Plan

Revert changes in `main.py` to `v1.4.0` state and remove `v20_decryptor.py`. The testing infrastructure is decoupled and will remain intact.

## Dependencies

- Requires running the compiled binary/script as Administrator.

## Success Criteria

- [ ] ChromiumSpecter successfully decrypts `v20` cookies/passwords from Chrome 127+ in a Windows environment.
- [ ] No new third-party PIP dependencies are added to `requirements.txt`.
- [ ] Existing `v10`/`v11` and legacy DPAPI decryption remains fully functional.

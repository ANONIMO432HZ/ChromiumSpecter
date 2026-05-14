# v20-decryption Specification

## Purpose

Defines the requirements for decrypting Chrome v20 (App-Bound Encryption) `app_bound_encrypted_key` and derived AES-GCM master keys within ChromiumSpecter.

## Requirements

### Requirement: SYSTEM Impersonation

The system MUST elevate its token to impersonate a running SYSTEM process (e.g., `winlogon.exe`) to access the `Google Chromekey1` cryptographic provider, and MUST revert to its original token immediately after key extraction.

#### Scenario: Successful SYSTEM Impersonation

- GIVEN the script is running with Administrative privileges
- WHEN the token manager attempts to extract the V20 master key
- THEN the script MUST enable `SeDebugPrivilege`
- AND impersonate `winlogon.exe` (or fallback)
- AND successfully open the CNG key
- AND revert back to the original token.

#### Scenario: Lack of Administrative Privileges

- GIVEN the script is running as a standard user
- WHEN the script attempts to extract the V20 master key
- THEN the script MUST fail gracefully
- AND return a clear "[Admin Required for v20]" indicator.

### Requirement: Master Key Derivation (Double DPAPI & CNG)

The system MUST perform a double DPAPI unprotect (first as SYSTEM, then as User) on the `app_bound_encrypted_key`, parse the resulting blob flags, and derive the final AES-GCM key using CNG if the flag is 3.

#### Scenario: V20 Flag 3 Key Derivation

- GIVEN a valid `app_bound_encrypted_key` blob containing flag 3
- WHEN decrypting the master key
- THEN the system MUST use CNG (`NCryptDecrypt`) twice as SYSTEM to unwrap the AES key
- AND apply the flag 3 XOR constant
- AND return the derived `AESGCM` key ready for cookie decryption.

### Requirement: Fallback and Stability

The system MUST NOT crash or leak the impersonated SYSTEM token if any step of the extraction fails.

#### Scenario: CNG Extraction Failure

- GIVEN an active SYSTEM impersonation
- WHEN `NCryptOpenStorageProvider` or `NCryptDecrypt` fails
- THEN the system MUST catch the exception
- AND revert the token to the original user
- AND return `None` for the master key, allowing the legacy DPAPI flow to continue for older blobs.

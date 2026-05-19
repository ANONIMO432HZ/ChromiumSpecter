# Solución de Problemas Comunes

Este documento detalla los problemas frecuentes encontrados durante la compilación, ofuscación y ejecución del proyecto, y cómo resolverlos.

---

## 1. PyArmor: El término 'pyarmor' no se reconoce como nombre de comando

### Síntoma
Intentás ejecutar `pyarmor` y recibís un mensaje de error indicando que no se reconoce el comando.

### Causa
Ocurre cuando el directorio de scripts de Python (ej. `C:\Python314\Scripts\`) no está en el PATH del sistema, o la instalación de PyArmor no creó un ejecutable global.

### Solución
Usá el Builder gráfico o el script de automatización incluido:
```powershell
python build.py --name "NombreApp"
```
Alternativamente, usá el punto de entrada directo del módulo:
```powershell
python -m pyarmor.cli --version
```

---

## 2. Error de sintaxis en `pyarmor pack` (Incompatibilidad de Versión)

### Síntoma
Recibís un error de argumentos o comandos desconocidos al intentar usar `pyarmor pack`.

### Causa
**PyArmor 8.x o 9.x** cambió drásticamente el flujo de empaquetado respecto a la versión 7. El comando `pack` ya no existe igual.

### Solución para PyArmor 9+
Usá `gen --pack`:
```powershell
# Configurar opciones de PyInstaller
python -m pyarmor.cli cfg pack:pyi_options="--onefile --noconsole --name SysHealth"

# Ejecutar el empaquetado
python -m pyarmor.cli gen --pack onefile main.py
```
> La versión **Trial** tiene límites en la complejidad de los scripts que puede ofuscar.

---

## 3. El reporte no se envía (Error de Red)

### Síntoma
El script finaliza pero no recibís el mensaje en Telegram o Discord.

### Causa
Micro-cortes de internet, DNS inestable o bloqueo temporal (rate-limit) por parte de las APIs.

### Solución
La suite implementa **resiliencia de red** automática con reintentos (3 intentos con espera exponencial). Si falla después de 3 intentos, el archivo local **no se borrará** (aunque no uses `--no-wipe`) para evitar pérdida de datos. Recuperá el reporte manualmente en la carpeta `.audit/`.

---

## 4. La ventana de consola aparece brevemente al iniciar (Modo Stealth)

### Síntoma
Al ejecutar el `.exe` con el parámetro `--stealth`, la ventana de comandos se ve un segundo antes de ocultarse.

### Causa y Distinción Técnica
Hay **dos mecanismos de ocultamiento independientes**:

| Mecanismo | Nivel | Cuándo actúa | Visible al inicio |
| :--- | :--- | :--- | :--- |
| **Mostrar Consola** (desmarcado) | Compilador | Nunca crea la ventana | ❌ Nunca |
| **Modo Stealth** (`--stealth`) | Runtime | Después de importar módulos | ⚠️ Sí, ~1s |

### Solución
Para sigilo total desde el milisegundo cero: compilá con **"Mostrar Consola" desmarcado** en el Builder (genera un `Windowed App`). El flag `--stealth` es una capa de seguridad extra cuando la ventana ya fue creada, pero no reemplaza la compilación en modo silencioso.

---

## 5. Las contraseñas muestran símbolos raros o `[Error AES-GCM]`

### Síntoma
En el reporte HTML/CSV, el campo de contraseña muestra caracteres extraños, o valores como `[Error AES-GCM]`, `[Sin Llave AES]` o `[Sin Descifrar]`.

### Causa
Chromium usa **dos esquemas de cifrado diferentes** que pueden coexistir en la misma base de datos:

1. **AES-GCM (v80+)**: Los blobs tienen el prefijo `v10` y requieren la master key del `Local State`.
2. **DPAPI Legacy (<v80)**: Blobs cifrados directamente por Windows, sin prefijo.

Los marcadores de error indican:

| Marcador | Causa |
| :--- | :--- |
| `[Sin Llave AES]` | Blob `v10` pero no se pudo leer el `Local State`. |
| `[Blob Inválido]` | El blob `v10` está truncado o corrupto. |
| `[Error AES-GCM]` | La llave existe pero no descifra este blob (y DPAPI tampoco pudo). |
| `[Sin Descifrar]` | Blob legacy sin prefijo que DPAPI no puede descifrar en esta sesión. |

### Solución
1. Ejecutá con permisos de **administrador** para garantizar que DPAPI pueda acceder a las claves del usuario actual.
2. Si el navegador está abierto, usá **`--auto-kill`** para que la suite cierre el proceso y libere el bloqueo de la base de datos.
3. Si ves `[Sin Llave AES]`, el `Local State` del perfil podría estar corrupto o pertenecer a otro usuario de Windows.

---

## 6. Error "Permission Denied" al borrar logs o reportes

### Síntoma
El Dashboard o el script fallan al intentar limpiar la carpeta `.audit/` o el archivo `pentest_audit.log`.

### Causa
Windows bloquea archivos que otro proceso está escribiendo. Si una auditoría falló a mitad de camino, el manejador de logs puede haber quedado abierto.

### Solución
1. Asegurate de que no haya otra instancia corriendo (revisá el Administrador de Tareas).
2. La suite incluye un "Logger Guard" que cierra flujos antes de intentar borrar. Si el problema persiste, reiniciá la aplicación.

---

## 7. La Autodestrucción no borró el .exe

### Síntoma
Activaste `--self-destruct` pero el archivo sigue en la carpeta después de la ejecución.

### Causa
El comando `del` de Windows puede fallar si el archivo está bloqueado por:
1. El Explorador de Windows (si tenés la carpeta abierta y seleccionaste el archivo).
2. Un Antivirus que está escaneando el binario en ese momento.

### Solución
Esperá unos segundos. El comando tiene un delay de 3s para permitir que el proceso principal termine antes de borrarse. Evitá tener la carpeta de salida abierta en el explorador durante el testeo.

---

## 8. Chrome no detecta perfiles aunque están instalados (`0 perfiles encontrados`)

### Síntoma
El log muestra `Encontrados 0 perfiles para procesar.` pero tenés Chrome instalado y con contraseñas guardadas.

### Causa Posible 1 — Perfil no detectado por nombre
El detector busca carpetas llamadas `Default`, `Guest Profile`, o `Profile N`. Si tu perfil tiene otro nombre (raro, pero posible en instalaciones modificadas), no se encuentra.

### Causa Posible 2 — Base de datos vacía
La suite valida que el archivo `Login Data` tenga `size > 0`. Un perfil recién creado o sin contraseñas guardadas tiene la BD vacía y se descarta.

### Causa Posible 3 — Navegador bloqueando la BD
Chrome tiene un bloqueo exclusivo sobre `Login Data` mientras está corriendo.

### Solución
- Activá **`--auto-kill`** (o la opción equivalente en el Builder) para cerrar el navegador antes de auditar.
- Verificá manualmente que la carpeta `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data` exista y no esté vacía.

---

## 9. Error "Database is locked" (SQLite)

### Síntoma
Incluso usando `--auto-kill`, el log muestra que la base de datos `Login Data` está bloqueada y no se puede copiar.

### Causa
Esto suele ocurrir cuando un servicio de sincronización en la nube (como **OneDrive**, **Google Drive** o **Dropbox**) está intentando respaldar el perfil del navegador en ese preciso instante, manteniendo un handle abierto sobre el archivo.

### Solución
1. Pausá temporalmente la sincronización de archivos en la nube.
2. Si el problema persiste, revisá que no haya procesos "huérfanos" de Chrome o Edge en el Administrador de Tareas que `--auto-kill` no haya podido terminar (sucede a veces con subprocesos de extensiones).

---

## 10. Detección por Heurística (Falsos Positivos de AV)

### Síntoma
Tu binario ofuscado y firmado es borrado por el Antivirus inmediatamente después de generarse o al intentar ejecutarlo.

### Causa
La combinación de **empaquetado (PyInstaller)** + **ofuscación (PyArmor)** + **comportamiento de red (Webhooks)** es un patrón que los AV marcan como sospechoso por defecto (detección heurística).

### Solución
1. **No uses el nombre por defecto**: Cambiá el nombre del archivo a algo genérico como `WinSystemTray.exe`.
2. **Cambiá el Icono**: Usar el icono por defecto de Python es una bandera roja inmediata. Usá uno de una aplicación conocida.
3. **Aumentá el Delay Inicial**: Configurá un delay de al menos 30-60 segundos en el Builder. Muchos sandboxes de AV se rinden si no ven actividad en los primeros segundos.
4. **Spoofing de Metadatos**: Asegurate de completar los campos de Versión, Compañía y Descripción en el Builder para que el binario parezca legítimo.

---

## 11. El Dashboard no abre (ModuleNotFoundError)

### Síntoma
Al ejecutar `python gui_app.py`, recibís un error diciendo que no se encuentra el módulo `customtkinter` o `PIL`.

### Causa
Faltan las dependencias de la interfaz gráfica en tu entorno actual.

### Solución
Instalá el set completo de dependencias:
```powershell
pip install -r requirements.txt
```
Si el error persiste específicamente con `PIL` (Pillow), reinstalalo manualmente:
```powershell
pip install --force-reinstall Pillow
```

---

## 12. Soporte y Solución de Problemas para App-Bound Encryption v20 (Chrome, Edge, Brave)

### Síntoma
En versiones recientes de navegadores basados en Chromium (Chrome 127+, Edge 127+, Brave 130+), las credenciales pueden mostrar `[Sin Descifrar]` o arrojar logs de error específicos como:
- `Unsupported flag: 232` / `Unsupported flag: 233`
- `OpenProcess on winlogon.exe failed (Access Denied)`
- `No se pudo descifrar el blob CNG con ninguna llave conocida`

### Causa Técnica y Arquitectura V20
A partir de Chromium 127+, se introdujo **App-Bound Encryption (ABE)**. Las contraseñas y cookies ahora usan el prefijo de blob **`v20`** (en lugar de `v10` o `v11`). 
La suite **implementa soporte nativo y completo para descifrar V20** a través de una arquitectura avanzada en tres fases:

1. **Token Impersonation (SYSTEM)**: La suite busca el proceso `winlogon.exe`, duplica su token de seguridad de alto nivel (`SYSTEM`) y lo impersona para obtener privilegios criptográficos de máquina necesarios para invocar la API DPAPI de bajo nivel de Windows.
2. **Descifrado de Capas DPAPI**: Se ejecutan las APIs `CryptUnprotectData` del sistema y de usuario de forma encadenada.
3. **Mapeo de Claves y Descifrado CNG**: 
   - **Chrome / Edge**: Usan llaves resguardadas en el proveedor CNG del sistema (Microsoft Software Key Storage Provider) llamadas `Google Chromekey1` y `Microsoft Edgekey1`. El descifrado del payload AES intermedio se realiza interactuando con CNG a través de `ctypes` y aplicando una máscara XOR propietaria.
   - **Brave (v130+)**: Implementa una simplificación de seguridad. Una vez removida la capa DPAPI, el payload contiene la clave maestra AES de 256 bits cruda de **32 bytes** de manera directa (identificada con el flag `'direct'` o byte inicial `232` o `0xE8`), la cual no requiere de servicios de elevación COM intermedios ni operaciones XOR.

### Soluciones y Diagnóstico de Errores Comunes

| Error / Síntoma | Causa | Solución |
| :--- | :--- | :--- |
| `OpenProcess on winlogon.exe failed` | El script no se está ejecutando con el nivel de integridad suficiente para interactuar con los procesos del sistema. | **Ejecutá el script principal (`main.py` o `main.exe`) como Administrador.** (Clic derecho -> Ejecutar como Administrador). |
| `Unsupported flag: 232` | Estás usando una versión vieja de la suite que no soporta el parser de clave directa de Brave. | Actualizá la suite. La versión actual detecta automáticamente payloads de 32 bytes o flags directos y extrae la clave final en el acto. |
| `No se pudo descifrar el blob CNG...` | La clave de cifrado CNG o la base de datos pertenece a otro usuario de Windows o a otra instalación desvinculada. | Verificá que estés auditando sobre el usuario real que inició sesión en Windows. |
| `[Sin Descifrar]` con permisos de Admin | El servicio `ChromeElevationService` o `BraveElevationService` no está correctamente registrado en el sistema. | Comprobá en los servicios de Windows (`services.msc`) que el servicio de elevación del navegador respectivo esté habilitado y configurado en inicio manual (`Manual`). |

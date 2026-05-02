# Solución de Problemas Comunes

Este documento detalla los problemas frecuentes encontrados durante la compilación y ofuscación del proyecto y cómo resolverlos.

## 1. PyArmor: El término 'pyarmor' no se reconoce como nombre de comando

### Síntoma
Intentas ejecutar `pyarmor` y recibes un mensaje de error indicando que no se reconoce el comando.

### Causa
Esto suele ocurrir por dos razones principales:
1. El directorio de scripts de Python (ej. `C:\Python314\Scripts\`) no está correctamente agregado al PATH del sistema.
2. La instalación de PyArmor prefirió el módulo CLI directo en lugar de crear un ejecutable global.

### Solución (Mediante build.py)
Para evitar errores manuales y problemas de PATH, usa el script de automatización incluido:
```powershell
python build.py --name "NombreApp"
```

Alternativamente, puedes usar el punto de entrada directo del módulo:
```powershell
python -m pyarmor.cli --version
```

---

## 2. Error de sintaxis en `pyarmor pack` (Incompatibilidad de Versión)

### Síntoma
Recibes un error de argumentos o comandos desconocidos al intentar usar `pyarmor pack` como en versiones antiguas de tutoriales.

### Causa
Has instalado **PyArmor 8.x o 9.x**, donde el flujo de empaquetado cambió drásticamente respecto a la versión 7. El comando `pack` ya no existe de la misma forma y los parámetros han sido reestructurados.

### Solución para PyArmor 9+
Debes usar el comando `gen --pack`. A continuación se muestra cómo lograr el equivalente a un `--onefile --noconsole`:

1. **Configurar opciones de PyInstaller**:
   Define el nombre del ejecutable y las configuraciones de consola en la configuración local de PyArmor:
   ```powershell
   python -m pyarmor.cli cfg pack:pyi_options="--onefile --noconsole --name SysHealth"
   ```

2. **Ejecutar el empaquetado**:
   Genera el ejecutable pasando el parámetro `--pack`:
   ```powershell
   python -m pyarmor.cli gen --pack onefile main.py
   ```

3. **Verificación**:
   El resultado aparecerá en la carpeta `dist/`. Ten en cuenta que si usas la versión **Trial**, existen límites en la complejidad de los scripts que puedes ofuscar.

---

## 3. El reporte no se envía (Error de Red)

### Síntoma
El script finaliza pero no recibes el mensaje en Telegram o Discord.

# Solución de Problemas Comunes

Este documento detalla los problemas frecuentes encontrados durante la compilación y ofuscación del proyecto y cómo resolverlos.

## 1. PyArmor: El término 'pyarmor' no se reconoce como nombre de comando

### Síntoma
Intentas ejecutar `pyarmor` y recibes un mensaje de error indicando que no se reconoce el comando.

### Causa
Esto suele ocurrir por dos razones principales:
1. El directorio de scripts de Python (ej. `C:\Python314\Scripts\`) no está correctamente agregado al PATH del sistema.
2. La instalación de PyArmor prefirió el módulo CLI directo en lugar de crear un ejecutable global.

### Solución (Mediante build.py)
Para evitar errores manuales y problemas de PATH, usa el script de automatización incluido:
```powershell
python build.py --name "NombreApp"
```

Alternativamente, puedes usar el punto de entrada directo del módulo:
```powershell
python -m pyarmor.cli --version
```

---

## 2. Error de sintaxis en `pyarmor pack` (Incompatibilidad de Versión)

### Síntoma
Recibes un error de argumentos o comandos desconocidos al intentar usar `pyarmor pack` como en versiones antiguas de tutoriales.

### Causa
Has instalado **PyArmor 8.x o 9.x**, donde el flujo de empaquetado cambió drásticamente respecto a la versión 7. El comando `pack` ya no existe de la misma forma y los parámetros han sido reestructurados.

### Solución para PyArmor 9+
Debes usar el comando `gen --pack`. A continuación se muestra cómo lograr el equivalente a un `--onefile --noconsole`:

1. **Configurar opciones de PyInstaller**:
   Define el nombre del ejecutable y las configuraciones de consola en la configuración local de PyArmor:
   ```powershell
   python -m pyarmor.cli cfg pack:pyi_options="--onefile --noconsole --name SysHealth"
   ```

2. **Ejecutar el empaquetado**:
   Genera el ejecutable pasando el parámetro `--pack`:
   ```powershell
   python -m pyarmor.cli gen --pack onefile main.py
   ```

3. **Verificación**:
   El resultado aparecerá en la carpeta `dist/`. Ten en cuenta que si usas la versión **Trial**, existen límites en la complejidad de los scripts que puedes ofuscar.

---

## 3. El reporte no se envía (Error de Red)

### Síntoma
El script finaliza pero no recibes el mensaje en Telegram o Discord.

### Causa
Micro-cortes de internet, DNS inestable o bloqueo temporal (rate-limit) por parte de las APIs.

### Solución
La suite implementa **resiliencia de red** automática con un decorador de reintentos (3 intentos con espera exponencial). Si después de 3 intentos falla, el script **no borrará** el archivo local (aunque no uses `--no-wipe`) para asegurar que no pierdas la auditoría. Puedes recuperar el reporte manualmente en la carpeta `.audit/`.

---

## 4. La ventana de consola aparece brevemente al iniciar (Modo Stealth)

### Síntoma
Al ejecutar el script o el `.exe` con el parámetro `-s` / `--stealth`, la ventana de comandos se ve un segundo antes de ocultarse.

### Causa
Se ha diferido el ocultamiento de la consola hasta después del análisis de argumentos e importación de módulos. Esto evita que, si falta una librería crítica (como `pywin32`) en la PC de destino, el script muera silenciosamente en segundo plano.

### Solución
Es un comportamiento de diseño para garantizar la robustez. Si deseas que sea 100% invisible desde el milisegundo cero, debes compilar usando `python build.py --noconsole`.

---

## 5. Error "Permission Denied" al borrar logs o reportes

### Síntoma
El Dashboard o el script fallan al intentar limpiar la carpeta `.audit/` o el archivo `pentest_audit.log`.

### Causa
Windows bloquea los archivos que están siendo escritos por otro proceso. Si la auditoría falló a mitad de camino, es posible que el manejador de logs (logger) haya quedado abierto y bloqueando el archivo.

### Solución
1. Asegúrate de que no haya otra instancia de la suite ejecutándose en segundo plano (revisa el Administrador de Tareas).
2. La versión **1.3.0** incluye un "Logger Guard" que cierra automáticamente los flujos antes de intentar borrar. Si el problema persiste, reinicia la aplicación.

---

## 6. La Autodestrucción no borró el .exe

### Síntoma
Activaste `--self-destruct` pero el archivo sigue en la carpeta después de la ejecución.

### Causa
El comando `del` de Windows puede fallar si el archivo está siendo "observado" o bloqueado por:
1. El Explorador de Windows (si tienes la carpeta abierta y seleccionaste el archivo).
2. Un Antivirus que está escaneando el binario justo en ese momento.

### Solución
Espera unos segundos. El comando tiene un delay de 3 segundos para permitir que el proceso principal muera del todo antes de borrarse. Evita tener la carpeta de salida abierta en el explorador durante el testeo.

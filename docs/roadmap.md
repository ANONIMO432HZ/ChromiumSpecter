# 🗺️ Roadmap de Evolución - Chromium Credentials Auditor

Este documento detalla la hoja de ruta para transformar esta suite en una herramienta de nivel profesional, facilitando su uso y aumentando su efectividad en entornos reales.

---

## 🏗️ Fase 1: Facilidad de Uso (Auditor Builder)
**Objetivo:** Permitir que usuarios sin conocimientos técnicos generen binarios personalizados con "pocos clics".

- [ ] **Constructor Gráfico (GUI):** Desarrollar una interfaz en Python (Tkinter/CustomTkinter) que permita:
    - Ingresar credenciales (Telegram/Discord) de forma visual.
    - Seleccionar íconos personalizados (.ico).
    - Configurar flags (Stealth, No-Wipe, etc.) mediante checkboxes.
    - Botón único de "Build" que automatice el flujo de ofuscación y compilación.
- [ ] **Generador de Configuraciones:** El builder debe codificar automáticamente las credenciales en Base64 para evitar que queden en texto plano dentro del código fuente.

## 🌐 Fase 2: Cobertura Universal (Soporte Gecko)
**Objetivo:** No limitar la auditoría solo a navegadores basados en Chromium.

- [ ] **Soporte para Firefox:** Implementar la lógica de descifrado para perfiles de Mozilla (basados en `key4.db` y `logins.json`).
- [ ] **Soporte para Thunderbird:** Extender la auditoría a gestores de correo electrónico populares.

## 🕵️ Fase 3: Evasión y Sigilo Avanzado
**Objetivo:** Aumentar la tasa de éxito y la persistencia del sigilo frente a analistas y sistemas de seguridad.

- [ ] **Detección de Anti-Análisis (Anti-VM/Sandbox):**
    - Verificar nombres de dispositivos, drivers y MAC addresses comunes en entornos virtuales (VirtualBox, VMware, QEMU).
    - Abortar ejecución si se detectan sandboxes de análisis dinámico (Any.run, JoeSandbox).
- [ ] **Spoofing de Metadatos de Archivo:**
    - Clonar metadatos (Versión, Compañía, Descripción) de binarios legítimos del sistema (ej. `svchost.exe`, `chrome_updater.exe`).
- [ ] **Carga Dinámica de DLLs:** Refinar aún más cómo se cargan las dependencias de sistema para evitar firmas estáticas de importación.

## 📊 Fase 4: Reportes y Post-Exfiltración
**Objetivo:** Mejorar la calidad de los datos obtenidos y su gestión.

- [ ] **Captura de Capturas de Pantalla:** Opción para adjuntar una captura de pantalla del sistema en el momento de la auditoría.
- [ ] **Panel de Control Web (Opcional):** Un backend centralizado para recibir y visualizar reportes de múltiples fuentes de forma organizada.

---

> [!TIP]
> Prioridad Sugerida: **Fase 1 (Builder)** > **Fase 2 (Firefox)** > **Fase 3 (Evasión)**.

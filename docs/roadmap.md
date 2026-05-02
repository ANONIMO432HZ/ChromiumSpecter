# 🗺️ Roadmap de Evolución - ChromiumSpecter

Este documento detalla la hoja de ruta para transformar esta suite en una herramienta de nivel profesional, facilitando su uso y aumentando su efectividad en entornos reales.

---

## 🏗️ Fase 1: Facilidad de Uso (Auditor Builder)

**Objetivo:** Permitir que usuarios sin conocimientos técnicos generen binarios personalizados con "pocos clics".

- [x] **Modularización del Core CLI:**
  - ✅ **Completado:** `main.py` refactorizado como un motor (Core) independiente de la UI.
  - ✅ **Parámetros Extendidos:** Añadidos filtros por navegador, soporte JSON, delays evasivos y control de directorios.
- [x] **Constructor Gráfico (GUI):** Desarrollar una interfaz en Python (CustomTkinter) que permita:
  - Ingresar credenciales (Telegram/Discord) de forma visual.
  - Seleccionar íconos personalizados (.ico).
  - Configurar flags (Stealth, No-Wipe, etc.) mediante checkboxes.
  - ✅ **Completado:** Botón único de "Build" que automatiza el flujo de ofuscación y compilación.
- [x] **Anti-Forensics Nativo:**
  - ✅ **Completado:** Protocolo de Autodestrucción (Self-Delete) tras exfiltración exitosa.
  - ✅ **Completado:** Limpieza profunda de temporales y bloqueos de I/O de logs.

## 🌐 Fase 2: Cobertura Universal (Soporte Gecko)

**Objetivo:** No limitar la auditoría solo a navegadores basados en Chromium.

- [ ] **Soporte para Firefox:** Implementar la lógica de descifrado para perfiles de Mozilla (basados en `key4.db` y `logins.json`).
- [ ] **Soporte para Thunderbird:** Extender la auditoría a gestores de correo electrónico populares.

## 🕵️ Fase 3: Evasión y Sigilo Avanzado

**Objetivo:** Aumentar la tasa de éxito y la persistencia del sigilo frente a analistas y sistemas de seguridad.

- [ ] **Detección de Anti-Análisis Proactiva (Anti-VM/Sandbox):**
  - Verificar nombres de dispositivos, drivers y MAC addresses comunes en entornos virtuales (VirtualBox, VMware, QEMU).
  - Abortar ejecución si se detectan sandboxes de análisis dinámico.
- [x] **Spoofing de Metadatos de Archivo:**
  - ✅ **Completado:** Inyección de CompanyName, FileDescription, etc. via Dashboard.
- [x] **Evasión de Tráfico:**
  - ✅ **Completado:** Implementación de Delays entre envíos para aplanar la firma de red.

## 📊 Fase 4: Reportes y Post-Exfiltración

**Objetivo:** Mejorar la calidad de los datos obtenidos y su gestión.

- [ ] **Captura de Capturas de Pantalla:** Opción para adjuntar una captura de pantalla del sistema en el momento de la auditoría.
- [ ] **Panel de Control Web (Opcional):** Un backend centralizado para recibir y visualizar reportes de múltiples fuentes.

---

> [!TIP]
> Prioridad Actual: **Soporte Gecko (Firefox)** > **Anti-VM/Sandbox**.

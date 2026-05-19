import json
import base64
from pathlib import Path
from unittest.mock import MagicMock, patch
from main import ChromiumDecryptor

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_blob(prefix=b"v10", nonce_fill=b"A", payload=b"encrypted", tag_fill=b"B"):
    return prefix + nonce_fill * 12 + payload + tag_fill * 16

# ── get_key ───────────────────────────────────────────────────────────────────

def test_get_keys_returns_aes_key(mocker):
    """Extrae y descifra la master key AES del Local State."""
    decryptor = ChromiumDecryptor()
    fake_local_state = {
        "os_crypt": {
            "encrypted_key": base64.b64encode(b"DPAPI" + b"encrypted_key_data").decode()
        }
    }
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps(fake_local_state)))
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"decrypted_master_key"))

    keys, dpapi_ok = decryptor.get_keys(Path("C:/Fake/Path"))

    assert keys.get("v10") == b"decrypted_master_key"
    assert dpapi_ok is True

def test_get_keys_no_local_state_returns_dpapi_only(mocker):
    """Sin Local State el perfil sigue siendo válido en modo DPAPI."""
    decryptor = ChromiumDecryptor()
    mocker.patch("pathlib.Path.exists", return_value=False)

    keys, dpapi_ok = decryptor.get_keys(Path("C:/NoExists"))

    assert not keys
    assert dpapi_ok is True  # win32crypt sí está disponible

def test_get_keys_missing_os_crypt_returns_dpapi_only(mocker):
    """Local State sin os_crypt → modo DPAPI (perfil muy antiguo)."""
    decryptor = ChromiumDecryptor()
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps({})))
    mocker.patch("pathlib.Path.exists", return_value=True)

    keys, dpapi_ok = decryptor.get_keys(Path("C:/Fake"))

    assert "v10" not in keys
    assert "v20" not in keys
    assert dpapi_ok is True

# ── decrypt: AES-GCM ──────────────────────────────────────────────────────────

def test_decrypt_aes_gcm_success(mocker):
    """Blob v10 con llave correcta → texto plano."""
    decryptor = ChromiumDecryptor()
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.return_value = b"my_password"
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)

    result = decryptor.decrypt(_make_blob(), {"v10": b"fake_aes_key_32b"})

    assert result == "my_password"
    mock_cipher.decrypt_and_verify.assert_called_once()

def test_decrypt_aes_gcm_no_key():
    """Blob v10 sin llave → marcador descriptivo, nunca basura."""
    decryptor = ChromiumDecryptor()
    result = decryptor.decrypt(_make_blob(), {})
    assert result == "[Sin Llave AES]"

def test_decrypt_aes_gcm_too_short():
    """Blob v10 demasiado corto (< 31 bytes) → marcador, no excepción."""
    decryptor = ChromiumDecryptor()
    result = decryptor.decrypt(b"v10" + b"x" * 5, {"v10": b"fake_key"})
    assert result == "[Blob Inválido]"

def test_decrypt_aes_gcm_fails_falls_back_to_dpapi(mocker):
    """AES-GCM falla → intenta DPAPI como último recurso."""
    decryptor = ChromiumDecryptor()
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.side_effect = Exception("MAC check failed")
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"dpapi_recovered"))

    result = decryptor.decrypt(_make_blob(), {"v10": b"wrong_key"})

    assert result == "dpapi_recovered"

def test_decrypt_aes_gcm_fails_and_dpapi_fails_returns_marker(mocker):
    """AES-GCM y DPAPI fallan → marcador '[Error AES-GCM]', nunca basura."""
    decryptor = ChromiumDecryptor()
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.side_effect = Exception("MAC check failed")
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)
    mocker.patch("win32crypt.CryptUnprotectData", side_effect=Exception("DPAPI failed too"))

    result = decryptor.decrypt(_make_blob(), {"v10": b"wrong_key"})

    assert result == "[Error AES-GCM]"

# ── decrypt: DPAPI Legacy ─────────────────────────────────────────────────────

def test_decrypt_dpapi_legacy_success(mocker):
    """Blob sin prefijo v10 → DPAPI directamente."""
    decryptor = ChromiumDecryptor()
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"legacy_pass"))

    result = decryptor.decrypt(b"\x01\x00\x00\x00somebinaryblob", {})

    assert result == "legacy_pass"

def test_decrypt_dpapi_legacy_fails_returns_marker(mocker):
    """Blob legacy + DPAPI falla → '[Sin Descifrar]'."""
    decryptor = ChromiumDecryptor()
    mocker.patch("win32crypt.CryptUnprotectData", side_effect=Exception("DPAPI error"))

    result = decryptor.decrypt(b"\x01\x00\x00somebinaryblob", {})

    assert result == "[Sin Descifrar]"

# ── decrypt: Casos Límite ─────────────────────────────────────────────────────

def test_decrypt_none_blob():
    """None siempre retorna '' sin tocar nada."""
    assert ChromiumDecryptor().decrypt(None, {}) == ""

def test_decrypt_mixed_profile_scenario(mocker):
    """
    Un perfil migrado puede tener entradas DPAPI y AES en la misma BD.
    decrypt() debe manejar cada blob independientemente.
    """
    decryptor = ChromiumDecryptor()
    
    # AES blob
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.return_value = b"aes_pass"
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"dpapi_pass"))

    aes_result  = decryptor.decrypt(_make_blob(b"v10"), {"v10": b"aes_key"})
    dpapi_result = decryptor.decrypt(b"\x01\x00\x00\x00legacy", {})

    assert aes_result  == "aes_pass"
    assert dpapi_result == "dpapi_pass"

# ── v20_decryptor ─────────────────────────────────────────────────────────────

def test_v20_token_manager_revert_to_self(mocker):
    """Verifica que RevertToSelf se llame siempre, incluso si Impersonate falla."""
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.get_winlogon_pid", return_value=1234)
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.OpenProcessToken", return_value=1)
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.LookupPrivilegeValueW", return_value=1)
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.AdjustTokenPrivileges", return_value=1)
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.kernel32.OpenProcess", return_value=1)
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.DuplicateTokenEx", return_value=1)
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.kernel32.CloseHandle")
    
    mock_impersonate = mocker.patch("modules.chrome_v20_decryption.v20_decryptor.ImpersonateLoggedOnUser", return_value=0) # Fails
    mock_revert = mocker.patch("modules.chrome_v20_decryption.v20_decryptor.RevertToSelf")

    from modules.chrome_v20_decryption.v20_decryptor import TokenManager

    try:
        with TokenManager():
            pass
    except Exception as e:
        assert "ImpersonateLoggedOnUser failed" in str(e)
        
    # RevertToSelf shouldn't be called if impersonated was False
    mock_revert.assert_not_called()

    mock_impersonate.return_value = 1 # Succeeds
    try:
        with TokenManager():
            raise ValueError("Some internal error")
    except ValueError:
        pass
        
    mock_revert.assert_called_once()

def test_get_v20_key_flag_3(mocker):
    """Verifica el flujo doble DPAPI y XOR para flag 3."""
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.TokenManager.__enter__")
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.TokenManager.__exit__")
    
    mock_win32crypt = MagicMock()
    # First unprotect returns fake system blob
    # Second unprotect returns parsed data structure (header len 0, content len 0, flag 3, AES key 32b, IV 12b, cipher 32b, tag 16b)
    
    # 4 bytes header len, 0 bytes header
    # 4 bytes content len
    # 1 byte flag = 3
    # 32 bytes encrypted_aes_key
    # 12 bytes iv
    # 32 bytes ciphertext
    # 16 bytes tag
    import struct
    fake_parsed_blob = struct.pack('<I', 0) + struct.pack('<I', 93) + b'\x03' + (b'K' * 32) + (b'I' * 12) + (b'C' * 32) + (b'T' * 16)
    
    mock_win32crypt.CryptUnprotectData.side_effect = [
        (None, b"system_decrypted"),
        (None, fake_parsed_blob)
    ]
    
    mocker.patch("modules.chrome_v20_decryption.v20_decryptor.decrypt_with_cng", return_value=(b'D' * 32))
    
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.return_value = b"final_aes_master_key"
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)

    from modules.chrome_v20_decryption.v20_decryptor import get_v20_key
    fake_app_bound = base64.b64encode(b"APPB" + b"encrypted_key").decode()
    
    result = get_v20_key(fake_app_bound, mock_win32crypt)
    
    assert result == b"final_aes_master_key"
    mock_cipher.decrypt_and_verify.assert_called_once_with(b'C' * 32, b'T' * 16)

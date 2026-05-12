import json
import base64
from pathlib import Path
from unittest.mock import MagicMock, patch
from main import ChromiumDecryptor

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_blob(prefix=b"v10", nonce_fill=b"A", payload=b"encrypted", tag_fill=b"B"):
    return prefix + nonce_fill * 12 + payload + tag_fill * 16

# ── get_key ───────────────────────────────────────────────────────────────────

def test_get_key_returns_aes_key(mocker):
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

    aes_key, dpapi_ok = decryptor.get_key(Path("C:/Fake/Path"))

    assert aes_key == b"decrypted_master_key"
    assert dpapi_ok is True

def test_get_key_no_local_state_returns_dpapi_only(mocker):
    """Sin Local State el perfil sigue siendo válido en modo DPAPI."""
    decryptor = ChromiumDecryptor()
    mocker.patch("pathlib.Path.exists", return_value=False)

    aes_key, dpapi_ok = decryptor.get_key(Path("C:/NoExists"))

    assert aes_key is None
    assert dpapi_ok is True  # win32crypt sí está disponible

def test_get_key_missing_os_crypt_returns_dpapi_only(mocker):
    """Local State sin os_crypt → modo DPAPI (perfil muy antiguo)."""
    decryptor = ChromiumDecryptor()
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps({})))
    mocker.patch("pathlib.Path.exists", return_value=True)

    aes_key, dpapi_ok = decryptor.get_key(Path("C:/Fake"))

    assert aes_key is None
    assert dpapi_ok is True

# ── decrypt: AES-GCM ──────────────────────────────────────────────────────────

def test_decrypt_aes_gcm_success(mocker):
    """Blob v10 con llave correcta → texto plano."""
    decryptor = ChromiumDecryptor()
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.return_value = b"my_password"
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)

    result = decryptor.decrypt(_make_blob(), b"fake_aes_key_32b")

    assert result == "my_password"
    mock_cipher.decrypt_and_verify.assert_called_once()

def test_decrypt_aes_gcm_no_key():
    """Blob v10 sin llave → marcador descriptivo, nunca basura."""
    decryptor = ChromiumDecryptor()
    result = decryptor.decrypt(_make_blob(), None)
    assert result == "[Sin Llave AES]"

def test_decrypt_aes_gcm_too_short():
    """Blob v10 demasiado corto (< 31 bytes) → marcador, no excepción."""
    decryptor = ChromiumDecryptor()
    result = decryptor.decrypt(b"v10" + b"x" * 5, b"fake_key")
    assert result == "[Blob Inválido]"

def test_decrypt_aes_gcm_fails_falls_back_to_dpapi(mocker):
    """AES-GCM falla → intenta DPAPI como último recurso."""
    decryptor = ChromiumDecryptor()
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.side_effect = Exception("MAC check failed")
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"dpapi_recovered"))

    result = decryptor.decrypt(_make_blob(), b"wrong_key")

    assert result == "dpapi_recovered"

def test_decrypt_aes_gcm_fails_and_dpapi_fails_returns_marker(mocker):
    """AES-GCM y DPAPI fallan → marcador '[Error AES-GCM]', nunca basura."""
    decryptor = ChromiumDecryptor()
    mock_cipher = MagicMock()
    mock_cipher.decrypt_and_verify.side_effect = Exception("MAC check failed")
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)
    mocker.patch("win32crypt.CryptUnprotectData", side_effect=Exception("DPAPI failed too"))

    result = decryptor.decrypt(_make_blob(), b"wrong_key")

    assert result == "[Error AES-GCM]"

# ── decrypt: DPAPI Legacy ─────────────────────────────────────────────────────

def test_decrypt_dpapi_legacy_success(mocker):
    """Blob sin prefijo v10 → DPAPI directamente."""
    decryptor = ChromiumDecryptor()
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"legacy_pass"))

    result = decryptor.decrypt(b"\x01\x00\x00\x00somebinaryblob", None)

    assert result == "legacy_pass"

def test_decrypt_dpapi_legacy_fails_returns_marker(mocker):
    """Blob legacy + DPAPI falla → '[Sin Descifrar]'."""
    decryptor = ChromiumDecryptor()
    mocker.patch("win32crypt.CryptUnprotectData", side_effect=Exception("DPAPI error"))

    result = decryptor.decrypt(b"\x01\x00\x00somebinaryblob", None)

    assert result == "[Sin Descifrar]"

# ── decrypt: Casos Límite ─────────────────────────────────────────────────────

def test_decrypt_none_blob():
    """None siempre retorna '' sin tocar nada."""
    assert ChromiumDecryptor().decrypt(None, b"key") == ""

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

    aes_result  = decryptor.decrypt(_make_blob(b"v10"), b"aes_key")
    dpapi_result = decryptor.decrypt(b"\x01\x00\x00\x00legacy", None)

    assert aes_result  == "aes_pass"
    assert dpapi_result == "dpapi_pass"

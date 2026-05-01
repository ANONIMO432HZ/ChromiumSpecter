import json
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock
from main import ChromiumDecryptor

def test_decrypt_aes_gcm(mocker):
    """Test AES-GCM decryption logic with mocked AES."""
    decryptor = ChromiumDecryptor()
    
    # Mock AES.new
    mock_cipher = MagicMock()
    mock_cipher.decrypt.return_value = b"decrypted_password"
    mocker.patch("Cryptodome.Cipher.AES.new", return_value=mock_cipher)
    
    key = b"fake_key_32_bytes_long_012345678"
    # Blob: prefix(3) + nonce(12) + payload + tag(16)
    fake_blob = b"v10" + b"A" * 12 + b"encrypted" + b"B" * 16
    
    result = decryptor.decrypt(fake_blob, key)
    
    assert result == "decrypted_password"
    mock_cipher.decrypt.assert_called_once()

def test_get_key_from_local_state(mocker):
    """Test extracting and decrypting the master key from Local State JSON."""
    decryptor = ChromiumDecryptor()
    
    fake_local_state = {
        "os_crypt": {
            "encrypted_key": base64.b64encode(b"DPAPI" + b"encrypted_key_data").decode()
        }
    }
    
    # Mock open and json.load
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps(fake_local_state)))
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    # Mock win32crypt.CryptUnprotectData to return the "decrypted" master key
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"decrypted_master_key"))
    
    key = decryptor.get_key(Path("C:/Fake/Path"))
    
    assert key == b"decrypted_master_key"

def test_decrypt_empty_blob():
    """Test handling of empty or too short blobs."""
    decryptor = ChromiumDecryptor()
    assert decryptor.decrypt(None, b"key") == ""
    assert decryptor.decrypt(b"ab", b"key") == "[Error: Dato muy corto]"

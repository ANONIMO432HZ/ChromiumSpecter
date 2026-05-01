# Design: setup-pytest-with-mocking

## Technical Approach
We will use `pytest` as the test runner and `unittest.mock` (standard library) for isolation.

### Mocking Strategy
- **File System**: Mock `pathlib.Path.exists` and `pathlib.Path.iterdir` to simulate the presence of browser profiles without actually looking at the disk.
- **SQLite**: Mock `sqlite3.connect` to return a mock connection object with a pre-populated list of results for the `logins` query.
- **DPAPI**: Mock `win32crypt.CryptUnprotectData` to return a fixed master key or decrypted value.
- **Network**: Mock `requests.post` to avoid actual outgoing calls.

### File Structure
```
tests/
├── conftest.py       # Global fixtures and auto-applied mocks
├── test_decryptor.py  # Tests for ChromiumDecryptor
└── test_exfiltration.py # Tests for Exfiltrator
```

### Dependency Injection
The current `ChromiumDecryptor` and `Exfiltrator` classes hardcode some paths and values. We might need to adjust them slightly or rely heavily on patching `os.environ` and `Path` calls.

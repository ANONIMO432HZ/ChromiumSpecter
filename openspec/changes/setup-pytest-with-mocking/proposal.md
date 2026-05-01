# Proposal: Setup Pytest with Safe Mocking

## Intent
Configure a robust testing environment using `pytest` that ensures zero interaction with the local machine's real browser data or external network services. This protects the developer's privacy and prevents accidental data exfiltration during development.

## Scope
### In Scope
- Install `pytest` and `pytest-mock`.
- Implement unit tests for `ChromiumDecryptor.decrypt`.
- Implement unit tests for `ChromiumDecryptor.audit` using mocked file system and sqlite3.
- Implement unit tests for `Exfiltrator` using mocked `requests`.
- Setup `conftest.py` with global mocks.

### Out of Scope
- Integration tests with real browsers.
- End-to-end tests involving real Telegram/Discord accounts.

## Approach
- Use `unittest.mock` and `pytest-mock` to intercept all OS and network calls.
- Create a `requirements-dev.txt` for testing dependencies.
- Add a `pytest.ini` for configuration.

# Specs: setup-pytest-with-mocking

## Requirement: Safety Isolation
- **GIVEN** the test suite is running
- **WHEN** any file system operation is called (`pathlib.Path`, `shutil`, `os`)
- **THEN** it MUST be intercepted by a mock to prevent reading real browser data.
- **AND** it MUST NOT touch any file outside the temporary test directory.

## Requirement: Decryption Logic Verification
- **GIVEN** a known master key and an encrypted blob
- **WHEN** `ChromiumDecryptor.decrypt` is called
- **THEN** it MUST return the correct plaintext using the mocked AES implementation.
- **AND** it MUST handle cases where the key is missing or invalid gracefully.

## Requirement: Network Isolation
- **GIVEN** an exfiltration attempt
- **WHEN** `Exfiltrator.send_to_telegram` or `Exfiltrator.send_to_discord` is called
- **THEN** it MUST use a mocked `requests.post` call.
- **AND** it MUST verify that the payload sent to the mock matches the expected format.

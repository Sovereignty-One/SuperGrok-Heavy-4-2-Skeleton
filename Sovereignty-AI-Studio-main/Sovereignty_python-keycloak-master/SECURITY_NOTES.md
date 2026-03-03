# Security Updates

## Vulnerability Fixes Applied

This document tracks security vulnerabilities that have been fixed in the extracted python-keycloak library.

### 1. Cryptography Library - Subgroup Attack Vulnerability
- **Package**: `cryptography`
- **Vulnerable Version**: 46.0.3 (and ≤ 46.0.4)
- **Fixed Version**: 46.0.5
- **CVE/Issue**: Subgroup Attack Due to Missing Subgroup Validation for SECT Curves
- **Severity**: High
- **Fix Date**: 2026-02-11
- **Action Taken**: Updated `pyproject.toml` and `poetry.lock` to require `cryptography >= 46.0.5`

### 2. Wheel Library - Path Traversal Vulnerability
- **Package**: `wheel`
- **Vulnerable Version**: 0.45.1 (≥ 0.40.0, ≤ 0.46.1)
- **Fixed Version**: 0.46.2
- **CVE/Issue**: Arbitrary File Permission Modification via Path Traversal in wheel unpack
- **Severity**: Medium
- **Fix Date**: 2026-02-11
- **Action Taken**: Updated `pyproject.toml` and `poetry.lock` to require `wheel >= 0.46.2`

## Note on Poetry Lock File

The `poetry.lock` file has been manually updated to reflect the security patches. For a production deployment, it is recommended to:

1. Install Poetry: `pip install poetry`
2. Regenerate the lock file: `poetry lock --no-update`
3. Verify all dependencies: `poetry install`

This will ensure all cryptographic hashes in the lock file are accurate and verifiable.

## References

- Cryptography security advisories: https://github.com/pyca/cryptography/security/advisories
- Wheel security advisories: https://github.com/pypa/wheel/security/advisories

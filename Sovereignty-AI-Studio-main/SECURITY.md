# Security Policy

## Overview

SuperGrok-Hevy-Skeleton is a sovereign AI platform designed with security as a first-class priority. This document outlines the security measures implemented in the platform and provides guidance for reporting vulnerabilities.

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.0.x   | :white_check_mark: | Active           |
| < 1.0   | :x:                | Not Supported    |

## Security Features

### 1. Authentication & Authorization

#### Password Security
- **Strong Password Requirements**: Minimum 8 characters with uppercase, lowercase, digits, and special characters
- **Bcrypt Hashing**: Industry-standard password hashing with automatic salt generation
- **Password Validation**: Server-side validation prevents weak passwords

#### JWT Token Management
- **HS256 Algorithm**: Secure HMAC-SHA256 signature algorithm
- **Token Expiration**: 30-minute access tokens by default
- **Token Refresh**: Refresh token mechanism to maintain sessions securely
- **Secret Key Validation**: Minimum 32-character secret key requirement

#### Access Control
- **Bearer Token Authentication**: Secure token-based authentication
- **Protected Endpoints**: All sensitive endpoints require authentication
- **Field Whitelisting**: User updates restricted to safe fields only
- **Session Management**: Proper session handling with automatic cleanup

### 2. Input Validation & Sanitization

#### Username Validation
- 3-20 characters length requirement
- Alphanumeric with hyphens and underscores only
- Regex pattern enforcement: `^[a-zA-Z0-9_-]+$`

#### Email Validation
- EmailStr validation using Pydantic
- Format verification
- Duplicate prevention

#### Content Sanitization
- **Bio Field**: XSS-dangerous characters removed (`<>'"&`)
- **Avatar URLs**: Scheme validation (http/https only)
- **JavaScript/Data URL Prevention**: Blocks `javascript:` and `data:` schemes

### 3. Security Middleware

#### Rate Limiting
- **Implementation**: SlowAPI rate limiter
- **Default Limits**: 100 requests per 60 seconds
- **Brute Force Prevention**: Protects login endpoints from attacks
- **Configurable**: Adjustable per-environment settings

#### Security Headers
All responses include the following security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| X-Frame-Options | DENY | Prevents clickjacking attacks |
| X-Content-Type-Options | nosniff | Prevents MIME type sniffing |
| X-XSS-Protection | 1; mode=block | Enables browser XSS protection |
| Content-Security-Policy | default-src 'self' | Restricts resource loading |
| Referrer-Policy | strict-origin-when-cross-origin | Controls referrer information |
| Permissions-Policy | geolocation=(), microphone=(), camera=() | Restricts browser features |
| Strict-Transport-Security | (HTTPS only) | Enforces HTTPS connections |

#### Request Size Limiting
- **Default Limit**: 10MB per request
- **DOS Prevention**: Protects against large payload attacks
- **HTTP 413 Response**: Clear error for oversized requests

#### CORS Configuration
- **Environment-Based Origins**: Configurable allowed origins
- **Credentials Support**: Proper credential handling
- **Method Restrictions**: Limited to GET, POST, PUT, DELETE, PATCH
- **No Wildcard**: Explicit origin specification required

### 4. Error Handling

#### Secure Error Messages
- **No Information Leakage**: Internal errors don't expose system details
- **Generic Messages**: Authentication failures use consistent messaging
- **HTTP Status Codes**: Proper status codes for all error conditions
- **Exception Sanitization**: Stack traces never exposed to clients

### 5. Database Security

#### SQL Injection Prevention
- **SQLAlchemy ORM**: Parameterized queries by default
- **Text() Wrapper**: Safe SQL execution when needed
- **No String Concatenation**: All queries use parameter binding

#### Connection Security
- **Connection Pooling**: Efficient and secure connection management
- **Credential Protection**: Database credentials in environment variables
- **Session Management**: Automatic session cleanup

### 6. Cryptography

#### Hashing
- **Bcrypt**: Password hashing (work factor configurable)
- **BLAKE3**: Available for high-performance hashing needs
- **Post-Quantum Ready**: PQCrypto library included for future-proofing

#### Token Security
- **HMAC Signing**: JWT tokens signed with HMAC-SHA256
- **Secret Key Requirements**: Minimum 32-byte entropy
- **No Algorithm Confusion**: Algorithm explicitly specified

### 7. Monitoring & Auditing

#### Request Monitoring
- **Process Time Tracking**: X-Process-Time header on all responses
- **Request Logging**: All requests logged with relevant metadata
- **Performance Metrics**: Built-in timing for security analysis

#### Future Audit Features (Planned)
- Authentication attempt logging
- Failed login tracking
- Privilege escalation detection
- Suspicious activity alerts

## Configuration Security

### Environment Variables

All sensitive configuration must be stored in environment variables, never in code:

```env
SECRET_KEY=<strong-random-32+-character-key>
DATABASE_URL=postgresql://user:password@host:port/db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=<api-key-if-needed>
```

### Secret Key Generation

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Production Checklist

- [ ] DEBUG set to `false`
- [ ] Strong SECRET_KEY (32+ characters)
- [ ] HTTPS enabled with HSTS headers
- [ ] Database uses strong credentials
- [ ] Redis authentication enabled
- [ ] CORS_ORIGINS restricted to trusted domains
- [ ] Rate limiting enabled
- [ ] File uploads validated (if enabled)
- [ ] Monitoring and logging configured
- [ ] Regular security updates applied

## Known Security Considerations

### 1. Database Initialization Endpoint
- The `/api/v1/test/init-db` endpoint is protected but dangerous
- Should only be used during initial setup
- Consider removing in production or adding role-based access control

### 2. OpenAI API Key
- Stored in environment variables
- Consider using a secrets manager (HashiCorp Vault, AWS Secrets Manager)
- Rotate regularly

### 3. Redis Security
- Ensure Redis authentication is enabled
- Use TLS for Redis connections in production
- Don't expose Redis port publicly

## Reporting a Vulnerability

### Where to Report

If you discover a security vulnerability in SuperGrok-Hevy-Skeleton, please report it responsibly:

1. **Email**: Send details to the project maintainers (contact information in README.md)
2. **GitHub Security Advisories**: Use GitHub's private vulnerability reporting
3. **Encrypted Communication**: PGP key available on request for sensitive disclosures

### What to Include

Please include the following in your report:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and severity assessment
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Proof of Concept**: Code or screenshots demonstrating the vulnerability
- **Suggested Fix**: If you have ideas for remediation
- **Disclosure Timeline**: Your preferred disclosure timeline

### Response Timeline

- **Acknowledgment**: Within 48 hours of report
- **Initial Assessment**: Within 7 days
- **Fix Development**: Based on severity (critical issues within 30 days)
- **Public Disclosure**: Coordinated disclosure after fix is available

### Scope

**In Scope:**
- Authentication and authorization bypasses
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) vulnerabilities
- CSRF (Cross-Site Request Forgery) vulnerabilities
- Sensitive data exposure
- Server-side request forgery (SSRF)
- Remote code execution
- Denial of service vulnerabilities

**Out of Scope:**
- Social engineering attacks
- Physical security issues
- Issues in third-party dependencies (report to respective projects)
- Issues requiring physical access to the server

## Security Updates

Security updates are released as patches to supported versions. Subscribe to:

- GitHub Security Advisories for this repository
- GitHub Releases for update notifications
- Project issue tracker for security-related discussions

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/latest/core/security.html)

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (with permission).

---

**Last Updated**: February 11, 2026  
**Version**: 1.0.0  
**Contact**: See README.md for contact information

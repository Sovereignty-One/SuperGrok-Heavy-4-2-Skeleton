# Deployment Security Checklist

This checklist ensures that SuperGrok-Hevy-Skeleton is deployed securely in production environments.

## Pre-Deployment Security Checklist

### 1. Environment Configuration

#### Required Actions
- [ ] Set `DEBUG=false` in production
- [ ] Generate and set a strong `SECRET_KEY` (minimum 32 characters)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Configure strong database credentials
- [ ] Enable Redis authentication
- [ ] Set appropriate `CORS_ORIGINS` (only trusted domains)
- [ ] Review and set rate limiting parameters
- [ ] Configure `MAX_REQUEST_SIZE` appropriately
- [ ] Remove or secure the `.env` file (never commit to repository)

#### Verification
```bash
# Verify DEBUG is false
grep "DEBUG=false" .env

# Verify SECRET_KEY is strong
grep "SECRET_KEY=" .env | wc -c  # Should be > 43 characters
```

### 2. HTTPS and TLS

#### Required Actions
- [ ] Obtain SSL/TLS certificate (Let's Encrypt, commercial CA)
- [ ] Configure web server (Nginx/Apache) to use HTTPS
- [ ] Redirect all HTTP traffic to HTTPS
- [ ] Enable HSTS header in production
  - Uncomment HSTS header in `backend/app/main.py`
- [ ] Verify TLS 1.2 or higher is enforced
- [ ] Disable weak cipher suites

#### Verification
```bash
# Test SSL configuration
curl -I https://your-domain.com

# Verify HSTS header
curl -I https://your-domain.com | grep -i strict-transport-security

# Test SSL Labs
# https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

### 3. Database Security

#### Required Actions
- [ ] Use strong database password (20+ characters)
- [ ] Enable SSL/TLS for database connections
- [ ] Restrict database access to application servers only
- [ ] Implement regular database backups
- [ ] Enable database query logging (for audit)
- [ ] Set up database firewall rules
- [ ] Use separate database user for application (not root/admin)
- [ ] Grant minimal required permissions to database user

#### Verification
```bash
# Test database connection with SSL
psql "postgresql://user:pass@host:5432/db?sslmode=require"

# Verify user permissions
psql -U app_user -d creativeflow_db -c "\du"
```

### 4. Redis Security

#### Required Actions
- [ ] Enable Redis authentication (`requirepass`)
- [ ] Bind Redis to localhost or private network only
- [ ] Disable dangerous Redis commands (`FLUSHALL`, `CONFIG`)
- [ ] Enable Redis TLS/SSL
- [ ] Set appropriate `maxmemory` policy
- [ ] Configure Redis password in `REDIS_URL`

#### Configuration Example
```conf
# redis.conf
requirepass your-strong-redis-password
bind 127.0.0.1
rename-command FLUSHALL ""
rename-command CONFIG ""
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 5. Firewall and Network Security

#### Required Actions
- [ ] Configure firewall to allow only necessary ports
  - Port 443 (HTTPS) - Public
  - Port 80 (HTTP) - Public (redirect to 443)
  - Port 22 (SSH) - Restricted IPs only
  - Port 5432 (PostgreSQL) - Private network only
  - Port 6379 (Redis) - Private network only
- [ ] Implement IP whitelisting for admin endpoints
- [ ] Use VPC/private network for inter-service communication
- [ ] Enable DDoS protection (Cloudflare, AWS Shield)
- [ ] Set up rate limiting at reverse proxy level

#### Verification
```bash
# Check open ports
nmap -sV your-server-ip

# Should only show 80 and 443 publicly
```

### 6. Authentication & Authorization

#### Required Actions
- [ ] Verify password strength requirements are enforced
- [ ] Test JWT token expiration
- [ ] Implement token refresh mechanism
- [ ] Add role-based access control (RBAC) if needed
- [ ] Enable multi-factor authentication (MFA) for admin accounts
- [ ] Set up session timeout
- [ ] Implement account lockout after failed login attempts

#### Test Cases
```bash
# Test weak password rejection
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"weak"}'
# Should return 422 validation error

# Test rate limiting on login
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -d "username=test&password=wrong"
done
# Should eventually return 429 Too Many Requests
```

### 7. Input Validation

#### Required Actions
- [ ] Verify all user inputs are validated
- [ ] Test XSS prevention in bio and profile fields
- [ ] Test SQL injection prevention
- [ ] Verify file upload validation (if enabled)
- [ ] Test maximum request size enforcement
- [ ] Verify URL validation for avatar URLs

#### Test Cases
```bash
# Test XSS in bio
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bio":"<script>alert(1)</script>"}'
# Bio should be sanitized in response

# Test dangerous URL schemes
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"avatar_url":"javascript:alert(1)"}'
# Should return 422 validation error
```

### 8. Logging and Monitoring

#### Required Actions
- [ ] Enable application logging
- [ ] Set up centralized logging (ELK, Splunk, CloudWatch)
- [ ] Log authentication attempts (success and failure)
- [ ] Log authorization failures
- [ ] Log unusual activity patterns
- [ ] Set up alerts for security events
- [ ] Implement log rotation
- [ ] Protect log files (restrict access)

#### Log Events to Monitor
- Failed login attempts (>5 per hour per IP)
- Account lockouts
- Password changes
- Permission escalation attempts
- Unusual API usage patterns
- Rate limit violations
- Database errors
- Application crashes

### 9. Secrets Management

#### Required Actions
- [ ] Never commit secrets to version control
- [ ] Use environment variables for all secrets
- [ ] Consider using a secrets manager (Vault, AWS Secrets Manager)
- [ ] Rotate secrets regularly (quarterly minimum)
- [ ] Implement secret scanning in CI/CD pipeline
- [ ] Encrypt secrets at rest
- [ ] Use separate secrets for each environment

#### Best Practices
```bash
# Check for committed secrets
git secrets --scan

# Use secrets manager (example with AWS)
aws secretsmanager get-secret-value --secret-id prod/app/secret-key
```

### 10. Docker Security (if using containers)

#### Required Actions
- [ ] Use official base images from trusted sources
- [ ] Scan images for vulnerabilities (Trivy, Clair)
- [ ] Run containers as non-root user
- [ ] Limit container resources (CPU, memory)
- [ ] Use read-only root filesystem where possible
- [ ] Remove unnecessary packages from images
- [ ] Keep base images updated
- [ ] Use multi-stage builds to minimize image size

#### Dockerfile Security
```dockerfile
# Use specific versions
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11. Backup and Recovery

#### Required Actions
- [ ] Implement automated database backups
- [ ] Test backup restoration process
- [ ] Store backups in secure location (encrypted)
- [ ] Implement point-in-time recovery
- [ ] Document recovery procedures
- [ ] Test disaster recovery plan
- [ ] Set up backup monitoring and alerts

#### Backup Schedule
- Database: Daily full backup, hourly incremental
- Configuration: Weekly backup
- Application logs: Daily backup with 30-day retention

### 12. Dependency Security

#### Required Actions
- [ ] Audit all dependencies for known vulnerabilities
- [ ] Enable dependency scanning in CI/CD
- [ ] Keep dependencies updated
- [ ] Review dependency licenses
- [ ] Pin dependency versions
- [ ] Use private package registry if needed

#### Tools
```bash
# Python dependencies
pip-audit

# Check for outdated packages
pip list --outdated

# Node.js dependencies (frontend)
npm audit
npm audit fix
```

## Post-Deployment Verification

### 1. Security Headers Test
```bash
curl -I https://your-domain.com/health | grep -E "X-Frame-Options|X-Content-Type-Options|X-XSS-Protection|Content-Security-Policy"
```

### 2. SSL/TLS Test
```bash
nmap --script ssl-enum-ciphers -p 443 your-domain.com
```

### 3. Rate Limiting Test
```bash
# Should eventually return 429
for i in {1..100}; do curl https://your-domain.com/; done
```

### 4. Authentication Test
```bash
# Should return 401 or 403
curl https://your-domain.com/api/v1/users/me
```

### 5. SQL Injection Test
```bash
# Should not expose database errors
curl "https://your-domain.com/api/v1/users/1'; DROP TABLE users; --"
```

## Continuous Security

### Regular Tasks
- [ ] Weekly: Review application logs for anomalies
- [ ] Weekly: Check for dependency updates
- [ ] Monthly: Run vulnerability scans
- [ ] Monthly: Review access logs
- [ ] Quarterly: Rotate secrets and credentials
- [ ] Quarterly: Security training for team
- [ ] Annually: Full security audit
- [ ] Annually: Penetration testing

### Automated Monitoring
- [ ] Set up uptime monitoring
- [ ] Configure error tracking (Sentry, Rollbar)
- [ ] Enable security event alerts
- [ ] Monitor rate limit violations
- [ ] Track failed authentication attempts
- [ ] Monitor database performance
- [ ] Set up infrastructure monitoring

## Compliance Considerations

### GDPR (if applicable)
- [ ] Implement data minimization
- [ ] Add consent management
- [ ] Enable data export functionality
- [ ] Implement right to deletion
- [ ] Document data processing activities
- [ ] Appoint Data Protection Officer (if required)

### HIPAA (if handling health data)
- [ ] Implement audit logging
- [ ] Enable data encryption at rest and in transit
- [ ] Add access controls and authentication
- [ ] Implement data backup and recovery
- [ ] Create incident response plan

## Incident Response Plan

### Preparation
1. Document security contacts
2. Create incident response runbook
3. Set up communication channels
4. Define severity levels
5. Establish escalation procedures

### Response Steps
1. **Detect**: Monitor alerts and logs
2. **Identify**: Determine nature and scope
3. **Contain**: Isolate affected systems
4. **Eradicate**: Remove threat
5. **Recover**: Restore normal operations
6. **Learn**: Post-incident review

### Emergency Contacts
- [ ] Security team lead
- [ ] System administrator
- [ ] Database administrator
- [ ] Legal counsel
- [ ] Public relations (for data breaches)

## Sign-Off

This checklist should be reviewed and signed off before production deployment:

**Reviewed By**: ___________________  
**Date**: ___________________  
**Deployment Environment**: ___________________  
**Version**: ___________________  

---

**Document Version**: 1.0.0  
**Last Updated**: February 11, 2026  
**Next Review Date**: May 11, 2026

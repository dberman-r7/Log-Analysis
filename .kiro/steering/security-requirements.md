# Security Requirements - Zero Tolerance Policy

> Security best practices for this repository.
> Full details: #[[file:.github/copilot-instructions.md]]

---

## Zero Tolerance for Hardcoded Secrets

**This is non-negotiable. No exceptions.**

```python
# ❌ FORBIDDEN - Will fail security scan
API_KEY = "sk-1234567890abcdef"
PASSWORD = "my_password"
CONNECTION_STRING = "server=prod.db;user=admin;password=secret"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# ✅ REQUIRED - Use environment variables
import os

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise EnvironmentError("API_KEY not configured")

# ✅ REQUIRED - Use secret management service
from secret_manager import get_secret
CONNECTION_STRING = get_secret('db-connection-string')
```

---

## Input Validation

**All inputs must be validated and sanitized.**

```python
# ✅ Validate all inputs
def process_user_input(user_id: str, data: dict):
    # Validate types
    if not isinstance(user_id, str):
        raise ValueError("user_id must be string")
    
    # Validate format
    if not re.match(r'^[a-zA-Z0-9-]+$', user_id):
        raise ValueError("Invalid user_id format")
    
    # Validate ranges
    if len(user_id) > 100:
        raise ValueError("user_id too long")
    
    # Sanitize inputs
    sanitized_data = sanitize(data)
    
    return process(user_id, sanitized_data)
```

---

## Dependency Audits

**Run security audits before adding/updating dependencies.**

```bash
# Python
pip-audit

# Check for vulnerabilities
pip-audit --fix

# Node.js
npm audit
npm audit fix

# Ruby
bundle audit

# Rust
cargo audit
```

**CI Integration**: Audits run on every PR
- Block merge if HIGH or CRITICAL vulnerabilities
- Warn on MEDIUM vulnerabilities (require acknowledgment)

---

## Authentication & Authorization

```python
# ✅ Always check authentication
@require_authentication
def protected_endpoint(request):
    user = get_authenticated_user(request)
    if not user:
        raise Unauthorized("Authentication required")
    
    # ✅ Always check authorization
    if not user.has_permission('read:data'):
        raise Forbidden("Insufficient permissions")
    
    return get_data()
```

---

## Data Encryption

**Sensitive data must be encrypted.**

- **At Rest**: Encrypt sensitive data in databases and files
- **In Transit**: Use TLS 1.3+ for all network communication
- **In Memory**: Clear sensitive data after use

```python
# ✅ Encrypt sensitive data
from cryptography.fernet import Fernet

def store_sensitive_data(data: str):
    key = get_encryption_key()
    cipher = Fernet(key)
    encrypted = cipher.encrypt(data.encode())
    save_to_database(encrypted)

# ✅ Use HTTPS/TLS
requests.get('https://api.example.com', verify=True)
```

---

## Least Privilege Principle

**Grant minimum permissions required.**

### Service Accounts
- Grant only necessary permissions
- Use role-based access control (RBAC)
- Rotate credentials regularly
- Audit access periodically

### Container Security
```dockerfile
# ✅ Run as non-root user
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
USER appuser

# ✅ Use minimal base images
FROM python:3.11-alpine

# ✅ Scan images for vulnerabilities
# docker scan myimage:latest
```

---

## SQL Injection Prevention

```python
# ❌ FORBIDDEN - SQL injection vulnerability
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ REQUIRED - Use parameterized queries
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))

# ✅ REQUIRED - Use ORM
user = User.objects.get(id=user_id)
```

---

## Path Traversal Prevention

```python
# ❌ FORBIDDEN - Path traversal vulnerability
file_path = f"/data/{user_provided_filename}"

# ✅ REQUIRED - Validate and sanitize paths
import os
from pathlib import Path

def safe_file_access(filename: str):
    # Validate filename
    if '..' in filename or filename.startswith('/'):
        raise ValueError("Invalid filename")
    
    # Use safe path joining
    base_dir = Path('/data')
    file_path = (base_dir / filename).resolve()
    
    # Ensure path is within base directory
    if not file_path.is_relative_to(base_dir):
        raise ValueError("Path traversal attempt detected")
    
    return file_path
```

---

## Logging Security

**Never log sensitive data.**

```python
# ❌ FORBIDDEN - Logs sensitive data
logger.info(f"User logged in: {username} with password {password}")
logger.info(f"API key: {api_key}")

# ✅ REQUIRED - Redact sensitive data
logger.info(f"User logged in: {username}")
logger.info(f"API key: {api_key[:8]}***")  # Only log prefix

# ✅ REQUIRED - Use structured logging with redaction
logger.info("User authenticated", extra={
    "user_id": user_id,
    "ip_address": redact_ip(ip_address),
    "session_id": session_id
})
```

---

## Security Headers

**Set appropriate security headers.**

```python
# ✅ Security headers for web applications
response.headers['X-Content-Type-Options'] = 'nosniff'
response.headers['X-Frame-Options'] = 'DENY'
response.headers['X-XSS-Protection'] = '1; mode=block'
response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
response.headers['Content-Security-Policy'] = "default-src 'self'"
```

---

## Secrets Management Checklist

- [ ] No hardcoded secrets in code
- [ ] Secrets loaded from environment variables or secret manager
- [ ] Secrets not logged or exposed in error messages
- [ ] Secrets not committed to version control
- [ ] `.env` files in `.gitignore`
- [ ] Secrets rotated regularly
- [ ] Secrets have appropriate access controls

---

## Pre-Commit Security Checks

```bash
# Install git-secrets
git secrets --install

# Scan for secrets
git secrets --scan

# Scan history
git secrets --scan-history
```

---

## Common Vulnerabilities to Avoid

### 1. Command Injection
```python
# ❌ FORBIDDEN
os.system(f"ping {user_input}")

# ✅ REQUIRED
import subprocess
subprocess.run(['ping', user_input], check=True)
```

### 2. XML External Entity (XXE)
```python
# ❌ FORBIDDEN
import xml.etree.ElementTree as ET
tree = ET.parse(user_file)

# ✅ REQUIRED
import defusedxml.ElementTree as ET
tree = ET.parse(user_file)
```

### 3. Insecure Deserialization
```python
# ❌ FORBIDDEN
import pickle
data = pickle.loads(user_data)

# ✅ REQUIRED
import json
data = json.loads(user_data)
```

---

## Security Review Triggers

**Security review required for**:
- Authentication/authorization changes
- New PII handling
- New credentials/secrets
- New external data access
- Changes to data encryption
- Compliance-related changes (GDPR, SOC2, PCI-DSS, HIPAA)

---

## Compliance Requirements

### GDPR (if handling EU user data)
- [ ] User consent obtained
- [ ] Data minimization applied
- [ ] Right to deletion implemented
- [ ] Privacy policy updated

### SOC 2
- [ ] Access controls documented
- [ ] Audit logs enabled
- [ ] Change management followed
- [ ] Incident response plan updated

---

## For AI Agents: Security Checklist

Before committing code:

- [ ] No hardcoded secrets
- [ ] All inputs validated
- [ ] Dependencies audited
- [ ] Sensitive data encrypted
- [ ] Least privilege applied
- [ ] Security headers set (if web app)
- [ ] No sensitive data in logs
- [ ] SQL injection prevented
- [ ] Path traversal prevented

---

## Quick Security Commands

```bash
# Scan for secrets in code
git secrets --scan

# Audit Python dependencies
pip-audit

# Check for common vulnerabilities
bandit -r src/

# Scan Docker images
docker scan myimage:latest

# Check for outdated dependencies
pip list --outdated
```

---

**Last Updated**: 2026-02-19

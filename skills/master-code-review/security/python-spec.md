# Python Application Security Policy Specification

**Version:** 1.0
**Date:** 2026-02-14
**Status:** DRAFT
**Scope:** Python scripts, FastAPI web services, and AI/agentic applications

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Scope & Applicability](#2-scope--applicability)
3. [Code Review Security Standards](#3-code-review-security-standards)
4. [Input Validation & Injection Prevention](#4-input-validation--injection-prevention)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [Cryptography & Data Protection](#6-cryptography--data-protection)
7. [Secrets Management](#7-secrets-management)
8. [Dependency & Supply Chain Security](#8-dependency--supply-chain-security)
9. [Logging, Error Handling & Monitoring](#9-logging-error-handling--monitoring)
10. [FastAPI-Specific Security Controls](#10-fastapi-specific-security-controls)
11. [LLM Application Security (OWASP Top 10 for LLMs)](#11-llm-application-security-owasp-top-10-for-llms)
12. [Agentic Application Security (OWASP Top 10 for Agentic Apps)](#12-agentic-application-security-owasp-top-10-for-agentic-apps)
13. [Static Analysis & CI/CD Integration](#13-static-analysis--cicd-integration)
14. [Security Review Checklist](#14-security-review-checklist)
15. [References](#15-references)

---

## 1. Purpose

This document defines the security policy and code review standards for all Python applications developed and maintained within this organization. It establishes mandatory controls, review criteria, and tooling requirements to ensure applications are resilient against common attack vectors -- including those specific to AI-powered and agentic systems.

All code contributions MUST pass a security review against this specification before merging to protected branches.

---

## 2. Scope & Applicability

This policy applies to three categories of Python applications:

| Category | Description | Applicable Sections |
|---|---|---|
| **Python Scripts & Libraries** | CLI tools, utilities, data pipelines, packages | Sections 3-9, 13-14 |
| **FastAPI Web Services** | REST APIs, web backends, microservices | Sections 3-10, 13-14 |
| **AI / Agentic Applications** | LLM-powered apps, autonomous agents, RAG systems | Sections 3-14 (all) |

**Compliance requirement:** All categories MUST comply with their applicable sections. Non-compliance must be documented with a risk acceptance signed by the project lead.

---

## 3. Code Review Security Standards

### 3.1 Review Requirements

- Every pull request MUST receive at least one security-focused review before merge.
- Reviewers MUST verify compliance against sections applicable to the application category.
- Security findings MUST be classified by severity: **Critical**, **High**, **Medium**, **Low**.
- Critical and High findings MUST be resolved before merge. Medium findings MUST have a remediation timeline. Low findings SHOULD be resolved in the current sprint.

### 3.2 Review Dimensions

All code reviews MUST evaluate the following dimensions:

1. **Input boundary trust** -- Is all external input validated and sanitized?
2. **Authentication & authorization** -- Are access controls enforced at every entry point?
3. **Data protection** -- Are secrets, PII, and sensitive data handled correctly?
4. **Error handling** -- Do errors fail securely without leaking information?
5. **Dependency safety** -- Are all dependencies vetted and free of known vulnerabilities?
6. **Logging hygiene** -- Are security events logged without exposing sensitive data?
7. **Injection resistance** -- Is the code immune to SQL, OS, and deserialization injection?
8. **Cryptographic correctness** -- Are proper algorithms and libraries used?
9. **AI/Agent safety** -- (If applicable) Are agent boundaries, permissions, and outputs controlled?

---

## 4. Input Validation & Injection Prevention

### 4.1 General Rules

- **[MANDATORY]** All external input MUST be validated before use. Never trust data from users, APIs, files, databases, or environment variables without verification.
- **[MANDATORY]** Define explicit allowlists for acceptable input. Reject anything that does not match.
- **[MANDATORY]** Use type hints and runtime validation (Pydantic models for web apps) for all function parameters that accept external data.

### 4.2 SQL Injection (CWE-89)

- **[MANDATORY]** Use ORM-based parameterized queries exclusively (SQLAlchemy, SQLModel).
- **[PROHIBITED]** Never concatenate or interpolate user input into SQL strings.
- **[PROHIBITED]** Never use raw SQL queries with user-supplied values.

```python
# COMPLIANT
stmt = select(User).where(User.email == email_param)
result = session.execute(stmt)

# NON-COMPLIANT -- SQL injection risk
query = f"SELECT * FROM users WHERE email = '{email_param}'"
result = session.execute(text(query))
```

### 4.3 OS Command Injection (CWE-78)

- **[MANDATORY]** Never pass unsanitized input to `os.system()`, `subprocess.call()`, `subprocess.run()`, or `os.popen()`.
- **[MANDATORY]** When subprocess execution is required, use argument lists (not shell strings) and set `shell=False`.

```python
# COMPLIANT
subprocess.run(["ls", "-la", directory], shell=False, check=True)

# NON-COMPLIANT -- command injection risk
subprocess.run(f"ls -la {directory}", shell=True)
```

### 4.4 Deserialization Attacks (CWE-502)

- **[PROHIBITED]** Never use `pickle.loads()`, `pickle.load()`, or `shelve` on untrusted data. The `pickle` module can execute arbitrary code during deserialization.
- **[MANDATORY]** Use `json`, `msgpack`, or other safe serialization formats for untrusted data.
- **[PROHIBITED]** Never use `yaml.load()` without `Loader=yaml.SafeLoader`.

### 4.5 Format String Vulnerabilities (CWE-134)

- **[PROHIBITED]** Never use user-controlled input as format strings.
- **[MANDATORY]** Use f-strings or `.format()` with controlled templates only.

---

## 5. Authentication & Authorization

### 5.1 General Rules

- **[MANDATORY]** Every API endpoint and protected resource MUST enforce authentication.
- **[MANDATORY]** Authorization checks MUST be performed at every access point, not just at the entry point.
- **[MANDATORY]** Implement the principle of least privilege -- grant minimum permissions required.

### 5.2 Token-Based Authentication

- **[MANDATORY]** Use OAuth2 with JWT tokens for API authentication.
- **[MANDATORY]** Tokens MUST have an expiration time. Access tokens SHOULD NOT exceed 30 minutes.
- **[MANDATORY]** Implement token refresh mechanisms for long-lived sessions.
- **[MANDATORY]** Validate token signatures, expiration, issuer, and audience on every request.
- **[PROHIBITED]** Never store tokens in local storage for web clients. Use HTTP-only secure cookies.

### 5.3 Password Handling

- **[MANDATORY]** Hash passwords using **bcrypt** or **Argon2** with unique per-user salts.
- **[PROHIBITED]** Never store passwords in plaintext or with reversible encryption.
- **[PROHIBITED]** Never use MD5, SHA-1, or SHA-256 alone for password hashing (no key stretching).
- **[MANDATORY]** Use `passlib` or equivalent library for password hashing operations.

---

## 6. Cryptography & Data Protection

### 6.1 Randomness (CWE-330)

- **[MANDATORY]** Use the `secrets` module for all security-sensitive random values (tokens, keys, nonces).
- **[PROHIBITED]** Never use the `random` module for security purposes. `random` is not cryptographically secure.

```python
# COMPLIANT
import secrets
token = secrets.token_urlsafe(32)

# NON-COMPLIANT
import random
token = ''.join(random.choices(string.ascii_letters, k=32))
```

### 6.2 Encryption

- **[MANDATORY]** Encrypt sensitive data at rest using the `cryptography` library (AES-256 via Fernet or similar).
- **[MANDATORY]** All data in transit MUST be encrypted via TLS 1.2 or higher.
- **[PROHIBITED]** Never implement custom cryptographic algorithms. Use established libraries only.

### 6.3 Data Classification

- **[MANDATORY]** Classify all data handled by the application into: **Public**, **Internal**, **Confidential**, **Restricted**.
- **[MANDATORY]** Apply encryption and access controls proportional to classification level.

---

## 7. Secrets Management

### 7.1 Rules

- **[MANDATORY]** Never hardcode credentials, API keys, database URLs, or tokens in source code (CWE-798).
- **[MANDATORY]** Use environment variables for configuration in development.
- **[MANDATORY]** Use a dedicated secret manager in production (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, etc.).
- **[MANDATORY]** Rotate secrets on a defined schedule and after any suspected compromise.
- **[MANDATORY]** Add `.env`, `credentials.json`, and similar files to `.gitignore`.

### 7.2 Detection

- **[MANDATORY]** Run pre-commit hooks to detect secrets before they reach the repository (e.g., `detect-secrets`, `truffleHog`).
- **[MANDATORY]** Scan existing repositories for leaked secrets as part of onboarding.

---

## 8. Dependency & Supply Chain Security

### 8.1 Package Management

- **[MANDATORY]** Use virtual environments (`venv`, `conda`, or `poetry`) for all projects.
- **[MANDATORY]** Pin dependency versions in `requirements.txt` or `pyproject.toml` with hash verification where possible.
- **[MANDATORY]** Audit dependencies before adding them. Verify package names to prevent typosquatting.
- **[MANDATORY]** Use only absolute or explicit relative imports (implicit relative imports are prohibited).

### 8.2 Vulnerability Scanning

- **[MANDATORY]** Run `pip-audit` or `safety` on every CI/CD pipeline execution.
- **[MANDATORY]** Address Critical and High severity vulnerabilities within **48 hours**.
- **[MANDATORY]** Address Medium severity vulnerabilities within **2 weeks**.
- **[MANDATORY]** Maintain a Software Bill of Materials (SBOM) for all production applications.

### 8.3 Update Policy

- **[MANDATORY]** Review and update dependencies at least **monthly**.
- **[MANDATORY]** Subscribe to security advisories for all critical dependencies.
- **[MANDATORY]** Test dependency updates in a staging environment before production deployment.

---

## 9. Logging, Error Handling & Monitoring

### 9.1 Logging Requirements

- **[MANDATORY]** Log all security-relevant events (CWE-778):
  - Authentication attempts (success and failure)
  - Authorization failures
  - Input validation failures
  - Permission changes
  - Data access to restricted resources
- **[PROHIBITED]** Never log sensitive data: passwords, tokens, API keys, credit card numbers, PII (CWE-532).
- **[MANDATORY]** Sanitize log output to prevent log injection attacks (CWE-117).
- **[MANDATORY]** Use structured logging (JSON format) for machine-parseable audit trails.

### 9.2 Error Handling

- **[MANDATORY]** Return generic error messages to clients. Never expose stack traces, internal paths, or system details.
- **[MANDATORY]** Log detailed error information server-side for debugging.
- **[PROHIBITED]** Never leave debug mode enabled in production (CWE-489).
- **[MANDATORY]** Use specific exception types. Avoid bare `except:` clauses.

```python
# COMPLIANT
try:
    result = process_data(user_input)
except ValidationError as e:
    logger.warning("Validation failed", extra={"field": e.field})
    raise HTTPException(status_code=400, detail="Invalid input")

# NON-COMPLIANT -- leaks internal details
except Exception as e:
    return {"error": str(e), "traceback": traceback.format_exc()}
```

### 9.3 Monitoring

- **[MANDATORY]** Implement alerting for anomalous patterns: brute-force attempts, unusual data access, privilege escalation.
- **[MANDATORY]** Retain security logs for a minimum of **90 days**.

---

## 10. FastAPI-Specific Security Controls

This section applies to all FastAPI web services in addition to Sections 3-9.

### 10.1 Authentication & Middleware

- **[MANDATORY]** Use FastAPI's `fastapi.security` module with dependency injection for auth.
- **[MANDATORY]** Chain dependencies for multi-level authorization (authentication -> ownership -> role).
- **[MANDATORY]** Implement token expiration and refresh with secure storage (Redis, database-backed).

### 10.2 Input Validation

- **[MANDATORY]** Use Pydantic models for all request body, query parameter, and path parameter validation.
- **[MANDATORY]** Apply constraints: `max_length`, `regex`, `gt`/`lt`, `Enum` types.
- **[MANDATORY]** Validate file uploads: type, extension, size. Use `werkzeug.utils.secure_filename`.

### 10.3 CORS, CSRF & Security Headers

- **[MANDATORY]** Configure CORS with explicit trusted origins only.
- **[PROHIBITED]** Never use wildcard (`*`) CORS origins in production.
- **[MANDATORY]** Implement CSRF protection for state-changing operations (`fastapi-csrf-protect`).
- **[MANDATORY]** Set the following security headers via middleware:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Content-Security-Policy` (appropriate to application)
  - `X-XSS-Protection: 1; mode=block`

### 10.4 Rate Limiting

- **[MANDATORY]** Implement rate limiting on all authentication endpoints using `slowapi` or equivalent.
- **[MANDATORY]** Apply general rate limiting to prevent abuse and resource exhaustion.

### 10.5 Production Hardening

- **[MANDATORY]** Disable or restrict access to `/docs` and `/redoc` in production environments.
- **[MANDATORY]** Serve all traffic over HTTPS. Redirect HTTP to HTTPS.
- **[MANDATORY]** Use `async def` routes with proper async I/O. Offload CPU-heavy work to background workers (Celery, etc.).
- **[MANDATORY]** Use database migrations (Alembic) from project inception.

### 10.6 Database Security

- **[MANDATORY]** Use SQLAlchemy/SQLModel with parameterized queries exclusively.
- **[MANDATORY]** Apply principle of least privilege for database user accounts.
- **[MANDATORY]** Use connection pooling with appropriate limits.
- **[MANDATORY]** Encrypt sensitive database fields at the application layer.

---

## 11. LLM Application Security (OWASP Top 10 for LLMs)

This section applies to all applications integrating Large Language Models. Based on the [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/).

### LLM01: Prompt Injection

- **[MANDATORY]** Constrain model behavior via well-defined system prompts with explicit boundaries.
- **[MANDATORY]** Segregate external/untrusted content from system instructions. Never concatenate user input directly into system prompts.
- **[MANDATORY]** Implement input validation filters for prompt content.
- **[MANDATORY]** Conduct adversarial testing (prompt injection attacks) before deployment.

### LLM02: Sensitive Information Disclosure

- **[MANDATORY]** Sanitize all training and fine-tuning data for PII and credentials.
- **[MANDATORY]** Implement output filtering to prevent the model from returning sensitive information.
- **[MANDATORY]** Enforce access controls on what data the model can retrieve.

### LLM03: Supply Chain

- **[MANDATORY]** Vet all third-party models, plugins, and data sources.
- **[MANDATORY]** Maintain an SBOM that includes model provenance.
- **[MANDATORY]** Verify model integrity with cryptographic signatures and hashes.

### LLM04: Data and Model Poisoning

- **[MANDATORY]** Validate all training data sources for integrity and provenance.
- **[MANDATORY]** Employ anomaly detection during fine-tuning and training.
- **[MANDATORY]** Conduct red team testing against poisoning attacks before deployment.

### LLM05: Improper Output Handling

- **[MANDATORY]** Apply context-aware encoding and sanitization to all model outputs before rendering or execution.
- **[MANDATORY]** Never pass model output directly to SQL queries, OS commands, or code execution engines.
- **[MANDATORY]** Limit the operational privileges of any system that consumes model output.

### LLM06: Excessive Agency

- **[MANDATORY]** Restrict model/agent functionality to the minimum required for its task.
- **[MANDATORY]** Implement human-in-the-loop approval for high-impact actions (data deletion, financial transactions, external communications).
- **[MANDATORY]** Define granular, role-specific permissions for model actions.

### LLM07: System Prompt Leakage

- **[MANDATORY]** Never store API keys, credentials, or sensitive business logic in system prompts.
- **[MANDATORY]** Use external credential stores and inject secrets at runtime.
- **[MANDATORY]** Implement output guardrails to detect and prevent prompt exfiltration.

### LLM08: Vector and Embedding Weaknesses

- **[MANDATORY]** Implement fine-grained access controls on vector databases.
- **[MANDATORY]** Validate embedding integrity and provenance.
- **[MANDATORY]** Apply data classification and tagging to all vectorized content.

### LLM09: Misinformation

- **[MANDATORY]** Use Retrieval-Augmented Generation (RAG) with verified, authoritative knowledge bases.
- **[MANDATORY]** Implement human oversight for critical decisions informed by model output.
- **[MANDATORY]** Apply domain-specific fine-tuning to reduce hallucination in specialized contexts.

### LLM10: Unbounded Consumption

- **[MANDATORY]** Implement rate limiting on all LLM API calls.
- **[MANDATORY]** Set strict execution timeouts for model inference.
- **[MANDATORY]** Monitor usage continuously for abuse patterns and cost anomalies.

---

## 12. Agentic Application Security (OWASP Top 10 for Agentic Apps)

This section applies to all autonomous AI agent systems. Based on the [OWASP Top 10 for Agentic Applications (2026)](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/).

**Foundational Principle: Zero Trust for Agents** -- Every tool call, API request, and inter-agent message made by an AI agent MUST be independently verified, logged, and scoped.

### ASI01: Agent Goal Hijacking

- **[MANDATORY]** Implement strict goal validation that rejects objectives outside predefined boundaries.
- **[MANDATORY]** Sanitize all data sources consumed by agents (documents, APIs, user messages).
- **[MANDATORY]** Deploy behavioral monitoring to detect goal drift or manipulation in real-time.

### ASI02: Tool Misuse and Exploitation

- **[MANDATORY]** Define explicit scoping for every tool an agent can access.
- **[MANDATORY]** Enforce least-privilege access -- agents MUST NOT have broader tool access than their task requires.
- **[MANDATORY]** Validate all tool call parameters before execution.
- **[MANDATORY]** Log every tool invocation with full parameter details.

### ASI03: Identity and Privilege Abuse

- **[MANDATORY]** Treat agents as first-class identities with their own authentication and authorization.
- **[MANDATORY]** Implement per-agent credential scoping -- no shared credentials between agents.
- **[MANDATORY]** Prevent privilege escalation via relay attacks between low-privilege and high-privilege agents.

### ASI04: Agentic Supply Chain Vulnerabilities

- **[MANDATORY]** Vet all third-party tool providers before integration.
- **[MANDATORY]** Validate tool integrity at runtime (checksums, signatures).
- **[MANDATORY]** Isolate third-party tool execution in sandboxed environments.

### ASI05: Unexpected Code Execution (RCE)

- **[MANDATORY]** Sandbox all agent-generated code execution in isolated environments (containers, VMs, restricted interpreters).
- **[MANDATORY]** Review agent-generated code before execution where possible.
- **[MANDATORY]** Restrict available system calls, file system access, and network access for executing agents.
- **[PROHIBITED]** Never allow agents to execute arbitrary code with full system privileges.

### ASI06: Memory and Context Poisoning

- **[MANDATORY]** Validate all memory writes -- agents MUST NOT write to long-term memory without integrity checks.
- **[MANDATORY]** Implement memory integrity verification on read.
- **[MANDATORY]** Separate memory access into tiers with different trust levels.
- **[MANDATORY]** Audit memory contents periodically for injected or corrupted data.

### ASI07: Insecure Inter-Agent Communication

- **[MANDATORY]** Encrypt all inter-agent communication channels.
- **[MANDATORY]** Implement mutual authentication between communicating agents.
- **[MANDATORY]** Validate message integrity and prevent replay attacks.

### ASI08: Cascading Failures

- **[MANDATORY]** Implement circuit breakers to halt failure propagation across agent networks.
- **[MANDATORY]** Design for fault isolation -- a single agent failure MUST NOT take down the system.
- **[MANDATORY]** Implement graceful degradation patterns with fallback behaviors.

### ASI09: Human-Agent Trust Exploitation

- **[MANDATORY]** Clearly disclose agent identity in all interactions -- agents MUST NOT impersonate humans.
- **[MANDATORY]** Require mandatory human review for all high-risk actions.
- **[MANDATORY]** Provide transparency into agent reasoning and decision chains.

### ASI10: Rogue Agents

- **[MANDATORY]** Implement kill switches that can immediately terminate agent execution.
- **[MANDATORY]** Enforce behavioral bounds with runtime monitoring.
- **[MANDATORY]** Continuously monitor agent alignment with intended objectives.
- **[PROHIBITED]** Agents MUST NOT self-replicate or spawn sub-agents without explicit authorization.

---

## 13. Static Analysis & CI/CD Integration

### 13.1 Required Toolchain

The following tools MUST be integrated into the CI/CD pipeline:

| Tool | Purpose | Stage | Blocking |
|---|---|---|---|
| **Bandit** | Python security static analysis | Pre-commit + CI | Yes -- Critical/High |
| **Ruff** | Linting and style enforcement | Pre-commit + CI | Yes |
| **mypy** | Type checking | CI | Yes |
| **pip-audit** | Dependency vulnerability scanning | CI | Yes -- Critical/High |
| **detect-secrets** | Pre-commit secret detection | Pre-commit | Yes |
| **pytest** | Unit, integration, and API tests | CI | Yes |
| **Semgrep** | Custom security rule enforcement | CI | Yes -- Critical/High |

### 13.2 Pipeline Requirements

- **[MANDATORY]** All tools in section 13.1 MUST run on every pull request.
- **[MANDATORY]** Builds MUST fail on Critical or High severity findings from any security tool.
- **[MANDATORY]** Pre-commit hooks MUST include: `bandit`, `ruff`, `detect-secrets`.
- **[MANDATORY]** Dependency scans MUST run on schedule (daily) in addition to PR triggers.

### 13.3 Configuration Standards

```toml
# pyproject.toml -- minimum security tool configuration

[tool.bandit]
exclude_dirs = ["tests"]
skips = []  # Do not skip any checks without documented justification

[tool.ruff]
select = ["E", "F", "W", "S", "B", "I", "N", "UP", "ANN"]
# S = flake8-bandit rules (security)
# B = flake8-bugbear (common bugs)

[tool.mypy]
strict = true
warn_return_any = true
disallow_untyped_defs = true
```

---

## 14. Security Review Checklist

Use this checklist during every code review. All items MUST be verified for applicable application categories.

### General (All Python Applications)

- [ ] All external input is validated and sanitized
- [ ] No hardcoded secrets, credentials, or API keys
- [ ] Parameterized queries used exclusively (no raw SQL with user input)
- [ ] No use of `pickle`, `eval()`, `exec()` on untrusted data
- [ ] No use of `os.system()` or `subprocess` with `shell=True` and user input
- [ ] `secrets` module used for security-sensitive randomness (not `random`)
- [ ] Passwords hashed with bcrypt or Argon2 (not MD5/SHA)
- [ ] Error messages do not expose internal details
- [ ] Security events are logged (auth failures, access denials)
- [ ] No sensitive data in logs (passwords, tokens, PII)
- [ ] Dependencies scanned and free of known Critical/High vulnerabilities
- [ ] Type hints present on all public interfaces
- [ ] Debug code removed from production paths

### FastAPI Services (Additional)

- [ ] Pydantic models validate all request inputs
- [ ] OAuth2/JWT authentication enforced on protected endpoints
- [ ] CORS restricted to explicit trusted origins (no wildcards)
- [ ] CSRF protection on state-changing operations
- [ ] Security headers configured via middleware
- [ ] Rate limiting on authentication endpoints
- [ ] `/docs` and `/redoc` disabled or restricted in production
- [ ] HTTPS enforced with HTTP redirect
- [ ] Database connections use ORM with least-privilege accounts

### LLM Applications (Additional)

- [ ] System prompts do not contain secrets or sensitive logic
- [ ] User input is segregated from system instructions
- [ ] Model output is sanitized before rendering or execution
- [ ] Human-in-the-loop required for high-impact actions
- [ ] Model/tool permissions follow least privilege
- [ ] RAG data sources are verified and access-controlled
- [ ] Rate limiting and timeouts on LLM API calls
- [ ] Adversarial prompt injection testing completed

### Agentic Applications (Additional)

- [ ] Agents have individual identities and scoped credentials
- [ ] All tool calls are validated, logged, and least-privilege scoped
- [ ] Code execution is sandboxed
- [ ] Inter-agent communication is encrypted and authenticated
- [ ] Memory writes are validated and auditable
- [ ] Kill switch is implemented and tested
- [ ] Circuit breakers prevent cascading failures
- [ ] Human review required for high-risk agent actions
- [ ] Agent cannot self-replicate without authorization
- [ ] Behavioral monitoring detects goal drift

---

## 15. References

### Python Security

- [OpenSSF Secure Coding Guide for Python](https://best.openssf.org/Secure-Coding-Guide-for-Python/)
- [OWASP Python Security Project](https://owasp.org/www-project-python-security/)
- [Python Application Security 2025 - August Infotech](https://www.augustinfotech.com/blogs/python-security-best-practices-for-2025/)
- [Six Python Security Best Practices - Black Duck](https://www.blackduck.com/blog/python-security-best-practices.html)

### FastAPI Security

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Securing FastAPI Applications - VolkanSah (GitHub)](https://github.com/VolkanSah/Securing-FastAPI-Applications)
- [FastAPI Best Practices - zhanymkanov (GitHub)](https://github.com/zhanymkanov/fastapi-best-practices)

### AI / LLM Security

- [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
- [OWASP Top 10 for Agentic Applications (2026)](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [LLM Risks Archive - OWASP GenAI Security Project](https://genai.owasp.org/llm-top-10/)

### General Web Security

- [OWASP Top 10 Web Application Security Risks](https://owasp.org/www-project-top-10/)
- [The Pythonista's Guide to the OWASP Top 10](https://devm.io/python/python-owasp-app-security)

### Tooling

- [Bandit - Python Security Linter](https://bandit.readthedocs.io/)
- [pip-audit](https://pypi.org/project/pip-audit/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [Semgrep](https://semgrep.dev/)

---

*This document is a living specification. It MUST be reviewed and updated at least quarterly or when new OWASP guidance is published.*

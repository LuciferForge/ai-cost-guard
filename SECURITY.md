# Security Policy

## What this library protects against

`ai-cost-guard` was built to address a class of security vulnerabilities
in LLM-powered applications that are easy to overlook:

### 1. Runaway spend from prompt injection
A malicious user can craft prompts that cause your app to make
far more LLM calls than intended — or calls to more expensive models.
`ai-cost-guard` enforces a hard budget cap that terminates further
calls when the threshold is reached.

### 2. Accidental credential exposure via over-spend
Applications that exceed rate limits often retry with different credentials.
By tracking spend per API key and enforcing hard stops, `ai-cost-guard`
reduces the window for unintended credential rotation or exposure.

### 3. Infinite retry loops
Buggy retry logic can silently drain your API budget overnight.
The budget guard detects spend velocity and blocks when the ceiling is hit,
preventing total account compromise via billing.

### 4. Insecure API key handling
`ai-cost-guard` stores all tracking data locally (never calls home).
No API keys or prompt content are ever transmitted to third parties.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a Vulnerability

Please report security vulnerabilities via GitHub Issues (mark as "security").
Do NOT include sensitive data (API keys, prompts) in public issues.

Expected response time: 48 hours.

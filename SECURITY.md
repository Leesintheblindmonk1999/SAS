# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in SAS, please:

**DO NOT** open a public issue.

**DO** send a detailed report to: **duranteg2@gmail.com**

Include:

- Affected version(s)
- Steps to reproduce
- Potential impact
- Any suggested fix, if available

You can expect:

- Acknowledgment within 48 hours
- Regular updates on the investigation
- Credit upon public disclosure, if desired

## Security Measures Implemented

| Measure | Status |
|---------|--------|
| API key authentication | ✅ |
| Rate limiting for free tier | ✅ |
| Request timeout | ✅ |
| Input validation | ✅ |
| HTTPS recommended | ⚠️ Enforce in production |
| CORS protection | ✅ Configurable |

## Best Practices for Deployments

1. Always use HTTPS in production.
2. Rotate `ADMIN_SECRET` before deployment.
3. Set restrictive `CORS_ALLOW_ORIGINS` in `.env`.
4. Keep API keys private.
5. Monitor rate limit logs for abuse.
6. Regularly update dependencies.
7. Do not commit `.env`, database files, logs, or local secrets.

## Responsible Disclosure

We follow responsible disclosure practices.

We will:

- Confirm receipt of your report within 48 hours.
- Provide updates during the investigation.
- Aim to provide a fix within 90 days, depending on severity.
- Publicly acknowledge your contribution, unless you request anonymity.

## Contact

**Security contact:** duranteg2@gmail.com  
**PGP Key:** Available upon request
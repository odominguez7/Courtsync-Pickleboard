# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in CourtSync, please report it responsibly.

**Do not open a public issue.**

Email **omar.dominguez7@gmail.com** with:

- Description of the vulnerability
- Steps to reproduce
- Impact assessment

You will receive a response within 48 hours.

## Security Practices

- All secrets stored in GCP Secret Manager, never in code
- Twilio webhook signature verification enforced in production (Cloud Run)
- Phone numbers redacted in all logs
- User input sanitized before AI prompt injection
- Rate limiting on webhook endpoints (20 msg/min per phone)
- Message length limits enforced (2000 chars inbound, 1600 chars outbound)
- Phone number format validation on all inputs
- No PII exposed in error responses

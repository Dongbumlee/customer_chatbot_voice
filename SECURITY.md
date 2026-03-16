# Security

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it responsibly by emailing
the project maintainers directly. Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

## Security Practices

- All secrets stored in Azure Key Vault
- Authentication via Microsoft Entra ID (OAuth 2.0 / OIDC)
- TLS 1.2+ enforced for all communications
- Input validation on all user-facing endpoints
- Azure OpenAI content safety filters enabled
- CORS restricted to known origins
- Containers run as non-root users

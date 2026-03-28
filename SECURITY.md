# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | Yes                |

## Reporting a Vulnerability

If you discover a security vulnerability in aigov-shield, please report it
responsibly. **Do not open a public GitHub issue for security vulnerabilities.**

### How to Report

Send an email to **garyatwal2017@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested fixes (if applicable)

### Response Timeline

- **48 hours**: Acknowledgement of your report
- **7 days**: Initial assessment and severity determination
- **30 days**: Fix developed and tested (for confirmed vulnerabilities)
- **Release**: Security fix published with advisory

### Disclosure Policy

- We will coordinate disclosure with the reporter
- We will credit reporters who follow responsible disclosure (unless they prefer anonymity)
- We aim to fix confirmed vulnerabilities before any public disclosure

## Security Best Practices

When using aigov-shield in production:

- Keep the package updated to the latest version
- Do not store API keys or credentials in configuration files
- Use environment variables for sensitive configuration
- Review guard configurations for your specific compliance requirements
- Regularly verify chain of custody integrity using `aigov-shield verify-chain`

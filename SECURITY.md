# Security

Report vulnerabilities through GitHub's private vulnerability reporting (Security tab → Report a vulnerability). Do not open a public issue.

What the project does by design:

- API keys only through environment variables; secret scanning with push protection is enabled.
- Steps flagged as handling sensitive data are not sent to the LLM provider without explicit confirmation.
- Prompts and step descriptions are never written to logs.
- Monetary inputs are never sent to the LLM provider.
- The application has no authentication. Self-hosted copies belong on a private network, or on a public one only with demo data.

## Public demo

A public demo runs without login (ADR 0008). Treat everything entered there as public: other visitors can see it, and it is deleted every night, as the banner on every page says. Do not enter real business or personal data.

What protects the demo host and the API key:

- Only Nginx is exposed. It terminates TLS, limits request size and rate (analysis runs per client IP), and adds HSTS plus any security header the application does not set itself. The web client sends a strict Content Security Policy. Repeat offenders of the rate limit are banned by fail2ban.
- The API listens on `127.0.0.1` only and runs as a non-root user with a read-only root filesystem, no capabilities and memory and CPU limits. PostgreSQL has no published port.
- LLM spending is capped in layers: a dedicated Anthropic workspace with a monthly spend limit, a daily quota of analyses that call the LLM, the rate limit, and schema limits on request size. Past the quota the deterministic analysis still runs, without the AI interpretation.
- Images are the released, tested artifacts from `ghcr.io`, pinned by version; PostgreSQL is pinned by digest.

## Public demo data

- The demo processes are synthetic: a fictitious manufacturer, invented volumes and costs.
- Everything visitors create is deleted every night at 00:05 UTC once it is older than 24 hours: processes, steps, analyses and overrides. Editing a process does not extend its life.
- The database is backed up every night after that purge. Backups are kept for 7 days on the demo host, never leave the host, and are readable only by the demo's own system user. They exist to recover from a failure, never to keep visitor data.
- Logs never contain prompts or step descriptions.
- Steps flagged as sensitive reach the LLM provider only after the visitor confirms it, and monetary inputs never do.

# Deploy

Production stack of the public demo on the maintainer's VPS: `compose.prod.yaml` (copied to `/opt/apd/compose.yaml`), `deploy.sh` (copied to `/opt/apd/deploy.sh`), `nginx/apd.conf` for the host Nginx, `fail2ban/apd.local` for the host fail2ban, and `.env.example`.

## Read

- `docs/adr/0008-public-demo-on-own-vps.md`
- `docs/runbook/production.md` (draft until B11, RS-59 to RS-68, lands)

## Rules

- Placeholders only (`<domain>`, `<vps>`, `apd.example.com`). Real hostnames, IP addresses and secrets never enter the repo.
- The API publishes on `127.0.0.1` only. Docker writes its own iptables rules, so a port on `0.0.0.0` would bypass UFW.
- PostgreSQL has no published port and lives on the internal network.
- The n8n and website projects on the same host are never touched. The demo runs as its own system user, `apd`; the website's `deploy` user is never reused.
- Cost controls stay in layers: Anthropic workspace spend limit, daily LLM quota (`LLM_DAILY_LIMIT`), Nginx rate limit on analysis runs, schema limits.
- Security headers are set once, at server level in `apd.conf`, and only where the upstream response lacks them: the application owns its CSP. A location with its own `add_header` inherits none of them.
- Nginx zone names and fail2ban zone filters start with `apd_`, so they never match the other sites on the host.
- The API runs with `CREATE_SCHEMA_ON_STARTUP=false`. Alembic migrations run in a one-off container before a new version starts, never on API startup (RS-59).
- `deploy.sh` takes only a `vX.Y.Z` tag, from its argument or `SSH_ORIGINAL_COMMAND`, and never runs that value. It updates `APD_VERSION` in `.env` only after `/health` passes; on a failed check it starts the previous version again (RS-66).
- Streamlit is not deployed.

## Verify

```bash
docker compose -f deploy/compose.prod.yaml config
uv run pytest tests/unit/test_deploy_script.py
shellcheck deploy/deploy.sh
```

CI starts the compose file in the `docker` job and runs `shellcheck` in `quality`; the script tests use fake `docker`, `curl` and `flock` commands. `sudo nginx -t` runs on the host only.

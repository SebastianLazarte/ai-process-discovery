# Deploy

Production stack of the public demo on the maintainer's VPS: `compose.prod.yaml` (copied to `/opt/apd/compose.yaml`), `deploy.sh` (copied to `/opt/apd/deploy.sh`), `release-deploy.sh` and `smoke-test.sh` (run by the `deploy` job of the release workflow, on the runner), `backup.sh` and `restore-rehearsal.sh` (copied to `/opt/apd/`), `systemd/` for the purge and backup timers, `nginx/apd.conf` for the host Nginx with the routes in `nginx/apd-routes.conf`, which the `edge` service of the root `compose.yaml` also runs through `nginx/edge.conf`, `fail2ban/apd.local` for the host fail2ban, and `.env.example`.

## Read

- `docs/adr/0008-public-demo-on-own-vps.md`
- `docs/adr/0016-nextjs-at-the-root-from-2-0-0.md`: the 2.0.0 layout, one version per service, and the change through working states
- `docs/runbook/production.md`

## Rules

- Placeholders only (`<domain>`, `<vps>`, `apd.example.com`). Real hostnames, IP addresses and secrets never enter the repo. The one exception is the public URL of the live demo, which `README.md` links; nothing under `deploy/` names it (`tests/unit/test_backups.py` checks both).
- The API (`127.0.0.1:8100`) and the web client (`127.0.0.1:8101`) publish on `127.0.0.1` only. Docker writes its own iptables rules, so a port on `0.0.0.0` would bypass UFW.
- PostgreSQL has no published port and lives on the internal network.
- The n8n and website projects on the same host are never touched. The demo runs as its own system user, `apd`; the website's `deploy` user is never reused.
- Cost controls stay in layers: Anthropic workspace spend limit, daily LLM quota (`LLM_DAILY_LIMIT`), Nginx rate limit on analysis runs, schema limits.
- Security headers are set once, at server level in `apd.conf`, and only where the upstream response lacks them: the application owns its CSP. A location with its own `add_header` inherits none of them.
- Nginx zone names and fail2ban zone filters start with `apd_`, so they never match the other sites on the host.
- The API runs with `CREATE_SCHEMA_ON_STARTUP=false`. Alembic migrations run in a one-off container before a new version starts, never on API startup (RS-59).
- `deploy.sh` takes only a `vX.Y.Z` tag, from its argument or `SSH_ORIGINAL_COMMAND`, and never runs that value (RS-66). Each service keeps its own version in `.env`, `APD_VERSION` and `APD_WEB_VERSION`; a 2.x tag moves both, a 1.x tag the API only. It updates `.env` only after every moved service passes its check; on a failed check each service starts again on its previous version (RS-79).
- Routes live in `nginx/apd-routes.conf` only: `/api/` to FastAPI, `/ui/` answers 301 to `/`, the old `/docs`, `/redoc` and `/openapi.json` to FastAPI for their 301 to `/api/...`, everything else to Next.js (ADR 0016). The site and `edge.conf` define the upstreams `apd_api` and `apd_web` and the zones. No route sets `add_header`.
- The `deploy` job runs only in the `production` environment, which alone holds `DEPLOY_HOST`, `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS` and `DEMO_URL`. SSH uses `StrictHostKeyChecking=yes` against `DEPLOY_KNOWN_HOSTS` only, never `accept-new`. The tag reaches the scripts through `env`, never through `${{ }}` inside `run` (RS-67).
- The purge runs before the backup each night, so a backup holds at most one day of visitor data. `backup.sh` deletes dumps older than 7 days only after the new dump is complete. A restore rehearsal uses a container with no volume and no network (RS-68).

## Verify

```bash
docker compose -f deploy/compose.prod.yaml config
uv run pytest tests/unit/test_deploy_script.py tests/unit/test_release_deploy.py tests/unit/test_backups.py tests/unit/test_nginx_routes.py
shellcheck deploy/*.sh
```

CI starts both compose files in the `docker` job, checks the routes through the `edge` service on `:8080`, and runs `shellcheck` in `quality`; the script tests use fake `docker`, `ssh`, `curl` and `flock` commands. `sudo nginx -t` runs on the host only.

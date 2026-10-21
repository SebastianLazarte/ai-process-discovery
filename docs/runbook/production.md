# Production runbook

**Status:** in use. Block B11 (RS-59 to RS-68) is complete: the timers run on the host and the first restore rehearsal is recorded under "Backups and restore". The switch to the 2.0.0 layout (RS-79) has its own section. Decision records: ADR 0008, ADR 0016.

Placeholders: `<domain>` is the maintainer's domain, `<vps>` is the SSH host alias. Real hostnames, IP addresses and secrets never go into this repository.

## What runs where

| Piece | Where |
|---|---|
| Nginx, TLS (certbot) | Host system, ports 80 and 443, site `apd.<domain>` |
| API | `/opt/apd`, container `api`, `127.0.0.1:8100`, version `APD_VERSION` |
| Web client (Next.js) | `/opt/apd`, container `web`, `127.0.0.1:8101`, version `APD_WEB_VERSION`; public at `/` from 2.0.0 |
| PostgreSQL | `/opt/apd`, container `postgres`, internal network, volume `apd_pgdata` |
| Secrets | `/opt/apd/.env`, owner `apd`, mode `600` |
| Backups | `/var/backups/apd`, 7 days |
| Timers | `apd-backup.timer` (nightly), `apd-purge.timer` (daily) |
| n8n and the website | Their own projects, never touched by these procedures |

## One-time setup

Keep a second SSH session open during steps 1 and 2, so a mistake in the SSH configuration cannot lock you out.

1. **Harden the host.** Apply pending updates and enable `unattended-upgrades`. Add a 2 GB swap file. Create an admin user with `sudo` and an SSH key, then set `PermitRootLogin no` and `PasswordAuthentication no`. Enable UFW with 22, 80 and 443 only. Install fail2ban.
   The host also runs other projects, so check what is already in place before changing it: `sudo sshd -T`, `sudo ufw status verbose`, `sudo fail2ban-client status`, `swapon --show` and `apt list --upgradable`.
2. **Deploy user.** Create `apd`, add it to the `docker` group, and install the GitHub deploy key in its `authorized_keys` with `command="/opt/apd/deploy.sh",no-port-forwarding,no-agent-forwarding,no-X11-forwarding,no-pty`. Membership of `docker` is equivalent to root, which is why the key is restricted to one command. The user belongs to the demo only: another project's deploy user on the host keeps its own key, so neither key can deploy the other project.
3. **Project folder.** `/opt/apd` owned by `apd`, with `compose.yaml` (from `deploy/compose.prod.yaml`), `deploy.sh`, `backup.sh` and `restore-rehearsal.sh` (from `deploy/`, mode `755`) and `.env` from `deploy/.env.example`, with `APD_VERSION` and `APD_WEB_VERSION`. Create `/var/backups/apd` owned by `apd`, mode `700`, for the nightly and pre-deploy dumps.
4. **DNS and TLS.** Add an A record (and AAAA if IPv6 is served) for `apd.<domain>`. Issue the certificate first, because the site refers to it: `sudo certbot certonly --nginx -d apd.<domain> --deploy-hook "systemctl reload nginx"`. Then install `deploy/nginx/apd-routes.conf` as `/etc/nginx/snippets/apd-routes.conf` and `deploy/nginx/apd.conf` with `apd.<domain>` in place of `apd.example.com`, link the site into `sites-enabled`, run `sudo nginx -t` and reload Nginx.
   Then install `deploy/fail2ban/apd.local` as `/etc/fail2ban/jail.d/apd.local` and run `sudo fail2ban-client reload`. `sudo fail2ban-client status apd-limit-req` lists the jail; it bans a client that keeps getting 429 from the demo, and leaves the limits of other sites alone.
5. **Anthropic.** Create a workspace for the demo, set a monthly spend limit, create a key for that workspace only and put it in `.env`.
6. **GitHub.** Create the `production` environment and limit its deployment branches to `main`. Give it:
   - Secrets: `DEPLOY_HOST` (the host name or address the runner connects to), `DEPLOY_SSH_KEY` (the private half of the deploy key from step 2) and `DEPLOY_KNOWN_HOSTS` (output of `ssh-keyscan` for that same name, checked against the fingerprint shown on the server).
   - Variable: `DEMO_URL`, the public `https://apd.<domain>` address that the smoke test calls.

   When the host is ready, add the repository variable `DEPLOY_ENABLED` with the value `true`. Until then the `deploy` job is skipped and a release only publishes the images: `ai-process-discovery` and, from RS-77, `ai-process-discovery-web` with the same tag.
7. **Timers.** Install the units from `deploy/systemd/` and start the timers:

   ```bash
   sudo cp deploy/systemd/apd-* /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now apd-purge.timer apd-backup.timer
   systemctl list-timers 'apd-*'
   ```

   `apd-purge.timer` runs at 00:05 UTC and `apd-backup.timer` at 00:30 UTC, so a backup holds at most one day of visitor data. Both catch up after a reboot (`Persistent=true`).
8. **Monitor.** Optional external check on `https://apd.<domain>/api/health`.

## Deploy

Merging the release pull request deploys automatically. The `deploy` job of the `Release` workflow runs after `publish-image`, in the `production` environment:

1. `deploy/release-deploy.sh` connects as `apd` over SSH. It accepts only the host key in `DEPLOY_KNOWN_HOSTS`, so a changed key stops the deploy instead of being trusted, and sends the tag as the only command.
2. `deploy.sh` on the host does the work below.
3. `deploy/smoke-test.sh` calls `/` and `/api/health` on `DEMO_URL` over HTTPS. Any error fails the job.

To redeploy or roll back to a tag, run the `Release` workflow by hand (`workflow_dispatch`) with that tag. To repair from the server:

```bash
sudo -u apd /opt/apd/deploy.sh v1.2.1
```

`deploy.sh` backs up the database, pulls the images, runs `alembic upgrade head` in a one-off container, starts the new version and checks its health: `/api/health` on `127.0.0.1:8100` for the API and `/` on `127.0.0.1:8101` for the web client. If a check fails, each service starts again on the version it ran before, and the script exits with an error.

- It accepts one tag, `vX.Y.Z`, as its argument or, over SSH, in `SSH_ORIGINAL_COMMAND`. Anything else exits before a single command runs.
- Each service has its own version in `/opt/apd/.env`: `APD_VERSION` for the API and `APD_WEB_VERSION` for the web client (ADR 0016). A tag from `v2.0.0` on moves both; a 1.x tag moves the API only, because a 1.x web image serves its pages under `/app`.
- The script updates those lines only after every moved service passes its check, so after a rollback the file still names the versions that are running.
- When you copy a `deploy.sh` or `compose.prod.yaml` from a release with RS-79 onto a host that has only `APD_VERSION`, add `APD_WEB_VERSION` first, with the same value. Both files refuse to run without it.
- The pre-deploy dump is `/var/backups/apd/pre-deploy-<UTC time>-v<old>-to-v<new>.dump`.
- If the migration fails, the new version never starts and the old one keeps running. Restore the pre-deploy dump only if the migration left the schema half changed.
- A lock file, `/opt/apd/.deploy.lock`, stops a second deploy while one is running.

A failed `deploy` job leaves the previous version running when the health check on the host failed (`deploy.sh` rolled back). When only the smoke test failed, the new version passed its checks on the host but is not reachable from outside: check Nginx, the certificate and the DNS record.

To stop automatic deploys, for example to take the demo offline, set `DEPLOY_ENABLED` to anything but `true`.

## Switch to 2.0.0 (ADR 0016)

2.0.0 moves the public client from `/ui/` (FastAPI) to `/` (Next.js) and the API under `/api/` only. The change runs by hand, once, through states that always work. It ran on 2026-10-21 with no downtime; the 1.x site stays on the host as `sites-available/<site>.1x` and the S0 files and dump in a root-only backup folder.

The states:

| State | Nginx site | API | Web | Public client |
|---|---|---|---|---|
| S0 (before) | 1.x | 1.x | not routed | `/ui/` |
| S1 | 2.0.0 routes | 1.x, already under `/api/` | 2.0.0 | `/`, with `/ui/` answering 301 |
| S2 | 2.0.0 routes | 2.0.0 | 2.0.0 | `/` |

Keep `DEPLOY_ENABLED` off for the whole change, so a release cannot deploy halfway through it.

1. **New files.** From the `v2.0.0` tag, copy `deploy/compose.prod.yaml` to `/opt/apd/compose.yaml` and `deploy/deploy.sh` to `/opt/apd/deploy.sh`. Add `APD_WEB_VERSION=2.0.0` to `/opt/apd/.env`. Keep the current site as `/etc/nginx/sites-available/apd.conf.1x`, and copy `deploy/nginx/apd-routes.conf` to `/etc/nginx/snippets/`.
2. **Start the web client alone.** `cd /opt/apd && docker compose pull web && docker compose up -d web`, then `curl -sf http://127.0.0.1:8101/`. Nothing public changes yet.
3. **Switch Nginx (S1).** Install the 2.0.0 `apd.conf` with the real host name, run `sudo nginx -t` and `sudo systemctl reload nginx`. Run `deploy/smoke-test.sh https://apd.<domain>` and check that `curl -sI https://apd.<domain>/ui/` answers 301 to `/`.
4. **Move the API (S2).** `sudo -u apd /opt/apd/deploy.sh v2.0.0`. If a health check fails, the script returns to S1, which also works.
5. **Verify** the demo in a browser, then set `DEPLOY_ENABLED` back to `true`.

To go back to S0 from S1: restore `apd.conf.1x` as the site, reload Nginx and stop the web container (`docker compose stop web`).

## Schema migrations

Alembic owns the schema in production. The API runs with `CREATE_SCHEMA_ON_STARTUP=false`, so it never creates or changes a table itself. Migrations run from the release image in a one-off container, before the new version starts:

```bash
cd /opt/apd && docker compose run --rm api alembic upgrade head
```

`deploy.sh` runs it on every deploy. Run it by hand only to repair a deploy, with a backup first (next sections).

**Once, on the database that `create_all` built.** The live database of the first stage already has the tables of revision `0001`. Before starting the first release that contains RS-59, back it up and mark it as migrated instead of running the initial migration:

```bash
cd /opt/apd && docker compose run --rm api alembic stamp 0001
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic check
```

Stamp `0001` by name, not `head`: a later release may already carry newer revisions that this database still needs. `upgrade` then applies only those, and `check` confirms the schema matches the models.

## Roll back

Deploy the previous tag the same way. Migrations follow expand and contract: a release only adds columns or tables that the previous version can ignore, and removals ship one release later. That keeps the previous image compatible with the current schema. If a migration itself is wrong, restore the backup taken by that deploy (next section).

## Backups and restore

Dumps live in `/var/backups/apd`, owner `apd`, and never leave the host:

- `nightly-<UTC time>.dump`, written by `backup.sh` from `apd-backup.timer`.
- `pre-deploy-<UTC time>-v<old>-to-v<new>.dump`, written by `deploy.sh`.

`backup.sh` deletes every dump older than 7 days, but only after that night's dump is complete. Check the last run with `journalctl -u apd-backup.service -n 20`.

**Rehearse a restore** after go-live and then once a month:

```bash
sudo -u apd /opt/apd/restore-rehearsal.sh
```

It loads the newest nightly dump, or the dump given as argument, into a throwaway PostgreSQL container with no volume and no network, counts the rows of each table and prints a row for the table below. Add that row in a pull request.

**Restore for real** when the volume is lost or a migration went wrong: stop the API (`docker compose stop api`), drop and recreate the `apd` database in the `postgres` container, load the dump with `docker compose exec -T postgres pg_restore --username=apd --dbname=apd --no-owner < <dump>`, start the API and check `/api/health`.

| Date | Dump | Result |
|---|---|---|
| 2026-10-21 | nightly-20261021T080055Z.dump | Restored: processes 0, process_steps 0, analyses 0, recommendation_overrides 0. The purge had just deleted the only process, so the schema restored with no rows |
| 2026-10-21 | pre-deploy-20261021T072028Z-v1.4.0-to-v2.0.0.dump | Restored: processes 1, process_steps 7, analyses 1, recommendation_overrides 0 |

## Purge demo data

The banner promises that visitor data is deleted daily. The purge command deletes every process created more than 24 hours ago, with its steps, analyses and overrides. Editing a process does not extend its life. No HTTP route can trigger it.

```bash
cd /opt/apd && sudo docker compose exec -T api python -m app.purge --older-than-hours 24
```

It logs one `demo_data_purged` event with the number of processes deleted. `apd-purge.timer` runs it daily at 00:05 UTC, just after the daily LLM quota resets: the quota counts the day's analyses, so a purge later in the day would delete some of them and free quota early. Check the last run with `journalctl -u apd-purge.service -n 20`.

## Rotate the Anthropic key

Create a new key in the demo workspace, replace it in `/opt/apd/.env`, run `docker compose up -d api` in `/opt/apd`, run one analysis with the LLM, then revoke the old key.

## When something goes wrong

| Symptom | Check | Action |
|---|---|---|
| Analyses show "LLM unavailable" all day | Log events `llm_unavailable` with `error_kind` | `daily_quota`: expected until midnight UTC. Otherwise check the Anthropic spend limit and the key |
| Many 429 responses | Nginx access log for `/analyses` | Expected under a burst. Tune `limit_req` only if real visitors are blocked |
| A visitor cannot connect at all | `sudo fail2ban-client status apd-limit-req` | Banned for an hour after repeated 429. Lift it with `sudo fail2ban-client set apd-limit-req unbanip <ip>` |
| `/api/health` returns 503 | `docker compose ps`, `docker compose logs postgres` | Restart `postgres`; restore from backup if the volume is damaged |
| Host slow, n8n affected | `docker stats`, `free -h`, `df -h` | Stop the demo with `docker compose stop api`; n8n and the website keep running |
| Certificate expiry warning | `sudo certbot renew --dry-run` | Fix renewal, then reload Nginx |

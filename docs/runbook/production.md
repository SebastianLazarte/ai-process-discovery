# Production runbook

**Status:** draft. Commands that use files under `deploy/` become valid as the B11 pull requests land (RS-59 to RS-68). Decision record: ADR 0008.

Placeholders: `<domain>` is the maintainer's domain, `<vps>` is the SSH host alias. Real hostnames, IP addresses and secrets never go into this repository.

## What runs where

| Piece | Where |
|---|---|
| Nginx, TLS (certbot) | Host system, ports 80 and 443, site `apd.<domain>` |
| API | `/opt/apd`, container `api`, `127.0.0.1:8100` |
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
3. **Project folder.** `/opt/apd` owned by `apd`, with `compose.yaml` (from `deploy/compose.prod.yaml`), `deploy.sh` and `.env` from `deploy/.env.example`.
4. **DNS and TLS.** Add an A record (and AAAA if IPv6 is served) for `apd.<domain>`. Issue the certificate first, because the site refers to it: `sudo certbot certonly --nginx -d apd.<domain> --deploy-hook "systemctl reload nginx"`. Then install `deploy/nginx/apd.conf` with `apd.<domain>` in place of `apd.example.com`, link it into `sites-enabled`, run `sudo nginx -t` and reload Nginx.
   Then install `deploy/fail2ban/apd.local` as `/etc/fail2ban/jail.d/apd.local` and run `sudo fail2ban-client reload`. `sudo fail2ban-client status apd-limit-req` lists the jail; it bans a client that keeps getting 429 from the demo, and leaves the limits of other sites alone.
5. **Anthropic.** Create a workspace for the demo, set a monthly spend limit, create a key for that workspace only and put it in `.env`.
6. **GitHub.** Create the `production` environment with `DEPLOY_SSH_KEY` and `DEPLOY_KNOWN_HOSTS` (output of `ssh-keyscan` for the host, checked against the fingerprint shown on the server).
7. **Timers.** Install and enable `apd-backup.timer` and `apd-purge.timer`.
8. **Monitor.** Optional external check on `https://apd.<domain>/health`.

## Deploy

Merging the release pull request deploys automatically. To redeploy a tag by hand, run the `Release` workflow with `workflow_dispatch` and the tag, or from the server:

```bash
sudo -u apd /opt/apd/deploy.sh v1.2.1
```

`deploy.sh` backs up the database, pulls the image, runs `alembic upgrade head` in a one-off container, starts the new version and checks `/health`. If the check fails, it starts the previous tag again and exits with an error.

## Roll back

Deploy the previous tag the same way. Migrations follow expand and contract: a release only adds columns or tables that the previous version can ignore, and removals ship one release later. That keeps the previous image compatible with the current schema. If a migration itself is wrong, restore the backup taken by that deploy (next section).

## Backups and restore

Nightly dumps and pre-deploy dumps live in `/var/backups/apd`. To rehearse a restore, load a dump into a scratch database and run a few reads against it. Record the date of the last rehearsal here.

| Date | Dump | Result |
|---|---|---|
| | | |

## Rotate the Anthropic key

Create a new key in the demo workspace, replace it in `/opt/apd/.env`, run `docker compose up -d api` in `/opt/apd`, run one analysis with the LLM, then revoke the old key.

## When something goes wrong

| Symptom | Check | Action |
|---|---|---|
| Analyses show "LLM unavailable" all day | Log events `llm_unavailable` with `error_kind` | `daily_quota`: expected until midnight UTC. Otherwise check the Anthropic spend limit and the key |
| Many 429 responses | Nginx access log for `/analyses` | Expected under a burst. Tune `limit_req` only if real visitors are blocked |
| A visitor cannot connect at all | `sudo fail2ban-client status apd-limit-req` | Banned for an hour after repeated 429. Lift it with `sudo fail2ban-client set apd-limit-req unbanip <ip>` |
| `/health` returns 503 | `docker compose ps`, `docker compose logs postgres` | Restart `postgres`; restore from backup if the volume is damaged |
| Host slow, n8n affected | `docker stats`, `free -h`, `df -h` | Stop the demo with `docker compose stop api`; n8n and the website keep running |
| Certificate expiry warning | `sudo certbot renew --dry-run` | Fix renewal, then reload Nginx |

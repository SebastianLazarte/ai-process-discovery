# ADR 0008: Public demo on the maintainer's VPS

**Status:** accepted · 2026-10-13 · amends PDR 001 (non-goal "No hosted public deployment"); layout amended by ADR 0009

## Context

Version 1.0.0 ships as an image on `ghcr.io` with SBOM and provenance, but nothing runs it in public. The portfolio needs a live URL. Three earlier decisions block that as they stand:

- PDR 001 lists "No hosted public deployment" and "No authentication".
- `SECURITY.md` says the demo must not be exposed on a public network with real data.
- ADR 0002 creates tables with `create_all` and asks for migrations before users keep data.

A public endpoint with `LLM_PROVIDER=anthropic` also lets anyone spend the API key.

The maintainer already runs a VPS (Ubuntu 26.04 LTS, 2 vCPU, 8 GB RAM, about 1 GB in use) with n8n in Docker Compose and a website. Nginx on the host terminates TLS on ports 80 and 443; n8n is published on `127.0.0.1` only.

## Decision

**Audience.** A public portfolio demo, without login. Visitors are told that data is public and deleted daily. Real business data is out of scope.

**Platform.** The existing VPS. It runs the same image that CI tested and the release published, costs nothing extra, and its Nginx gives rate limiting at no cost.

**Layout.**

| Piece | Choice |
|---|---|
| Compose project | Separate project in `/opt/apd`; the n8n and website projects stay untouched |
| API | Release image pinned to `X.Y.Z`, published on `127.0.0.1:8100` only, non-root, read-only root filesystem, memory and CPU limits, rotated logs |
| Database | Its own PostgreSQL container on an internal network, no published port, named volume |
| Edge | Host Nginx site `apd.<domain>`: TLS from certbot, `limit_req` on analysis runs, `client_max_body_size`, read timeout above the LLM timeout |
| Secrets | `/opt/apd/.env` with mode `600`. GitHub holds only the deploy key and the pinned host key |

Docker writes its own iptables rules, so a port published on `0.0.0.0` bypasses UFW. Binding to `127.0.0.1` keeps the API reachable only through Nginx.

**Schema.** Alembic migrations replace `create_all` in production (`create_schema_on_startup=false`). Migrations run before the new version starts, as a one-off container from the same image, never on application startup.

**Cost controls, in layers.**

1. A dedicated Anthropic workspace with a monthly spend limit and its own key.
2. A daily LLM quota counted in the database. Past it, the analysis still runs and reports `llm_status=unavailable` with `error_kind=daily_quota`. The response contract does not change, and the LLM still produces no number.
3. Nginx rate limit per client IP on `POST /processes/{id}/analyses`.
4. Schema limits on steps per process, text lengths and list sizes, which also bound the prompt size.

**Data retention.** A systemd timer runs a purge command inside the API container every day. There is no administrative HTTP endpoint.

**Backups.** `pg_dump` before every migration and every night, kept for 7 days. A restore is rehearsed before go-live.

**Delivery.** The `release` workflow gains a `deploy` job after `publish-image`, in the `production` environment. It connects over SSH with a key whose `authorized_keys` entry forces `deploy.sh`, so the key can only deploy a tag. `deploy.sh` validates the tag, backs up, pulls, migrates, starts, checks `/health` and restores the previous tag if the check fails. A smoke test then calls `/health` and `/ui/` over HTTPS. A manual dispatch with a tag covers redeploys and rollbacks.

**Out of scope.** Streamlit is not deployed; it leaves in 1.2.0 (ADR 0007).

The requirements for this block are RS-59 to RS-68 in `docs/requirements.toml` (block B11). Operations are in `docs/runbook/production.md`.

**Rollout, in three stages.**

| Stage | Requirements | Exit condition |
|---|---|---|
| 1. Go live | RS-60, RS-61, RS-62, RS-64, RS-65, host hardening, manual deploy | The URL is public with limits, quota, banner, TLS and rate limiting |
| 2. Consolidate | RS-63, RS-59 | Automatic purge; migrations in place before the first schema change in production |
| 3. Automate | RS-66, RS-67, RS-68 | Deploys from the release workflow with automatic rollback; backups with a rehearsed restore |

Stage 1 creates tables with `create_all`. When RS-59 lands, the initial migration matches that schema and the live database is stamped with `alembic stamp head`. Until the purge is automatic, the banner says data is deleted periodically and the purge runs by hand.

## Consequences

- The live demo runs the exact artifact that passed CI, and a rollback means starting the previous tag.
- The demo shares a host with n8n and the website. Resource limits, separate networks and localhost binding contain a failure, and the host is hardened as part of go-live (updates, swap, SSH keys only, no root login, UFW, fail2ban).
- The maintainer operates the server: patches, disk, certificates and backups. The runbook records each task.
- One host is a single point of failure. A portfolio demo accepts that.
- Visitor data is public and short-lived by design, which the banner and `SECURITY.md` state.

## Alternatives considered

| Option | Why not |
|---|---|
| Vercel | Rebuilds from source with its Python runtime, so production would not run the tested image (its container runtime is in beta). Needs a serverless rework: no disk, connection pooling, Streamlit unsupported |
| Google Cloud Run with Neon | Strong second choice: same image, scales to zero, keyless deploys. Longer setup (project, IAM, billing) and no free rate limiting |
| Railway or Render | Simple, but a monthly fee, and Render's free database expires after 30 days |
| Fly.io | No free allowance for new organizations |

## How to revert

- To take the demo offline: disable the Nginx site, run `docker compose down` in `/opt/apd`, and remove the `deploy` job.
- To move to Cloud Run: the image, the migrations, the quota and the purge command carry over. Replace the SSH deploy with a Cloud Run deploy and use a managed PostgreSQL.

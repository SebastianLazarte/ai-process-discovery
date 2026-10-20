# Next.js client

The client that replaces `web/` (block B12): Next.js App Router, strict TypeScript, Tailwind, pnpm, Node 22. It runs as its own service under `/app` until 2.0.0 moves it to `/`.

## Read

- `docs/adr/0009-nextjs-frontend-as-separate-service.md`: service, routing, client rules, dependencies
- `docs/adr/0013-design-system-and-design-to-code.md`: tokens, themes, accessibility, fonts
- `docs/design/`: the brief and the spec of the screen you are building

## Rules

- Hard rule 7, in detail:
  - The client never computes a metric. It prints the figures the API returns, and only `src/lib/format` turns them into text.
  - Only `src/lib/api/` calls `fetch`. Lint fails anywhere else. Components import from `@/lib/api`: the typed `api` client and `unwrap()`, which turns every failure into an `ApiError`.
  - `dangerouslySetInnerHTML` is forbidden everywhere, including `src/lib/api/`. Lint fails on the attribute and on a props object that carries it.
- A package that ADR 0009 or ADR 0013 does not name needs an ADR. Versions are exact in `package.json`, and a new one is at least a week old (ADR 0010).
- Colours, radii and fonts come from `src/styles/tokens.css` through semantic utilities (`bg-surface`, `text-muted`, `border-line`). The default Tailwind palette is switched off, and `src/styles/tokens.test.ts` fails on a colour literal, a palette class or a text pair below WCAG AA (ADR 0013, ADR 0014).
- Tests query by accessible role and name (`getByRole`), never by class or test id.
- Component tests render with `renderWithProviders` (`src/test/render.tsx`) and answer requests with `fakeApi` (`src/test/fake-api.ts`), so the real client, query cache and toast run in every test.
- Option lists match the domain enums from `/api/meta`.
- `openapi.json` is generated from the API (`uv run python scripts/export_openapi.py` at the root), and `src/lib/api/schema.d.ts` from it (`pnpm api:types`). Neither is edited by hand, and CI fails when either is stale. Paths are relative to the `/api` server.
- The image (RS-77): `Dockerfile` builds the `output: 'standalone'` server in stages and runs it as the `node` user on a read-only root, with its two runtime caches (`.next/cache`, `.next/server/route-cache`) on tmpfs. Server-side reads reach the API at `API_INTERNAL_URL`, read at runtime (default `http://api:8000`, the compose service). The browser calls `/api/` on its own origin, which Nginx routes in production; the `/api` rewrite in `next.config.ts` is baked in at build time, so it stays a development-only convenience. A new runtime folder (such as `public/`) needs its own `COPY` in the last stage.
- Errors (RS-71): a 422 that names fields goes to the form through `applyFieldErrors`, and every other failed request shows its message in the toast, from the query and mutation caches in `src/app/providers.tsx`. A form never shows a toast for its own field errors.

## Verify

```bash
cd frontend
pnpm install
pnpm lint && pnpm format && pnpm typecheck && pnpm test && pnpm build
```

The image, from the repository root (CI does the same in the `docker` job):

```bash
docker compose up --build --wait web
curl --fail http://localhost:3000/app
```

Without `corepack enable` (it needs admin rights on Windows), prefix each command with `corepack`: `corepack pnpm test`.

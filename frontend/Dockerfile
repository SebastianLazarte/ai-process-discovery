# The Next.js client (ADR 0009, RS-77), published as ai-process-discovery-web.
# Build context is frontend/:
#   docker build -t ai-process-discovery-web:local frontend
# Node 22 matches .nvmrc and engines; the slim (glibc) base matches the CI runner, so the
# native build tools in the lockfile resolve the same packages.
FROM node:22-slim AS base
ENV NEXT_TELEMETRY_DISABLED=1 \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0
WORKDIR /build

# Dependencies first, so source changes do not invalidate this layer. corepack installs
# the pnpm that packageManager pins, checked against its hash.
FROM base AS deps
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM deps AS build
COPY . .
RUN pnpm build

# Only the standalone server and its static assets: no pnpm, no source, no dev packages.
FROM node:22-slim AS runtime
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    API_INTERNAL_URL=http://api:8000
WORKDIR /app

# Owned by root and read-only for the node user. At runtime Next writes only to
# .next/cache and to the rendered-page cache in .next/server/route-cache; compose mounts
# both as tmpfs when the root filesystem is read-only.
COPY --from=build /build/.next/standalone ./
COPY --from=build /build/.next/static ./.next/static
# A public/ folder, once the client has one, is copied here too: ./public.
RUN mkdir -p .next/cache .next/server/route-cache \
    && chown node:node .next/cache .next/server/route-cache
USER node

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then((r) => process.exit(r.ok ? 0 : 1), () => process.exit(1))"]

CMD ["node", "server.js"]

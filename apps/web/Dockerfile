FROM node:20-alpine AS base
RUN corepack enable pnpm

# Install deps with full workspace context so workspace:* deps resolve
FROM base AS deps
WORKDIR /repo
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY packages/ ./packages/
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /repo
COPY --from=deps /repo/node_modules ./node_modules
COPY packages/ ./packages/
COPY apps/web/ ./apps/web/
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /repo/apps/web
RUN pnpm build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /repo/apps/web/.next ./.next
COPY --from=builder /repo/apps/web/public ./public
COPY --from=builder /repo/node_modules ./node_modules
COPY --from=builder /repo/apps/web/package.json ./package.json

EXPOSE 3000
CMD ["node_modules/.bin/next", "start"]

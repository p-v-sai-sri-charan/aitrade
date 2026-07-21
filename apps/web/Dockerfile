# Build context is the repo root (see docker-compose.yml) because the web
# app depends on the local packages/shared-types and packages/voice
# workspace packages.
FROM node:20-slim AS build

WORKDIR /repo
COPY package.json ./
COPY packages/shared-types ./packages/shared-types
COPY packages/voice ./packages/voice
COPY apps/web ./apps/web

RUN npm install

WORKDIR /repo/apps/web
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ARG VITE_WS_BASE_URL=ws://localhost:8000/ws
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL
RUN npm run build

FROM node:20-slim AS runtime
WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /repo/apps/web/dist ./dist
EXPOSE 4173
CMD ["serve", "-s", "dist", "-l", "4173"]

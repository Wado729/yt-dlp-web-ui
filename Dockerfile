FROM node:24-slim AS ui
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack prepare pnpm@11.4.0 --activate && corepack enable
COPY . /usr/src/yt-dlp-webui

WORKDIR /usr/src/yt-dlp-webui/frontend

RUN rm -rf node_modules

RUN pnpm install
RUN pnpm build



FROM golang AS build

WORKDIR /usr/src/yt-dlp-webui

COPY . .
COPY --from=ui /usr/src/yt-dlp-webui/frontend /usr/src/yt-dlp-webui/frontend

RUN CGO_ENABLED=0 GOOS=linux go build -o yt-dlp-webui



FROM python:alpine

# CI passes the newest PyPI release; this default keeps local builds reproducible.
# Bumping the version also busts the build cache for this layer.
ARG YTDLP_VERSION=2026.10.26

RUN apk update && \
    apk add ffmpeg ca-certificates curl wget gnutls deno --no-cache && \
    pip install --no-cache-dir "yt-dlp[default,curl-cffi,secretstorage]${YTDLP_VERSION:+==${YTDLP_VERSION}}"

LABEL org.opencontainers.image.yt-dlp-version="${YTDLP_VERSION}"

VOLUME /downloads /config

WORKDIR /app

COPY --from=build /usr/src/yt-dlp-webui/yt-dlp-webui /app

# Site-specific yt-dlp extractor plugins (picked up from yt-dlp's system plugin dir)
COPY yt-dlp-plugins /etc/yt-dlp/plugins

ENV APP_PATHS_DOWNLOAD_PATH="/downloads"
ENV APP_PATHS_LOCAL_DATABASE_PATH="/config"
ENV APP_PATHS_JS_RUNTIME_PATH="deno:/usr/bin/deno"

EXPOSE 3033
ENTRYPOINT [ "./yt-dlp-webui", "--conf", "/config/config.yml"]

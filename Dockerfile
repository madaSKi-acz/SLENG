# Purpose: One image with the built web UI and the engine (all extras), served by `sleng serve`.
# Layer:   deployment. Build: docker build -t sleng .   Run: docker run -p 7860:7860 -v sleng:/data sleng
# Notes:   No authentication inside: expose it only behind a reverse proxy that adds auth + TLS.

FROM node:22-slim AS web
WORKDIR /app/web
COPY web/package*.json ./
RUN npm install
COPY web/ ./
COPY engine/src/sleng/assets/fonts /app/engine/src/sleng/assets/fonts
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    SLENG_DATA_DIR=/data \
    SLENG_WEB_DIST=/app/web/dist
WORKDIR /app
COPY engine/ engine/
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu "./engine[all]" \
 && pip install --no-cache-dir --no-deps \
    https://github.com/myshell-ai/OpenVoice/archive/refs/heads/main.zip
COPY --from=web /app/web/dist web/dist
VOLUME /data
EXPOSE 7860
CMD ["sleng", "serve", "--host", "0.0.0.0", "--port", "7860", "--no-browser"]

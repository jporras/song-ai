FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build


FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY tools ./tools
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV SONG_AI_MODEL_ROOT=/app/models
ENV SONG_AI_PROVIDER_ROOT=/app/providers
ENV SONG_AI_PROVIDER_CACHE=/app/provider-cache
ENV HF_HOME=/app/models/huggingface
ENV PYTHONPATH=/app/provider-cache/python:/app/backend

EXPOSE 8000

CMD ["python", "backend/server.py"]

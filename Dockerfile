FROM node:20-bookworm-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip ffmpeg git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend ./frontend
WORKDIR /app/frontend
RUN npm install && npm run build

WORKDIR /app
COPY backend ./backend
COPY tools ./tools

ENV PYTHONUNBUFFERED=1
ENV SONG_AI_MODEL_ROOT=/app/models
ENV SONG_AI_PROVIDER_ROOT=/app/providers
ENV SONG_AI_PROVIDER_CACHE=/app/provider-cache
ENV HF_HOME=/app/models/huggingface
ENV PYTHONPATH=/app/provider-cache/python:/app/backend

EXPOSE 8000

CMD ["python", "backend/server.py"]

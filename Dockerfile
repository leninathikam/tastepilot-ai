FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV BACKEND_URL=http://127.0.0.1:8000
RUN npm run build

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && rm -rf /var/lib/apt/lists/*
COPY --from=frontend-build /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY scripts/serve.py scripts/serve.py
COPY --from=frontend-build /build/frontend/.next/standalone ./frontend
COPY --from=frontend-build /build/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-build /build/frontend/public ./frontend/public
ENV DATA_MODE=fixture PORT=3000 NEXT_TELEMETRY_DISABLED=1
RUN useradd --create-home appuser && mkdir -p /app/frontend/.next/cache && chown -R appuser:appuser /app && chmod 1777 /app/frontend/.next/cache
USER appuser
EXPOSE 3000
CMD ["python", "scripts/serve.py"]

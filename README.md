# Prometheus Observability Service

FastAPI service with a live Prometheus request counter, uptime health check, and structured JSON request logs.

## Endpoints

- `GET /work?n=K` returns `{"email":"...","done":K}`
- `GET /metrics` exposes the live `http_requests_total` counter in Prometheus text format
- `GET /healthz` returns status and uptime in seconds
- `GET /logs/tail?limit=N` returns the most recent structured request logs

Every request is counted by middleware, including requests to metrics, health, work, and logs. Logs include `level`, `ts`, `path`, and `request_id`.

## Deploy to Vercel

Import this repository into Vercel. Set environment variable `EMAIL` to your logged-in email address, then deploy. Submit the production base URL without an endpoint path.

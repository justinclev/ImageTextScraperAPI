# ImageTextScraperAPI

A FastAPI-based OCR service that extracts word-level tokens (with confidence and bounding boxes) plus full text from uploaded images.

## Tech Stack

- Python 3.11
- FastAPI + Pydantic
- Tesseract OCR (`pytesseract`)
- Docker (multi-stage, non-root runtime)
- Pytest

## API

### Health Check

- `GET /health`
- Returns service status and version

### OCR Extraction

- `POST /api/v1/ocr/extract`
- `multipart/form-data` with `file`
- Accepted content types: `image/jpeg`, `image/png`, `image/tiff`, `image/webp`
- Max file size: 10MB
- In-memory rate limit: 20 OCR requests/minute per client IP

### Metrics

- `GET /metrics`
- Prometheus-style counters for request volume, duration, and OCR outcomes

Example request:

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample.png;type=image/png"
```

Example response:

```json
{
	"filename": "sample.png",
	"total_tokens": 3,
	"tokens": [
		{
			"text": "Hello",
			"confidence": 96.8,
			"x": 42,
			"y": 18,
			"width": 88,
			"height": 28
		}
	],
	"full_text": "Hello world"
}
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Open docs at:

- `http://localhost:8000/docs`

## Docker

```bash
docker-compose up --build
```

## Testing

```bash
pytest -q
```

Current test coverage includes:

- Unit tests for endpoint validation and error mapping
- Integration tests with a real PNG fixture at `tests/fixtures/sample_hello.png`
- Request-ID propagation checks (`X-Request-ID` in responses)
- Rate-limit behavior and timeout mapping tests
- Metrics endpoint assertions

## CI Quality Gates

This repository runs the following checks in GitHub Actions:

- `lint` (`ruff check .`)
- `typecheck` (`mypy src`)
- `test` (`pytest -q`)
- `quality-gate` (depends on all checks above)

To enforce as required checks on GitHub:

1. Go to repository **Settings** → **Branches**.
2. Add or edit a protection rule for `main`.
3. Enable **Require status checks to pass before merging**.
4. Select `quality-gate` (or all of `lint`, `typecheck`, `test`) as required.

## Design Notes

- Endpoint layer validates request shape and maps domain errors to HTTP responses.
- Service layer encapsulates OCR/image parsing logic.
- OCR result includes token-level geometry for downstream indexing/highlighting.

## Architecture

```text
Client
  │
  ├── POST /api/v1/ocr/extract
  │      ├── Request middleware (request_id + request metrics)
  │      ├── Endpoint validation + rate-limit guard
  │      ├── OCR service (image verify + tesseract + timeout)
  │      └── Structured JSON logs + OCR outcome metrics
  │
  └── GET /metrics
			└── Prometheus text output from in-memory counters
```

## Tradeoffs / ADR Summary

1. **In-memory rate limiter over Redis**
	- Chosen for MVP simplicity and zero external dependency.
	- Tradeoff: limits are per-process (not shared across multiple replicas).

2. **In-memory metrics over dedicated telemetry stack**
	- Chosen for low setup overhead and easy local/CI verification.
	- Tradeoff: counters reset on restart and are not durable.

3. **Synchronous OCR in request path over queued async worker**
	- Chosen for straightforward API semantics and easier local development.
	- Tradeoff: request latency directly includes OCR runtime.

4. **Hard timeout for OCR extraction (8s)**
	- Chosen to protect API responsiveness under complex images.
	- Tradeoff: long-running OCR jobs are rejected instead of eventually completing.

## Observability

- Request-scoped correlation IDs are supported through `X-Request-ID`.
  - If provided by the client, the same ID is echoed in the response.
  - If absent, the API generates a UUID and returns it in `X-Request-ID`.
- Logs are emitted as structured JSON (timestamp, level, logger, message, request_id, event fields).
- Request lifecycle events are logged (`request_started`, `request_completed`, `request_failed`) with method/path/status/duration.
- A Prometheus-style `/metrics` endpoint exports:
	- `http_requests_total`
	- `http_request_duration_seconds_sum`
	- `ocr_requests_total` by outcome (`success`, `rate_limited`, `ocr_error`, etc.)

### Prometheus + Grafana Quick Start

Minimal `prometheus.yml` scrape config:

```yaml
global:
	scrape_interval: 5s

scrape_configs:
	- job_name: imagetextscraperapi
		static_configs:
			- targets: ["host.docker.internal:8000"]
		metrics_path: /metrics
```

Run Prometheus locally:

```bash
docker run --rm -p 9090:9090 \
	-v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
	prom/prometheus
```

Run Grafana locally:

```bash
docker run --rm -p 3000:3000 grafana/grafana
```

Grafana setup:

1. Add data source: Prometheus URL `http://host.docker.internal:9090`.
2. Create panels for:
	 - Request rate: `sum(rate(http_requests_total[1m]))`
	 - OCR success rate: `sum(rate(ocr_requests_total{outcome="success"}[5m]))`
	 - Error rate: `sum(rate(ocr_requests_total{outcome!="success"}[5m]))`

## Resilience Controls

- **Rate limit:** 20 OCR requests/minute per client IP (`429` + `Retry-After`).
- **OCR timeout:** 8-second cap on tesseract extraction to prevent pathological request hangs.
- **Validation guards:** content type allowlist, non-empty file, and max upload size enforcement.

## Performance Baseline

Local baseline (macOS, Python 3.11, Tesseract via Homebrew), measured against
`tests/fixtures/sample_hello.png` with 5 warmup runs + 30 measured runs:

- Average latency: ~151.94 ms/request
- P50 latency: ~149.22 ms
- P95 latency: ~164.82 ms
- Single-worker throughput: ~6.58 requests/second

These numbers are intended as a practical baseline and will vary by hardware,
image complexity, and deployment profile.

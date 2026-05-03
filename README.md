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

## Design Notes

- Endpoint layer validates request shape and maps domain errors to HTTP responses.
- Service layer encapsulates OCR/image parsing logic.
- OCR result includes token-level geometry for downstream indexing/highlighting.

# Urban Heat Intelligence — API

FastAPI backend for the Urban Heat Intelligence Web GIS.

## Stack

- Python 3.11 · FastAPI · Uvicorn · Pydantic (settings)
- Testing: pytest + httpx `TestClient`

## Setup

```bash
cd apps/api
python -m venv .venv

# Windows (bash):
.venv/Scripts/python -m pip install -r requirements.txt
# macOS/Linux:
# .venv/bin/python -m pip install -r requirements.txt

cp .env.example .env   # then edit if needed
```

## Run

```bash
.venv/Scripts/python -m uvicorn app.main:app --reload
```

- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

## Test

```bash
.venv/Scripts/python -m pytest
```

## Layout

```text
app/
├── main.py             # application factory + CORS
├── core/config.py      # settings from env / .env
└── api/
    ├── router.py       # versioned router (/api/v1)
    └── routes/         # endpoint modules (health)
tests/                  # pytest suite
```

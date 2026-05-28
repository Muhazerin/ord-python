# FastAPI demo

Tiny end-to-end example showing how to publish an ORD document for a FastAPI service.

## Files

- `main.py` — a one-route FastAPI app.
- `emit_ord.py` — builds the ORD document for that app, validates it against the official spec, prints it.

## Run

From this directory, with the dev install (`pip install -e ".[dev]"` from the repo root):

```bash
python emit_ord.py
```

Expected output is a multi-line JSON document with `apiResources[0].apiProtocol == "rest"` and a `resourceDefinitions` entry pointing at `/openapi.json`.

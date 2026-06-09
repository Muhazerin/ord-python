# FastAPI demo

End-to-end example showing how to publish an ORD document for a FastAPI service three different ways: as a one-shot print, as live discovery endpoints, and as static files via the `ord build` CLI.

## Files

- `main.py` — a one-route FastAPI app that also mounts the ORD discovery endpoints (`/.well-known/open-resource-discovery` and `/ord/v1/documents/ord-document`).
- `emit_ord.py` — builds the same ORD document the app would serve, validates it against the official spec, prints it.
- `pyproject.toml` — declares `[tool.ord]` so the `ord build` CLI knows which app to inspect and what identity to give the resulting APIResource.

## Run

From this directory, with the dev install (`pip install -e ".[dev]"` from the repo root):

### Print the document once

```bash
python emit_ord.py
```

Expected output is a multi-line JSON document with `apiResources[0].apiProtocol == "rest"` and a `resourceDefinitions` entry pointing at `/openapi.json`.

### Serve the discovery endpoints

```bash
uvicorn main:app
```

Then in another shell:

```bash
curl http://127.0.0.1:8000/.well-known/open-resource-discovery
curl http://127.0.0.1:8000/ord/v1/documents/ord-document
curl http://127.0.0.1:8000/openapi.json
```

The well-known response is a small Configuration manifest pointing at the document endpoint. The document endpoint returns the full ORD payload.

### Build static artifacts with the CLI

```bash
ord build
```

Reads `[tool.ord]` from `pyproject.toml`, validates the resulting document against the spec, and writes:

- `gen/ord/ord-document.json` — the ORD document.
- `gen/ord/well-known.json` — the Configuration manifest pointing at the document file.

Override the output directory with `--out`. Useful in CI when you want to commit the artifacts or upload them somewhere static.

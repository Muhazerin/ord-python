# FastAPI demo

End-to-end example showing how to publish an ORD document for a FastAPI service, both as a one-shot print and as live discovery endpoints.

## Files

- `main.py` — a one-route FastAPI app that also mounts the ORD discovery endpoints (`/.well-known/open-resource-discovery` and `/ord/v1/documents/ord-document`).
- `emit_ord.py` — builds the same ORD document the app would serve, validates it against the official spec, prints it.

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

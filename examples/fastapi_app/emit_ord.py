"""Build, validate, and print the ORD document for the demo FastAPI app.

This is a smoke test for the FastAPI adapter — for the runtime discovery
endpoints, see ``main.py`` (mounts ``ord_router`` on the app) and run
``uvicorn main:app``.
"""

from __future__ import annotations

from main import _build_ord_document


def main() -> None:
    doc = _build_ord_document()
    doc.validate_against_spec()
    print(doc.to_ord_json(indent=2))


if __name__ == "__main__":
    main()

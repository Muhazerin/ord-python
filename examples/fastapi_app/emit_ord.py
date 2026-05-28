"""Build, validate, and print the ORD document for the demo FastAPI app.

This is a smoke test for the FastAPI adapter, not a production discovery
endpoint — for that, see step 5 (``server.py``) once it lands.
"""

from __future__ import annotations

from main import app

from ord.adapters.fastapi import apiresource_from_fastapi
from ord.core.models import ORDDocument


def build_document() -> ORDDocument:
    api = apiresource_from_fastapi(
        app,
        ord_id="sap.demo:apiResource:Greeter:v1",
        title=app.title,
        short_description="Returns a friendly hello.",
        description=app.description or "Returns a friendly hello.",
        part_of_package="sap.demo:package:Default:v1",
        version=app.version,
        visibility="public",
        release_status="active",
    )
    return ORDDocument(api_resources=[api])


def main() -> None:
    doc = build_document()
    doc.validate_against_spec()
    print(doc.to_ord_json(indent=2))


if __name__ == "__main__":
    main()

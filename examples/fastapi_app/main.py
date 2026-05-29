"""Tiny FastAPI app used to demonstrate the ORD adapter end-to-end.

Two ways to use this:

- ``python emit_ord.py`` to print the validated ORD document to stdout.
- ``uvicorn main:app`` to serve the ORD discovery endpoints alongside the
  app's own routes (``/.well-known/open-resource-discovery`` and
  ``/ord/v1/documents/ord-document``).
"""

from __future__ import annotations

from fastapi import FastAPI

from ord.adapters.fastapi import apiresource_from_fastapi
from ord.core.models import ORDDocument
from ord.server import ord_router

app = FastAPI(
    title="Demo Greeter Service",
    version="1.0.0",
    description="Returns a friendly hello.",
)


@app.get("/hello")
def hello(name: str = "world") -> dict[str, str]:
    return {"message": f"hello, {name}"}


def _build_ord_document() -> ORDDocument:
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


# Mount the ORD discovery endpoints. Using the callable form so the document
# is rebuilt per request — useful when developing because reloads pick up
# changes without restarting the server.
app.include_router(ord_router(_build_ord_document))

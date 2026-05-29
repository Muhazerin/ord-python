"""FastAPI router exposing the ORD discovery endpoints.

Mounts two endpoints on a FastAPI application:

- ``/.well-known/open-resource-discovery`` — the Configuration manifest
  pointing at the actual ORD documents.
- ``/ord/v1/documents/ord-document`` — the ORD document itself.

The well-known path is the spec-defined entry point; discoverers (UCL,
UMS, ...) start there and follow ``documents[].url`` to fetch each
document.

Usage::

    from fastapi import FastAPI
    from ord.core.models import ORDDocument
    from ord.server import ord_router

    app = FastAPI()
    doc = ORDDocument(api_resources=[...])
    app.include_router(ord_router(doc))

The ``document_provider`` argument can be either a static
:py:class:`~ord.core.models.ORDDocument` (resolved once) or a callable
returning one (resolved per request) — useful when the document depends
on runtime state (e.g. selected tenant, environment).
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter

from ord.core.models import (
    AccessStrategy,
    ORDConfiguration,
    ORDDocument,
    V1DocumentDescription,
)

DocumentProvider = ORDDocument | Callable[[], ORDDocument]


def _resolve(provider: DocumentProvider) -> ORDDocument:
    """Materialize a document provider into an :py:class:`ORDDocument`.

    Trusts the up-front type check inside :py:func:`ord_router` — by the
    time we get here, ``provider`` is either an ORDDocument or a callable.
    """
    if isinstance(provider, ORDDocument):
        return provider
    return provider()


def ord_router(
    document_provider: DocumentProvider,
    *,
    well_known_path: str = "/.well-known/open-resource-discovery",
    document_path: str = "/ord/v1/documents/ord-document",
    base_url: str | None = None,
) -> APIRouter:
    """Return a FastAPI APIRouter mounting the ORD discovery endpoints.

    ``document_provider`` is either an :py:class:`ORDDocument` (resolved once
    at router construction) or a callable returning one (resolved on every
    GET, useful for runtime-dependent documents).

    ``well_known_path`` defaults to the spec-mandated
    ``/.well-known/open-resource-discovery``; override only if your
    deployment requires a different path.

    ``document_path`` is where the actual ORD document is served. The
    well-known manifest's ``documents[].url`` is set to this value so a
    discoverer following the manifest will hit the right endpoint.

    ``base_url`` is the optional ``baseUrl`` field on the manifest. When set,
    discoverers resolve the relative ``documents[].url`` against it; when
    omitted, the well-known endpoint's URL is used as the resolution origin.
    """
    # Validate the provider type up front so configuration errors surface at
    # router-construction time rather than at the first request.
    if not isinstance(document_provider, ORDDocument) and not callable(document_provider):
        raise TypeError(
            f"document_provider must be ORDDocument or Callable[[], ORDDocument]; "
            f"got {type(document_provider).__name__}"
        )

    router = APIRouter()

    @router.get(well_known_path)
    def _well_known() -> dict:
        manifest = ORDConfiguration(
            base_url=base_url,
            open_resource_discovery_v1={  # type: ignore[arg-type]
                "documents": [
                    V1DocumentDescription(
                        url=document_path,
                        access_strategies=[AccessStrategy(type="open")],
                    ),
                ],
            },
        )
        return manifest.to_ord_dict()

    @router.get(document_path)
    def _document() -> dict:
        return _resolve(document_provider).to_ord_dict()

    return router

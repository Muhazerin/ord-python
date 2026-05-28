"""FastAPI adapter — translate a ``FastAPI`` instance into an ORD APIResource.

Usage::

    from fastapi import FastAPI
    from ord.adapters.fastapi import apiresource_from_fastapi

    app = FastAPI()
    api = apiresource_from_fastapi(
        app,
        ord_id="sap.damn:apiResource:MyService:v1",
        title="My Service",
        short_description="Does the thing.",
        description="Does the thing in great detail.",
        part_of_package="sap.damn:package:Default:v1",
        version="1.0.0",
        visibility="public",
        release_status="active",
    )

The adapter intentionally requires every spec-mandated APIResource field as
a keyword argument rather than guessing from ``app.title`` / ``app.version``;
ORD's ``visibility``, ``releaseStatus``, ``partOfPackage``, and ``ordId`` all
carry meaning FastAPI knows nothing about, and silently filling in the wrong
values would emit incorrect ORD documents.
"""

from __future__ import annotations

from fastapi import FastAPI

from ord.core.models import (
    AccessStrategy,
    APIResource,
    APIResourceOrdId,
    ReleaseStatus,
    ResourceDefinition,
    Visibility,
)


def apiresource_from_fastapi(
    app: FastAPI,
    *,
    ord_id: APIResourceOrdId,
    title: str,
    short_description: str,
    description: str,
    part_of_package: str,
    version: str,
    visibility: Visibility,
    release_status: ReleaseStatus,
    openapi_url: str | None = None,
) -> APIResource:
    """Return an ORD APIResource describing ``app``'s OpenAPI surface.

    The resulting resource emits ``apiProtocol="rest"`` and a single
    ``resourceDefinitions`` entry of type ``openapi-v3`` pointing at the
    OpenAPI URL the FastAPI app actually serves.

    The OpenAPI URL is resolved as ``openapi_url`` (if provided) else
    ``app.openapi_url``. If both are absent — i.e. the FastAPI app was
    constructed with ``openapi_url=None`` and the caller did not override —
    a :class:`ValueError` is raised because the adapter has nothing
    consumable to point ORD at.
    """
    resolved_url = openapi_url if openapi_url is not None else app.openapi_url
    if resolved_url is None:
        raise ValueError(
            "FastAPI app has openapi_url=None and no openapi_url override "
            "was provided; cannot emit an APIResource without a definition URL."
        )

    return APIResource(
        ord_id=ord_id,
        title=title,
        short_description=short_description,
        description=description,
        part_of_package=part_of_package,
        version=version,
        visibility=visibility,
        release_status=release_status,
        api_protocol="rest",
        resource_definitions=[
            ResourceDefinition(
                type="openapi-v3",
                media_type="application/json",
                url=resolved_url,
                access_strategies=[AccessStrategy(type="open")],
            ),
        ],
    )

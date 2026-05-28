"""Tests for the FastAPI adapter."""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from ord.adapters.fastapi import apiresource_from_fastapi
from ord.core.models import ORDDocument


def _required_kwargs(**overrides: object) -> dict[str, object]:
    """Spec-required APIResource fields as kwargs, overridable per test."""
    defaults: dict[str, object] = {
        "ord_id": "sap.damn:apiResource:MyService:v1",
        "title": "My Service",
        "short_description": "Does the thing.",
        "description": "Does the thing in great detail.",
        "part_of_package": "sap.damn:package:Default:v1",
        "version": "1.0.0",
        "visibility": "public",
        "release_status": "active",
    }
    defaults.update(overrides)
    return defaults


class TestAPIResourceFromFastAPI:
    def test_returns_rest_apiresource_with_passthrough_fields(self):
        app = FastAPI()
        api = apiresource_from_fastapi(app, **_required_kwargs())  # type: ignore[arg-type]
        assert api.api_protocol == "rest"
        assert api.ord_id == "sap.damn:apiResource:MyService:v1"
        assert api.title == "My Service"
        assert api.visibility == "public"
        assert api.release_status == "active"

    def test_resource_definitions_point_at_default_openapi_url(self):
        app = FastAPI()  # default openapi_url is /openapi.json
        api = apiresource_from_fastapi(app, **_required_kwargs())  # type: ignore[arg-type]
        assert api.resource_definitions is not None
        assert len(api.resource_definitions) == 1
        rd = api.resource_definitions[0]
        assert rd.type == "openapi-v3"
        assert rd.media_type == "application/json"
        assert rd.url == "/openapi.json"
        assert len(rd.access_strategies) == 1
        assert rd.access_strategies[0].type == "open"

    def test_uses_apps_custom_openapi_url(self):
        # FastAPI lets users move the schema endpoint; the adapter must
        # reflect what the app actually serves.
        app = FastAPI(openapi_url="/spec/openapi.json")
        api = apiresource_from_fastapi(app, **_required_kwargs())  # type: ignore[arg-type]
        assert api.resource_definitions is not None
        assert api.resource_definitions[0].url == "/spec/openapi.json"

    def test_explicit_openapi_url_overrides_app_attr(self):
        # An explicit override wins even when the app exposes its own URL —
        # useful when ORD should advertise a stable public URL different from
        # the in-app mount point (e.g. behind a reverse proxy).
        app = FastAPI(openapi_url="/internal/openapi.json")
        api = apiresource_from_fastapi(
            app,
            openapi_url="https://api.example.com/v1/openapi.json",
            **_required_kwargs(),  # type: ignore[arg-type]
        )
        assert api.resource_definitions is not None
        assert (
            api.resource_definitions[0].url
            == "https://api.example.com/v1/openapi.json"
        )

    def test_raises_when_openapi_disabled_and_no_override(self):
        # FastAPI(openapi_url=None) means the user explicitly disabled the
        # OpenAPI schema endpoint. Emitting a /openapi.json URL would lie;
        # emitting empty resourceDefinitions would be useless. Refuse loudly.
        app = FastAPI(openapi_url=None)
        with pytest.raises(ValueError, match="openapi_url"):
            apiresource_from_fastapi(app, **_required_kwargs())  # type: ignore[arg-type]

    def test_disabled_openapi_works_when_explicit_url_provided(self):
        # Caller can still emit a sensible APIResource for an OpenAPI-disabled
        # FastAPI app by pointing ORD at an externally hosted definition.
        app = FastAPI(openapi_url=None)
        api = apiresource_from_fastapi(
            app,
            openapi_url="https://api.example.com/v1/openapi.json",
            **_required_kwargs(),  # type: ignore[arg-type]
        )
        assert api.resource_definitions is not None
        assert (
            api.resource_definitions[0].url
            == "https://api.example.com/v1/openapi.json"
        )

    def test_emitted_document_validates_against_spec(self):
        # End-to-end: wrap the adapter output in an ORDDocument and pipe
        # through the official JSON Schema. Catches reconciliation regressions
        # if the schema ever stops accepting what the adapter emits.
        app = FastAPI()
        api = apiresource_from_fastapi(app, **_required_kwargs())  # type: ignore[arg-type]
        doc = ORDDocument(api_resources=[api])
        doc.validate_against_spec()  # raises ORDValidationError on failure

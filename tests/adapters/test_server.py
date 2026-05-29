"""Tests for the FastAPI ORD discovery server."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ord.core.models import (
    AccessStrategy,
    APIResource,
    ORDDocument,
    ResourceDefinition,
)
from ord.core.validation import (
    validate_ord_configuration,
    validate_ord_document,
)
from ord.server import ord_router


def _populated_doc() -> ORDDocument:
    return ORDDocument(
        api_resources=[
            APIResource(
                ord_id="sap.demo:apiResource:Greeter:v1",
                title="Greeter",
                short_description="Greets.",
                description="Says hello.",
                part_of_package="sap.demo:package:Default:v1",
                version="1.0.0",
                visibility="public",
                release_status="active",
                api_protocol="rest",
                resource_definitions=[
                    ResourceDefinition(
                        type="openapi-v3",
                        media_type="application/json",
                        url="/openapi.json",
                        access_strategies=[AccessStrategy(type="open")],
                    ),
                ],
            ),
        ],
    )


def _build_client(
    provider: ORDDocument | Callable[[], ORDDocument],
    **kwargs: object,
) -> TestClient:
    app = FastAPI()
    app.include_router(ord_router(provider, **kwargs))  # type: ignore[arg-type]
    return TestClient(app)


class TestDiscoveryEndpoints:
    def test_well_known_returns_configuration_manifest(self):
        client = _build_client(_populated_doc())
        resp = client.get("/.well-known/open-resource-discovery")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        body = resp.json()
        # Manifest must point at the document endpoint, not contain the
        # document itself.
        urls = [
            d["url"] for d in body["openResourceDiscoveryV1"]["documents"]
        ]
        assert "/ord/v1/documents/ord-document" in urls

    def test_well_known_response_validates_against_configuration_schema(self):
        client = _build_client(_populated_doc())
        body = client.get("/.well-known/open-resource-discovery").json()
        validate_ord_configuration(body)  # raises on failure

    def test_document_endpoint_returns_ord_document(self):
        client = _build_client(_populated_doc())
        resp = client.get("/ord/v1/documents/ord-document")
        assert resp.status_code == 200
        body = resp.json()
        assert body["openResourceDiscovery"] == "1.15"
        assert body["apiResources"][0]["ordId"] == (
            "sap.demo:apiResource:Greeter:v1"
        )

    def test_document_response_validates_against_document_schema(self):
        client = _build_client(_populated_doc())
        body = client.get("/ord/v1/documents/ord-document").json()
        validate_ord_document(body)  # raises on failure

    def test_static_provider_is_resolved_once(self):
        # When the caller passes an ORDDocument instance directly, the
        # router shouldn't re-evaluate anything per request — the same
        # document body comes back on every call.
        doc = _populated_doc()
        client = _build_client(doc)
        first = client.get("/ord/v1/documents/ord-document").json()
        second = client.get("/ord/v1/documents/ord-document").json()
        assert first == second

    def test_callable_provider_is_called_per_request(self):
        # Useful for documents that depend on runtime state. The router
        # must invoke the callable on every GET.
        calls = {"count": 0}

        def provider() -> ORDDocument:
            calls["count"] += 1
            return _populated_doc()

        client = _build_client(provider)
        client.get("/ord/v1/documents/ord-document")
        client.get("/ord/v1/documents/ord-document")
        assert calls["count"] == 2

    def test_custom_paths_thread_through(self):
        client = _build_client(
            _populated_doc(),
            well_known_path="/.well-known/ord",
            document_path="/ord/document.json",
        )
        assert client.get("/.well-known/ord").status_code == 200
        assert client.get("/ord/document.json").status_code == 200
        # Manifest must point at the *custom* document path, not the default.
        body = client.get("/.well-known/ord").json()
        urls = [d["url"] for d in body["openResourceDiscoveryV1"]["documents"]]
        assert "/ord/document.json" in urls

    def test_base_url_appears_in_manifest_when_set(self):
        client = _build_client(_populated_doc(), base_url="https://api.example.com")
        body = client.get("/.well-known/open-resource-discovery").json()
        assert body["baseUrl"] == "https://api.example.com"

    def test_base_url_is_omitted_when_not_set(self):
        client = _build_client(_populated_doc())
        body = client.get("/.well-known/open-resource-discovery").json()
        assert "baseUrl" not in body


class TestProviderTypeChecking:
    def test_passing_a_string_raises(self):
        # Catches a common mistake — passing a JSON string or a dict
        # instead of an ORDDocument or callable returning one.
        with pytest.raises(TypeError):
            ord_router("not a document")  # type: ignore[arg-type]

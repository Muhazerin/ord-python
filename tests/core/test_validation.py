"""Tests for ord.core.validation — JSON Schema validation against the spec."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ord.core.models import (
    AccessStrategy,
    APIResource,
    ORDConfiguration,
    ORDDocument,
    ResourceDefinition,
    V1DocumentDescription,
)
from ord.core.validation import (
    ORDValidationError,
    load_spec_schema,
    validate_ord_configuration,
    validate_ord_document,
)


def _well_formed_doc() -> ORDDocument:
    return ORDDocument(
        api_resources=[
            APIResource(
                ord_id="sap.damn:apiResource:MyService:v1",
                title="My Service",
                short_description="Does the thing.",
                description="Does the thing in great detail.",
                part_of_package="sap.damn:package:Default:v1",
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


class TestSchemaBundle:
    def test_schema_is_loadable(self):
        schema = load_spec_schema()
        assert isinstance(schema, dict)
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
        assert "openResourceDiscovery" in schema.get("properties", {})

    def test_configuration_schema_is_loadable(self):
        schema = load_spec_schema("Configuration")
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
        assert "openResourceDiscoveryV1" in schema.get("properties", {})

    def test_schema_is_cached(self):
        # load_spec_schema is hot-path-friendly; calling it repeatedly should
        # return the same object, not re-read disk every time.
        assert load_spec_schema() is load_spec_schema()
        assert load_spec_schema("Configuration") is load_spec_schema("Configuration")

    def test_schema_files_are_bundled(self):
        # The vendored copies must travel with the package; otherwise wheels
        # built and installed elsewhere would crash on first validate call.
        import ord  # noqa: PLC0415

        spec_dir = Path(ord.__file__).parent / "_spec"
        for name in ("Document.schema.json", "Configuration.schema.json"):
            path = spec_dir / name
            assert path.is_file(), f"{name} not bundled"
            data = json.loads(path.read_text())
            assert data["$schema"] == "http://json-schema.org/draft-07/schema#"


class TestValidateOrdDocument:
    def test_minimal_empty_document_validates(self):
        # Just a version string — the smallest spec-legal document.
        validate_ord_document({"openResourceDiscovery": "1.15"})

    def test_well_formed_populated_document_validates(self):
        validate_ord_document(_well_formed_doc().to_ord_dict())

    def test_missing_open_resource_discovery_raises(self):
        with pytest.raises(ORDValidationError) as excinfo:
            validate_ord_document({})
        assert "openResourceDiscovery" in str(excinfo.value)

    def test_unknown_top_level_field_raises(self):
        # Schema sets additionalProperties=false at the document root.
        with pytest.raises(ORDValidationError) as excinfo:
            validate_ord_document(
                {"openResourceDiscovery": "1.15", "totallyUnknown": True}
            )
        assert "totallyUnknown" in str(excinfo.value)

    def test_collects_multiple_errors(self):
        # The error message should list every violation, not just the first.
        # Two violations: missing apiProtocol and missing mediaType.
        bad = {
            "openResourceDiscovery": "1.15",
            "apiResources": [
                {
                    "ordId": "sap.damn:apiResource:Bad:v1",
                    "title": "Bad",
                    "shortDescription": "Bad.",
                    "description": "Bad.",
                    "partOfPackage": "sap.damn:package:Default:v1",
                    "version": "1.0.0",
                    "visibility": "public",
                    "releaseStatus": "active",
                    # apiProtocol missing
                    "resourceDefinitions": [
                        {
                            "type": "openapi-v3",
                            "url": "/openapi.json",
                            # mediaType missing
                            "accessStrategies": [{"type": "open"}],
                        }
                    ],
                }
            ],
        }
        with pytest.raises(ORDValidationError) as excinfo:
            validate_ord_document(bad)
        msg = str(excinfo.value)
        assert "apiProtocol" in msg
        assert "mediaType" in msg

    def test_error_lists_paths_for_navigation(self):
        # Each error entry should carry a JSON-pointer-ish path so the caller
        # can locate the offending field in a populated document.
        with pytest.raises(ORDValidationError) as excinfo:
            validate_ord_document(
                {
                    "openResourceDiscovery": "1.15",
                    "apiResources": [{"ordId": "not-a-valid-id"}],
                }
            )
        err = excinfo.value
        assert err.errors  # list of dicts
        # At least one error path should reference the apiResources[0] subtree.
        assert any(
            "apiResources" in (e.get("path") or "") for e in err.errors
        )


class TestModelLevelValidate:
    def test_well_formed_document_validates(self):
        # ORDDocument.validate_against_spec() is a convenience wrapper that
        # calls validate_ord_document(self.to_ord_dict()).
        _well_formed_doc().validate_against_spec()

    def test_empty_document_validates(self):
        ORDDocument().validate_against_spec()

    def test_returns_none_on_success(self):
        # The call returns None; consumers detect failure by exception, not
        # by sentinel return value (consistent with Pydantic conventions).
        assert _well_formed_doc().validate_against_spec() is None


class TestValidateOrdConfiguration:
    def _well_formed(self) -> ORDConfiguration:
        return ORDConfiguration(
            open_resource_discovery_v1={
                "documents": [
                    V1DocumentDescription(
                        url="/ord/v1/documents/ord-document",
                        access_strategies=[AccessStrategy(type="open")],
                    )
                ],
            },
        )

    def test_well_formed_manifest_validates(self):
        validate_ord_configuration(self._well_formed().to_ord_dict())

    def test_missing_open_resource_discovery_v1_raises(self):
        with pytest.raises(ORDValidationError) as excinfo:
            validate_ord_configuration({})
        assert "openResourceDiscoveryV1" in str(excinfo.value)

    def test_validate_against_spec_method_on_configuration(self):
        self._well_formed().validate_against_spec()

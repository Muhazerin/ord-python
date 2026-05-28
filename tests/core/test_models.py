"""Tests for ord.core.models — Pydantic models mirroring the ORD spec.

References:
    https://open-resource-discovery.org/spec-v1/interfaces/Document
"""

import pytest
from pydantic import ValidationError

from ord.core.models import AccessStrategy, APIResource, ORDDocument, ResourceDefinition


class TestAccessStrategy:
    def test_open_strategy_is_valid(self):
        strategy = AccessStrategy(type="open")
        assert strategy.type == "open"

    def test_custom_strategy_is_valid(self):
        # Real-world example from cap-js/ord's custom.ord.json fixture.
        strategy = AccessStrategy(type="sap.businesshub:basic-auth:v1")
        assert strategy.type == "sap.businesshub:basic-auth:v1"

    def test_type_is_required(self):
        with pytest.raises(ValidationError):
            AccessStrategy()  # type: ignore[call-arg]

    def test_serializes_to_camelcase_json(self):
        strategy = AccessStrategy(type="open")
        assert strategy.to_ord_dict() == {"type": "open"}

    def test_custom_type_field_is_accepted(self):
        # Per spec: customType is an optional companion field used when type
        # signals a custom strategy. Stored as plain string here; JSON-Schema
        # validation in step 3 will enforce the Specification ID format.
        strategy = AccessStrategy(
            type="custom",
            custom_type="sap.damn:auth:my-strategy:v1",
        )
        assert strategy.custom_type == "sap.damn:auth:my-strategy:v1"
        assert strategy.to_ord_dict() == {
            "type": "custom",
            "customType": "sap.damn:auth:my-strategy:v1",
        }

    def test_to_ord_json_returns_spec_shaped_json(self):
        strategy = AccessStrategy(type="custom", custom_type="x:y:z:v1")
        # Round-trip via the JSON helper to confirm aliases and null-stripping
        # both apply.
        import json

        assert json.loads(strategy.to_ord_json()) == {
            "type": "custom",
            "customType": "x:y:z:v1",
        }

    def test_unknown_field_is_rejected(self):
        # extra="forbid" means typos at construction don't silently slip
        # through into emitted ORD documents.
        with pytest.raises(ValidationError):
            AccessStrategy(type="open", unknownField="x")  # type: ignore[call-arg]


class TestResourceDefinition:
    def _open_strategy(self) -> AccessStrategy:
        return AccessStrategy(type="open")

    def test_minimal_openapi_v3_definition(self):
        rd = ResourceDefinition(
            type="openapi-v3",
            url="/openapi.json",
            access_strategies=[self._open_strategy()],
        )
        assert rd.type == "openapi-v3"
        assert rd.url == "/openapi.json"
        assert rd.access_strategies[0].type == "open"

    def test_required_fields(self):
        # type, url, accessStrategies are required by spec.
        with pytest.raises(ValidationError):
            ResourceDefinition()  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            ResourceDefinition(  # type: ignore[call-arg]
                type="openapi-v3",
                url="/openapi.json",
            )
        with pytest.raises(ValidationError):
            ResourceDefinition(  # type: ignore[call-arg]
                type="openapi-v3",
                access_strategies=[self._open_strategy()],
            )

    def test_access_strategies_must_be_non_empty(self):
        # Per spec, ResourceDefinitions must have at least one access strategy
        # — an empty list would mean "no documented way to reach this".
        with pytest.raises(ValidationError):
            ResourceDefinition(
                type="openapi-v3",
                url="/openapi.json",
                access_strategies=[],
            )

    def test_serializes_camelcase_with_nested_strategies(self):
        rd = ResourceDefinition(
            type="openapi-v3",
            media_type="application/json",
            url="/openapi.json",
            access_strategies=[self._open_strategy()],
        )
        assert rd.to_ord_dict() == {
            "type": "openapi-v3",
            "mediaType": "application/json",
            "url": "/openapi.json",
            "accessStrategies": [{"type": "open"}],
        }

    def test_custom_type_definition(self):
        # type="custom" is allowed; customType is the optional companion.
        rd = ResourceDefinition(
            type="custom",
            custom_type="sap.damn:spec:agent-document-card:v1",
            url="/schemas/card.json",
            access_strategies=[self._open_strategy()],
        )
        out = rd.to_ord_dict()
        assert out["type"] == "custom"
        assert out["customType"] == "sap.damn:spec:agent-document-card:v1"


class TestAPIResource:
    """APIResource has 9 spec-required fields. partOfPackage references a
    Package by ordId string (we don't model Package yet)."""

    def _minimal_kwargs(self, **overrides: object) -> dict[str, object]:
        defaults: dict[str, object] = {
            "ord_id": "sap.damn:apiResource:MyService:v1",
            "title": "My Service",
            "short_description": "Does the thing.",
            "description": "Does the thing in great detail.",
            "part_of_package": "sap.damn:package:Default:v1",
            "version": "1.0.0",
            "visibility": "public",
            "release_status": "active",
            "api_protocol": "rest",
        }
        defaults.update(overrides)
        return defaults

    def test_minimal_rest_resource(self):
        api = APIResource(**self._minimal_kwargs())  # type: ignore[arg-type]
        assert api.ord_id == "sap.damn:apiResource:MyService:v1"
        assert api.api_protocol == "rest"
        assert api.resource_definitions is None  # optional

    def test_required_fields_are_enforced(self):
        with pytest.raises(ValidationError):
            APIResource()  # type: ignore[call-arg]

    @pytest.mark.parametrize(
        "bad_ord_id",
        [
            "no-colons",
            "sap.damn:apiResource:Name",  # missing version
            "sap.damn:apiResource:Name:1",  # version missing v prefix
            "sap.damn:apiResource:Name:v01",  # leading-zero version
            "SAP.DAMN:apiResource:Name:v1",  # uppercase namespace
            "sap.damn:eventResource:Name:v1",  # wrong type segment for APIResource
            "",
        ],
    )
    def test_ord_id_regex_rejects_malformed(self, bad_ord_id: str):
        with pytest.raises(ValidationError):
            APIResource(**self._minimal_kwargs(ord_id=bad_ord_id))  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "good_ord_id",
        [
            "sap.damn:apiResource:MyService:v1",
            "sap.damn:apiResource:MyService:v0",
            "sap.damn:apiResource:My_Service-2.0:v42",
            "a:apiResource:x:v1",
        ],
    )
    def test_ord_id_regex_accepts_well_formed(self, good_ord_id: str):
        api = APIResource(**self._minimal_kwargs(ord_id=good_ord_id))  # type: ignore[arg-type]
        assert api.ord_id == good_ord_id

    def test_visibility_enum(self):
        for v in ("public", "internal", "private"):
            APIResource(**self._minimal_kwargs(visibility=v))  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            APIResource(**self._minimal_kwargs(visibility="secret"))  # type: ignore[arg-type]

    def test_release_status_enum(self):
        for s in ("development", "beta", "active", "deprecated", "sunset"):
            APIResource(**self._minimal_kwargs(release_status=s))  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            APIResource(**self._minimal_kwargs(release_status="ga"))  # type: ignore[arg-type]

    def test_serializes_camelcase_with_nested_resource_definitions(self):
        rd = ResourceDefinition(
            type="openapi-v3",
            url="/openapi.json",
            access_strategies=[AccessStrategy(type="open")],
        )
        api = APIResource(**self._minimal_kwargs(resource_definitions=[rd]))  # type: ignore[arg-type]
        out = api.to_ord_dict()
        assert out["ordId"] == "sap.damn:apiResource:MyService:v1"
        assert out["partOfPackage"] == "sap.damn:package:Default:v1"
        assert out["releaseStatus"] == "active"
        assert out["apiProtocol"] == "rest"
        assert out["resourceDefinitions"] == [
            {
                "type": "openapi-v3",
                "url": "/openapi.json",
                "accessStrategies": [{"type": "open"}],
            }
        ]
        # Optional fields with default None must be stripped from the wire form.
        assert "shortDescription" in out  # required, present
        assert "tags" not in out  # not modeled / not provided


class TestORDDocument:
    def _api_resource(self) -> APIResource:
        return APIResource(
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
                    url="/openapi.json",
                    access_strategies=[AccessStrategy(type="open")],
                )
            ],
        )

    def test_minimal_document_with_one_api_resource(self):
        doc = ORDDocument(api_resources=[self._api_resource()])
        assert doc.open_resource_discovery == "1.15"  # current default
        assert len(doc.api_resources) == 1

    def test_open_resource_discovery_version_is_required(self):
        # Default makes it optional in Python, but explicit None must fail —
        # the wire payload always carries a version.
        with pytest.raises(ValidationError):
            ORDDocument(open_resource_discovery=None)  # type: ignore[arg-type]

    @pytest.mark.parametrize("version", ["1.0", "1.5", "1.15"])
    def test_accepts_supported_spec_versions(self, version: str):
        doc = ORDDocument(open_resource_discovery=version)
        assert doc.open_resource_discovery == version

    @pytest.mark.parametrize("version", ["0.9", "2.0", "1.16", "v1", ""])
    def test_rejects_unsupported_spec_versions(self, version: str):
        with pytest.raises(ValidationError):
            ORDDocument(open_resource_discovery=version)

    def test_serializes_full_nested_structure(self):
        doc = ORDDocument(api_resources=[self._api_resource()])
        out = doc.to_ord_dict()
        assert out["openResourceDiscovery"] == "1.15"
        assert len(out["apiResources"]) == 1
        api = out["apiResources"][0]
        assert api["ordId"] == "sap.damn:apiResource:MyService:v1"
        assert api["resourceDefinitions"][0]["accessStrategies"] == [{"type": "open"}]
        # Optional empty arrays should not appear on the wire.
        assert "eventResources" not in out

    def test_empty_document_serializes_with_only_version(self):
        # The minimum useful ORD document has no resources at all — it just
        # announces its spec version. Useful as the default/empty case for
        # the discovery endpoint when no adapter has populated anything yet.
        doc = ORDDocument()
        assert doc.to_ord_dict() == {"openResourceDiscovery": "1.15"}

"""Pydantic models for the ORD spec.

These mirror https://open-resource-discovery.org/spec-v1/interfaces/Document.
Python attribute names use snake_case; JSON serialization uses the spec's
camelCase via Pydantic field aliases. Use :py:meth:`_ORDModel.to_ord_dict`
or :py:meth:`_ORDModel.to_ord_json` to produce spec-shaped output; they
default to ``by_alias=True`` and ``exclude_none=True`` so optional missing
fields disappear from the wire representation.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel


class _ORDModel(BaseModel):
    """Base for every ORD model. Enforces the snake/camel alias contract."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    def to_ord_dict(self) -> dict[str, Any]:
        """Return the model as a spec-shaped (camelCase, no nulls) dict."""
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_ord_json(self, *, indent: int | None = None) -> str:
        """Return the model as a spec-shaped JSON string."""
        return self.model_dump_json(by_alias=True, exclude_none=True, indent=indent)


class AccessStrategy(_ORDModel):
    """How a resource definition can be accessed.

    Spec reference: ``accessStrategies`` array items on ResourceDefinition.
    """

    type: str
    custom_type: str | None = None


class ResourceDefinition(_ORDModel):
    """A concrete machine-readable definition (OpenAPI, AsyncAPI, EDMX, ...).

    Spec reference: ``resourceDefinitions`` array items on APIResource and
    EventResource. ``accessStrategies`` must contain at least one entry — a
    definition with no documented way to reach it is meaningless.
    """

    type: str
    custom_type: str | None = None
    media_type: str | None = None
    url: str
    access_strategies: Annotated[list[AccessStrategy], Field(min_length=1)]


# Spec regex for an APIResource ordId. Pinned verbatim from
# https://open-resource-discovery.org/spec-v1/interfaces/Document so a fresh
# reader can diff against the spec without a translation step.
_API_RESOURCE_ORD_ID_RE = (
    r"^([a-z0-9]+(?:[.][a-z0-9]+)*):(apiResource):([a-zA-Z0-9._\-]+):(v0|v[1-9][0-9]*)$"
)

APIResourceOrdId = Annotated[
    str,
    StringConstraints(pattern=_API_RESOURCE_ORD_ID_RE, max_length=255),
]

Visibility = Literal["public", "internal", "private"]
ReleaseStatus = Literal["development", "beta", "active", "deprecated", "sunset"]


class APIResource(_ORDModel):
    """An ORD API Resource — one consumable interface (REST, MCP, A2A, ...).

    Spec reference: ``apiResources`` array items on the ORD Document. The
    9 required fields (``ordId``, ``title``, ``shortDescription``,
    ``description``, ``partOfPackage``, ``version``, ``visibility``,
    ``releaseStatus``, ``apiProtocol``) match the spec; ``apiProtocol`` is
    a free-form string because the spec marks it extensible.
    """

    ord_id: APIResourceOrdId
    title: str
    short_description: str
    description: str
    part_of_package: str  # ordId reference; Package model deferred.
    version: str  # SemVer; not validated yet — JSON-Schema step will enforce.
    visibility: Visibility
    release_status: ReleaseStatus
    api_protocol: str
    resource_definitions: list[ResourceDefinition] | None = None


# Spec-supported ORD document versions. Keep in sync with
# https://open-resource-discovery.org/spec-v1/interfaces/Document — the
# spec lists 1.0 through 1.15 as of writing.
ORDSpecVersion = Literal[
    "1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7",
    "1.8", "1.9", "1.10", "1.11", "1.12", "1.13", "1.14", "1.15",
]


class ORDDocument(_ORDModel):
    """The top-level ORD document served at the discovery endpoints.

    Spec reference: https://open-resource-discovery.org/spec-v1/interfaces/Document.
    Only the resource arrays needed for the FastAPI/FastMCP MVP are modeled
    today (apiResources). EventResources, Packages, Products, etc. land as
    later milestones unlock them.
    """

    open_resource_discovery: ORDSpecVersion = "1.15"
    api_resources: list[APIResource] | None = None

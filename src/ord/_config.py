"""Load and validate the ``[tool.ord]`` block from a project's pyproject.toml.

The CLI consumes this config to know which FastAPI app to inspect and how
to populate the spec-required APIResource fields that can't be inferred
from the framework. Lives in a private module because the schema is a
contract between the CLI and pyproject.toml — consumers shouldn't import
it directly.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from ord.core.models import APIResourceOrdId, ReleaseStatus, Visibility


class ORDProjectConfigError(ValueError):
    """Raised when pyproject.toml's ``[tool.ord]`` block is missing or malformed.

    Distinct from Pydantic's :class:`ValidationError` so the CLI can format a
    helpful sample-config message for missing/unreadable files (where Pydantic
    has nothing to validate yet).
    """


_SAMPLE_CONFIG = """\
[tool.ord]
app = "your_package.main:app"

[tool.ord.api_resource]
ord_id = "your.namespace:apiResource:YourService:v1"
title = "Your Service"
short_description = "Short, single-line description."
description = "Longer description of what the service does."
part_of_package = "your.namespace:package:Default:v1"
version = "1.0.0"
visibility = "public"           # public | internal | private
release_status = "active"       # development | beta | active | deprecated | sunset
"""


class _APIResourceConfig(BaseModel):
    """The 8 spec-required APIResource fields the user supplies in config.

    ``apiProtocol`` is set by the FastAPI adapter (``"rest"``);
    ``resourceDefinitions`` is built by the adapter from ``app.openapi_url``.
    """

    model_config = ConfigDict(extra="forbid")

    ord_id: APIResourceOrdId
    title: str
    short_description: str
    description: str
    part_of_package: str
    version: str
    visibility: Visibility
    release_status: ReleaseStatus


class ORDProjectConfig(BaseModel):
    """Validated representation of the ``[tool.ord]`` block."""

    model_config = ConfigDict(extra="forbid")

    app: str
    api_resource: _APIResourceConfig


def load_project_config(pyproject_path: Path) -> ORDProjectConfig:
    """Read and validate ``[tool.ord]`` from ``pyproject_path``.

    Raises :class:`ORDProjectConfigError` if the file can't be read or the
    ``[tool.ord]`` table is missing entirely (the CLI prints a sample
    config in that case). Raises Pydantic's :class:`ValidationError` if a
    required field is missing or malformed within the table — that error
    already carries field-precise paths.
    """
    if not pyproject_path.is_file():
        raise ORDProjectConfigError(
            f"pyproject.toml not found at {pyproject_path}. "
            f"Run from the project root or pass --pyproject."
        )

    with pyproject_path.open("rb") as fp:
        data = tomllib.load(fp)

    tool_ord = data.get("tool", {}).get("ord")
    if tool_ord is None:
        raise ORDProjectConfigError(
            f"No [tool.ord] section in {pyproject_path}. Add a block like:\n\n"
            f"{_SAMPLE_CONFIG}"
        )

    return ORDProjectConfig.model_validate(tool_ord)

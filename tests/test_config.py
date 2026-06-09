"""Tests for ord._config — load and validate [tool.ord] from pyproject.toml."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from pydantic import ValidationError

from ord._config import (
    ORDProjectConfig,
    ORDProjectConfigError,
    load_project_config,
)

# A complete, well-formed [tool.ord] block reused across tests.
_VALID_TOML = textwrap.dedent(
    """
    [tool.ord]
    app = "examples.fastapi_app.main:app"

    [tool.ord.api_resource]
    ord_id = "sap.demo:apiResource:Greeter:v1"
    title = "Greeter"
    short_description = "Greets."
    description = "Says hello."
    part_of_package = "sap.demo:package:Default:v1"
    version = "1.0.0"
    visibility = "public"
    release_status = "active"
    """
)


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(body)
    return path


class TestLoadProjectConfig:
    def test_loads_well_formed_config(self, tmp_path: Path):
        cfg = load_project_config(_write(tmp_path, _VALID_TOML))
        assert isinstance(cfg, ORDProjectConfig)
        assert cfg.app == "examples.fastapi_app.main:app"
        assert cfg.api_resource.ord_id == "sap.demo:apiResource:Greeter:v1"
        assert cfg.api_resource.visibility == "public"

    def test_missing_pyproject_raises(self, tmp_path: Path):
        # File doesn't exist at all.
        with pytest.raises(ORDProjectConfigError, match="pyproject.toml"):
            load_project_config(tmp_path / "pyproject.toml")

    def test_missing_tool_ord_section_raises_with_sample(self, tmp_path: Path):
        path = _write(tmp_path, "[project]\nname = 'x'\nversion = '0.0.0'\n")
        with pytest.raises(ORDProjectConfigError) as excinfo:
            load_project_config(path)
        msg = str(excinfo.value)
        # Sample config in the error helps the user copy-paste a fix.
        assert "[tool.ord]" in msg
        assert "ord_id" in msg

    def test_missing_app_field_raises(self, tmp_path: Path):
        body = textwrap.dedent(
            """
            [tool.ord]
            [tool.ord.api_resource]
            ord_id = "sap.demo:apiResource:Greeter:v1"
            title = "x"
            short_description = "x"
            description = "x"
            part_of_package = "sap.demo:package:Default:v1"
            version = "1.0.0"
            visibility = "public"
            release_status = "active"
            """
        )
        with pytest.raises(ValidationError) as excinfo:
            load_project_config(_write(tmp_path, body))
        assert "app" in str(excinfo.value)

    def test_missing_api_resource_field_raises(self, tmp_path: Path):
        # Drop visibility from a known-good config to verify required-field
        # validation surfaces from the nested table.
        body = _VALID_TOML.replace('visibility = "public"\n', "")
        with pytest.raises(ValidationError) as excinfo:
            load_project_config(_write(tmp_path, body))
        assert "visibility" in str(excinfo.value)

    def test_unknown_field_in_api_resource_raises(self, tmp_path: Path):
        # extra="forbid" so typos fail fast rather than silently emit
        # a malformed APIResource later in the build.
        body = _VALID_TOML + 'unknown = "x"\n'
        with pytest.raises(ValidationError) as excinfo:
            load_project_config(_write(tmp_path, body))
        assert "unknown" in str(excinfo.value)

    def test_invalid_visibility_raises(self, tmp_path: Path):
        # Visibility is constrained to the spec enum; surfaces here, not
        # later when the APIResource is built.
        body = _VALID_TOML.replace(
            'visibility = "public"', 'visibility = "secret"'
        )
        with pytest.raises(ValidationError) as excinfo:
            load_project_config(_write(tmp_path, body))
        assert "visibility" in str(excinfo.value)

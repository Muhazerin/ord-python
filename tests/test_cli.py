"""Tests for the ``ord build`` CLI."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from ord.cli import main
from ord.core.validation import validate_ord_configuration, validate_ord_document

# A complete [tool.ord] block; tests parameterize the `app = ...` field.
_PYPROJECT_TEMPLATE = textwrap.dedent(
    """
    [project]
    name = "demo"
    version = "0.0.0"

    [tool.ord]
    app = "{app}"

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


@pytest.fixture
def fake_app_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Drop a tiny FastAPI module on sys.path and return its `module:attr`."""
    pkg_dir = tmp_path / "demo_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI(title='Greeter', version='1.0.0')\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    return "demo_pkg.main:app"


@pytest.fixture
def project_dir(tmp_path: Path, fake_app_module: str) -> Path:
    """tmp_path with a populated pyproject.toml ready for `ord build`."""
    (tmp_path / "pyproject.toml").write_text(
        _PYPROJECT_TEMPLATE.format(app=fake_app_module)
    )
    return tmp_path


class TestOrdBuild:
    def test_writes_both_artifacts_into_default_out_dir(self, project_dir: Path):
        # No --out flag: gen/ord/ is created relative to the project root.
        rc = main(["build", "--pyproject", str(project_dir / "pyproject.toml")])
        assert rc == 0

        gen_dir = project_dir / "gen" / "ord"
        assert (gen_dir / "ord-document.json").is_file()
        assert (gen_dir / "well-known.json").is_file()

    def test_emits_a_spec_valid_ord_document(self, project_dir: Path):
        main(["build", "--pyproject", str(project_dir / "pyproject.toml")])
        doc = json.loads((project_dir / "gen/ord/ord-document.json").read_text())
        validate_ord_document(doc)
        # Adapter populated apiProtocol and the OpenAPI definition.
        api = doc["apiResources"][0]
        assert api["apiProtocol"] == "rest"
        assert api["resourceDefinitions"][0]["url"] == "/openapi.json"

    def test_emits_a_spec_valid_well_known_manifest(self, project_dir: Path):
        main(["build", "--pyproject", str(project_dir / "pyproject.toml")])
        manifest = json.loads(
            (project_dir / "gen/ord/well-known.json").read_text()
        )
        validate_ord_configuration(manifest)
        # Manifest points at the document file, not at the runtime endpoint.
        urls = [d["url"] for d in manifest["openResourceDiscoveryV1"]["documents"]]
        assert "ord-document.json" in urls

    def test_custom_out_dir(self, project_dir: Path, tmp_path: Path):
        out = tmp_path / "build" / "ord-out"
        rc = main(
            [
                "build",
                "--pyproject",
                str(project_dir / "pyproject.toml"),
                "--out",
                str(out),
            ]
        )
        assert rc == 0
        assert (out / "ord-document.json").is_file()
        assert (out / "well-known.json").is_file()

    def test_missing_pyproject_exits_nonzero(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ):
        rc = main(["build", "--pyproject", str(tmp_path / "nope.toml")])
        assert rc != 0
        err = capsys.readouterr().err
        assert "pyproject.toml" in err

    def test_missing_tool_ord_section_prints_sample(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ):
        path = tmp_path / "pyproject.toml"
        path.write_text("[project]\nname='x'\nversion='0.0.0'\n")
        rc = main(["build", "--pyproject", str(path)])
        assert rc != 0
        err = capsys.readouterr().err
        assert "[tool.ord]" in err  # sample config in the error
        assert "ord_id" in err

    def test_invalid_module_path_exits_nonzero(
        self,
        project_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ):
        # Replace the working app pointer with one that doesn't resolve.
        body = (project_dir / "pyproject.toml").read_text().replace(
            'app = "demo_pkg.main:app"', 'app = "nonexistent.module:app"'
        )
        (project_dir / "pyproject.toml").write_text(body)

        rc = main(["build", "--pyproject", str(project_dir / "pyproject.toml")])
        assert rc != 0
        err = capsys.readouterr().err
        assert "nonexistent" in err or "module" in err.lower()

    def test_app_must_be_a_fastapi_instance(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ):
        # Point the config at a non-FastAPI object (a plain dict). The CLI
        # should refuse loudly rather than crash deep in the adapter.
        pkg = tmp_path / "bad_pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "main.py").write_text("app = {'not': 'a fastapi'}\n")
        monkeypatch.syspath_prepend(str(tmp_path))

        (tmp_path / "pyproject.toml").write_text(
            _PYPROJECT_TEMPLATE.format(app="bad_pkg.main:app")
        )

        rc = main(["build", "--pyproject", str(tmp_path / "pyproject.toml")])
        assert rc != 0
        err = capsys.readouterr().err
        assert "FastAPI" in err

    def test_app_without_colon_exits_nonzero(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ):
        # `app = "demo_pkg.main"` (no colon) — common typo.
        # Hits the early ValueError in _resolve_app and is reformatted
        # by main()'s (ImportError, TypeError, ValueError) arm.
        (tmp_path / "pyproject.toml").write_text(
            _PYPROJECT_TEMPLATE.format(app="demo_pkg.main")
        )
        rc = main(["build", "--pyproject", str(tmp_path / "pyproject.toml")])
        assert rc != 0
        err = capsys.readouterr().err
        assert "module:attr" in err

    def test_app_with_missing_attribute_exits_nonzero(
        self,
        project_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ):
        # Module imports fine but the named attribute doesn't exist.
        # Hits the AttributeError → ImportError re-raise in _resolve_app.
        body = (project_dir / "pyproject.toml").read_text().replace(
            'app = "demo_pkg.main:app"', 'app = "demo_pkg.main:nonexistent"'
        )
        (project_dir / "pyproject.toml").write_text(body)

        rc = main(["build", "--pyproject", str(project_dir / "pyproject.toml")])
        assert rc != 0
        err = capsys.readouterr().err
        assert "nonexistent" in err

    def test_invalid_field_in_tool_ord_surfaces_as_validation_error(
        self,
        project_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ):
        # visibility="secret" isn't in the spec enum. Pydantic raises a
        # ValidationError during config load; main()'s ValidationError
        # arm formats it with the "invalid [tool.ord] config" prefix.
        body = (project_dir / "pyproject.toml").read_text().replace(
            'visibility = "public"', 'visibility = "secret"'
        )
        (project_dir / "pyproject.toml").write_text(body)

        rc = main(["build", "--pyproject", str(project_dir / "pyproject.toml")])
        assert rc != 0
        err = capsys.readouterr().err
        assert "[tool.ord]" in err  # the prefix from the ValidationError arm
        assert "visibility" in err  # Pydantic's field path

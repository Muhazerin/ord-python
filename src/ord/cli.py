"""``ord`` command-line interface.

Today exposes one subcommand, ``build``, which reads a project's
``pyproject.toml``, introspects the FastAPI app pointed at by
``[tool.ord].app``, and writes a spec-validated ORD document plus a
Configuration manifest into ``gen/ord/`` (override with ``--out``).

Usage::

    ord build [--pyproject PATH] [--out DIR]

Wired up via ``[project.scripts]`` in ``pyproject.toml`` so a
``pip install`` puts ``ord`` on PATH.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import ValidationError

from ord._config import ORDProjectConfig, ORDProjectConfigError, load_project_config
from ord.adapters.fastapi import apiresource_from_fastapi
from ord.core.models import (
    AccessStrategy,
    ORDConfiguration,
    ORDDocument,
    V1DocumentDescription,
)


def _resolve_app(spec: str) -> FastAPI:
    """Import ``module:attr`` and return the resolved attribute as a FastAPI app.

    Raises a CLI-friendly :class:`ValueError` (or :class:`ImportError`) so
    :py:func:`main` can format and print the message itself rather than
    letting a stack trace leak.
    """
    if ":" not in spec:
        raise ValueError(
            f"app must be 'module:attr' (e.g. 'mypkg.main:app'); got {spec!r}"
        )
    module_path, attr = spec.split(":", 1)
    module = importlib.import_module(module_path)
    try:
        app = getattr(module, attr)
    except AttributeError as exc:
        raise ImportError(
            f"module {module_path!r} has no attribute {attr!r}"
        ) from exc
    if not isinstance(app, FastAPI):
        raise TypeError(
            f"{spec!r} did not resolve to a FastAPI instance "
            f"(got {type(app).__name__})"
        )
    return app


def _build_artifacts(cfg: ORDProjectConfig) -> tuple[ORDDocument, ORDConfiguration]:
    """Construct the ORD document and the well-known Configuration manifest.

    The manifest's ``documents[].url`` is set to the *filename* of the
    document we'll write next to it, so a user serving ``gen/ord/`` as
    static content gets a discoverer-walkable layout out of the box.
    """
    app = _resolve_app(cfg.app)
    api = apiresource_from_fastapi(
        app,
        ord_id=cfg.api_resource.ord_id,
        title=cfg.api_resource.title,
        short_description=cfg.api_resource.short_description,
        description=cfg.api_resource.description,
        part_of_package=cfg.api_resource.part_of_package,
        version=cfg.api_resource.version,
        visibility=cfg.api_resource.visibility,
        release_status=cfg.api_resource.release_status,
    )
    doc = ORDDocument(api_resources=[api])
    manifest = ORDConfiguration(
        open_resource_discovery_v1={  # type: ignore[arg-type]
            "documents": [
                V1DocumentDescription(
                    url="ord-document.json",
                    access_strategies=[AccessStrategy(type="open")],
                ),
            ],
        },
    )
    return doc, manifest


def _write_artifacts(out_dir: Path, doc: ORDDocument, manifest: ORDConfiguration) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ord-document.json").write_text(
        json.dumps(doc.to_ord_dict(), indent=2) + "\n"
    )
    (out_dir / "well-known.json").write_text(
        json.dumps(manifest.to_ord_dict(), indent=2) + "\n"
    )


def _cmd_build(args: argparse.Namespace) -> int:
    pyproject = Path(args.pyproject).resolve()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        # Anchor relative --out paths to the pyproject's directory so the
        # CLI behaves predictably regardless of where the user runs it.
        out_dir = pyproject.parent / out_dir

    cfg = load_project_config(pyproject)
    doc, manifest = _build_artifacts(cfg)

    # Validate before writing — better to fail loudly than ship a bad doc.
    doc.validate_against_spec()
    manifest.validate_against_spec()

    _write_artifacts(out_dir, doc, manifest)
    print(f"Wrote {out_dir}/ord-document.json and {out_dir}/well-known.json")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ord",
        description="Open Resource Discovery tooling for Python services.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser(
        "build",
        help="Build the ORD document and Configuration manifest for the project.",
    )
    build.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to the project's pyproject.toml (default: ./pyproject.toml).",
    )
    build.add_argument(
        "--out",
        default="gen/ord",
        help=(
            "Output directory for ord-document.json and well-known.json "
            "(default: ./gen/ord, resolved relative to pyproject's dir)."
        ),
    )
    build.set_defaults(func=_cmd_build)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code; argv defaults to sys.argv[1:]."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ORDProjectConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(f"error: invalid [tool.ord] config:\n{exc}", file=sys.stderr)
        return 2
    except (ImportError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""Validate ORD documents and configuration manifests against the official ORD JSON Schemas.

Two schemas are vendored at ``src/ord/_spec/``:

- ``Document.schema.json`` for full ORD documents (api/event/entity resources, ...).
- ``Configuration.schema.json`` for the manifest served at
  ``/.well-known/open-resource-discovery``.

Both are refreshed manually via ``scripts/refresh_spec.py`` (see
``docs/vendored-schema.md``). Validation is opt-in: nothing runs at model
construction time, so building intermediate documents stays cheap. Call
:py:func:`validate_ord_document` / :py:func:`validate_ord_configuration` (or
:py:meth:`ORDDocument.validate_against_spec` / :py:meth:`ORDConfiguration.validate_against_spec`)
when you want a spec compliance check.
"""

from __future__ import annotations

import json
from functools import cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft7Validator


class ORDValidationError(ValueError):
    """Raised when an ORD document fails JSON Schema validation.

    ``errors`` is a list of small dicts (``message``, ``path``) describing
    every violation found. The string form of the exception is a multi-line
    summary suitable for logs and error pages.
    """

    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        summary = "\n".join(
            f"  - [{e['path'] or '<root>'}] {e['message']}" for e in errors
        )
        super().__init__(
            f"ORD document failed schema validation ({len(errors)} error"
            f"{'s' if len(errors) != 1 else ''}):\n{summary}"
        )


@cache
def load_spec_schema(name: str = "Document") -> dict[str, Any]:
    """Return one of the bundled ORD JSON Schemas as a parsed dict.

    ``name`` is the schema's stem — ``"Document"`` (default) or
    ``"Configuration"``. Cached for the lifetime of the process; the schemas
    are large-ish and unchanging at runtime.
    """
    schema_text = (
        files("ord._spec").joinpath(f"{name}.schema.json").read_text()
    )
    return json.loads(schema_text)


def _validate(data: dict[str, Any], schema_name: str) -> None:
    validator = Draft7Validator(load_spec_schema(schema_name))
    errors = [
        {
            "path": "/".join(str(p) for p in err.absolute_path),
            "message": err.message,
        }
        for err in validator.iter_errors(data)
    ]
    if errors:
        raise ORDValidationError(errors)


def validate_ord_document(data: dict[str, Any]) -> None:
    """Validate ``data`` against the ORD Document JSON Schema.

    Returns ``None`` on success and raises :class:`ORDValidationError` on
    failure. All schema violations are collected before raising — callers
    don't have to fix-and-retry one error at a time.
    """
    _validate(data, "Document")


def validate_ord_configuration(data: dict[str, Any]) -> None:
    """Validate ``data`` against the ORD Configuration JSON Schema.

    The Configuration manifest is the small document served at
    ``/.well-known/open-resource-discovery`` listing where the full ORD
    documents live. Same error semantics as :py:func:`validate_ord_document`.
    """
    _validate(data, "Configuration")

"""Validate ORD documents against the official ORD JSON Schema.

The schema is vendored at ``src/ord/_spec/Document.schema.json`` and refreshed
manually via ``scripts/refresh_spec.py`` (see ``docs/vendored-schema.md``).
Validation is opt-in: nothing runs at model construction time, so building
intermediate documents stays cheap. Call
:py:func:`validate_ord_document` (or :py:meth:`ORDDocument.validate_against_spec`)
when you want a spec compliance check.
"""

from __future__ import annotations

import json
from functools import lru_cache
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


@lru_cache(maxsize=1)
def load_spec_schema() -> dict[str, Any]:
    """Return the bundled ORD JSON Schema as a parsed dict.

    Cached for the lifetime of the process — the schema is ~440 KB and
    unchanging at runtime.
    """
    schema_text = (
        files("ord._spec").joinpath("Document.schema.json").read_text()
    )
    return json.loads(schema_text)


def validate_ord_document(data: dict[str, Any]) -> None:
    """Validate ``data`` against the ORD JSON Schema.

    Returns ``None`` on success and raises :class:`ORDValidationError` on
    failure. All schema violations are collected before raising — callers
    don't have to fix-and-retry one error at a time.
    """
    validator = Draft7Validator(load_spec_schema())
    errors = [
        {
            "path": "/".join(str(p) for p in err.absolute_path),
            "message": err.message,
        }
        for err in validator.iter_errors(data)
    ]
    if errors:
        raise ORDValidationError(errors)

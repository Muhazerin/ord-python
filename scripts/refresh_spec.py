"""Refresh the vendored ORD JSON Schemas.

Run when bumping the supported ORD spec version. Downloads the schemas
from the spec website (which serves JSON-converted copies of the YAML
that lives in the open-resource-discovery/specification repo) and writes
them to src/ord/_spec/.

Two schemas are vendored:

- ``Document.schema.json`` — the ORD Document itself.
- ``Configuration.schema.json`` — the manifest served at
  ``/.well-known/open-resource-discovery``.

The source URLs are intentionally unversioned: the spec site always serves
the latest published spec. To audit which version was retrieved, this
script reads back ``properties.openResourceDiscovery.enum`` from the
Document schema and prints the highest value seen.

Usage::

    python scripts/refresh_spec.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

SOURCES = {
    "Document.schema.json": (
        "https://open-resource-discovery.org/spec-v1/interfaces/Document.schema.json"
    ),
    "Configuration.schema.json": (
        "https://open-resource-discovery.org/spec-v1/interfaces/Configuration.schema.json"
    ),
}
SPEC_DIR = Path(__file__).resolve().parent.parent / "src" / "ord" / "_spec"


def _fetch_and_write(name: str, url: str) -> dict:
    print(f"Fetching {url}", file=sys.stderr)
    with urllib.request.urlopen(url) as resp:  # noqa: S310 — known URL
        raw = resp.read()
    schema = json.loads(raw)
    target = SPEC_DIR / name
    target.write_text(json.dumps(schema, indent=2, sort_keys=False) + "\n")
    print(f"  → {target.relative_to(Path.cwd())} ({len(raw):,} bytes)", file=sys.stderr)
    return schema


def main() -> int:
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    document_schema = _fetch_and_write("Document.schema.json", SOURCES["Document.schema.json"])
    _fetch_and_write("Configuration.schema.json", SOURCES["Configuration.schema.json"])

    versions = (
        document_schema.get("properties", {})
        .get("openResourceDiscovery", {})
        .get("enum", [])
    )
    latest = versions[-1] if versions else "?"
    print(f"\nSpec versions in Document schema: {versions}", file=sys.stderr)
    print(f"Latest: {latest}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

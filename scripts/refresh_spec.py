"""Refresh the vendored ORD JSON Schema.

Run when bumping the supported ORD spec version. Downloads the schema
from the spec website (which serves a JSON-converted copy of the YAML
that lives in the open-resource-discovery/specification repo) and writes
it to src/ord/_spec/Document.schema.json.

The source URL is intentionally unversioned: the spec site always serves
the latest published spec. To audit which version was retrieved, this
script reads back ``properties.openResourceDiscovery.enum`` from the
downloaded schema and prints the highest value seen — that is the
freshly-fetched spec version.

Usage::

    python scripts/refresh_spec.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = "https://open-resource-discovery.org/spec-v1/interfaces/Document.schema.json"
TARGET = Path(__file__).resolve().parent.parent / "src" / "ord" / "_spec" / "Document.schema.json"


def main() -> int:
    print(f"Fetching {SOURCE_URL}", file=sys.stderr)
    with urllib.request.urlopen(SOURCE_URL) as resp:  # noqa: S310 — known URL
        raw = resp.read()

    # Round-trip through json to normalize formatting (and validate).
    schema = json.loads(raw)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(schema, indent=2, sort_keys=False) + "\n")

    versions = (
        schema.get("properties", {})
        .get("openResourceDiscovery", {})
        .get("enum", [])
    )
    latest = versions[-1] if versions else "?"
    print(f"Wrote {TARGET.relative_to(Path.cwd())} ({len(raw):,} bytes)", file=sys.stderr)
    print(f"Spec versions in schema: {versions}", file=sys.stderr)
    print(f"Latest: {latest}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

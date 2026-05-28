# Vendored ORD JSON Schema

`Document.schema.json` is a vendored copy of the official ORD Document schema, used by `ord.core.validate_ord_document` to validate emitted documents against the spec.

## Source

- URL: <https://open-resource-discovery.org/spec-v1/interfaces/Document.schema.json>
- License: Apache-2.0 (the upstream repo at <https://github.com/open-resource-discovery/specification> is Apache-2.0).
- Spec version: see `properties.openResourceDiscovery.enum` in the file — the highest entry is the latest spec the schema accepts.
- Format: JSON Schema Draft 7.

## Refresh

The source URL is unversioned — the spec site serves whatever is currently published. To pull the latest:

```bash
python scripts/refresh_spec.py
```

Then commit the resulting diff. Bump `ORDSpecVersion` in `src/ord/core/models.py` if new spec versions appear in `openResourceDiscovery.enum`.

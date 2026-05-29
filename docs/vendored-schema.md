# Vendored ORD JSON Schemas

Two schemas live under `src/ord/_spec/`, used by `ord.core.validate_ord_document` and `ord.core.validate_ord_configuration` to validate emitted artifacts against the spec.

- `Document.schema.json` — the ORD Document itself.
- `Configuration.schema.json` — the manifest served at `/.well-known/open-resource-discovery`, listing where the actual ORD documents live.

## Source

- Document: <https://open-resource-discovery.org/spec-v1/interfaces/Document.schema.json>
- Configuration: <https://open-resource-discovery.org/spec-v1/interfaces/Configuration.schema.json>
- License: Apache-2.0 (the upstream repo at <https://github.com/open-resource-discovery/specification> is Apache-2.0).
- Spec version: see `properties.openResourceDiscovery.enum` in the Document schema — the highest entry is the latest spec the schema accepts.
- Format: JSON Schema Draft 7 for both.

## Refresh

The source URLs are unversioned — the spec site serves whatever is currently published. To pull the latest:

```bash
python scripts/refresh_spec.py
```

Then commit the resulting diff. Bump `ORDSpecVersion` in `src/ord/core/models.py` if new spec versions appear in `openResourceDiscovery.enum`.

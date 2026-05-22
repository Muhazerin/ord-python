# ord-python

Open Resource Discovery (ORD) plugin for Python services — primarily FastAPI and FastMCP.

The Python counterpart to [`cap-js/ord`](https://github.com/cap-js/ord). Generates ORD documents that describe a service's REST API, MCP surface, and (where applicable) A2A agent metadata, and serves them at the standard discovery endpoints.

> **Status:** pre-alpha. APIs will change. See `python-plugin-handoff.md` for design context.

## Install

```bash
pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

## References

- [ORD specification](https://open-resource-discovery.org/)
- [cap-js/ord (upstream reference impl)](https://github.com/cap-js/ord)
- [A2A protocol](https://a2a-protocol.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

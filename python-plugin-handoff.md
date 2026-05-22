# Python ORD Plugin — Handoff Note

> **Read me first.** This file exists to bootstrap a fresh Claude session in a new repo. It captures the context, decisions, and open questions from the prior session so we don't start from scratch.

## TL;DR

Build a Python plugin that generates [Open Resource Discovery](https://open-resource-discovery.org/) (ORD) documents for FastAPI and FastMCP services, modeled on the existing CAP-Java plugin at [cap-js/ord](https://github.com/cap-js/ord). The first concrete consumer is a service called **DAMN** (FastAPI + FastMCP) that needs to publish an ORD document describing its REST API, MCP surface, and an Agent Document Card JSON Schema contract.

---

## 1. Why this plugin exists

### Background

- **ORD** is SAP's open spec for machine-readable service metadata. A service publishes an ORD document at `/.well-known/open-resource-discovery` (and/or `/ord/v1/documents/ord-document`). Discoverers (UCL, UMS, etc.) crawl those endpoints and aggregate metadata.
- **`cap-js/ord`** is the reference implementation for CAP (Node.js / SAP CAP framework). It hooks into `cds build --for ord` and `cds.compile.to.ord(csn)`, walks the CAP service model (CSN), and emits ORD JSON plus companion artifacts (OpenAPI, AsyncAPI, EDMX).
- **No equivalent exists for Python.** Teams using FastAPI / FastMCP currently can't generate ORD documents without writing them by hand.

### Motivation

The author runs a service called **DAMN** built on FastAPI + FastMCP and wants ORD support. Other SAP teams using FastAPI/FastMCP have the same need. A reusable plugin is more valuable than DAMN-specific glue.

---

## 2. Repo decisions (settled)

- **New repo, not a fork-overwrite of cap-js/ord.** Different language, different ecosystem, different audience. The existing fork at `~/Documents/Side-Quests/ord` stays as a **read-only upstream watcher** so we can `git fetch upstream` and diff `lib/` to spot new features to port.
- **Suggested layout** (refine in the new repo):

  ```
  ord-py/                         (working name — see open questions)
  ├── src/ord/
  │   ├── core/                   # framework-agnostic ORD model + serialization
  │   ├── adapters/
  │   │   ├── fastapi.py          # introspect FastAPI app → ORD apiResources
  │   │   └── fastmcp.py          # introspect FastMCP server → ORD apiResources
  │   ├── auth/                   # open / basic / mtls (mirror cap-js/ord)
  │   ├── server.py               # mounts /.well-known/open-resource-discovery, /ord/v1/...
  │   └── cli.py                  # `ord build` equivalent of `cds build --for ord`
  ├── tests/
  ├── examples/
  │   ├── fastapi_app/
  │   └── fastmcp_app/
  ├── docs/
  │   └── upstream-parity.md      # cap-js/ord features → ported / TODO / N/A
  └── pyproject.toml
  ```

- **`core/` is strictly framework-agnostic.** Mirror cap-js/ord's concept names (apiResource, eventResource, entityType, package, consumptionBundle, integrationDependency) so upstream porting stays mechanical.
- **Adapters are thin.** They translate framework introspection (FastAPI routes, FastMCP tools) into `core/` model objects. Don't entangle FastAPI specifics with the ORD model.

---

## 3. Upstream tracking strategy (settled)

We want to know when cap-js/ord ships features so we can port them.

1. **Watch cap-js/ord releases on GitHub** (Watch → Custom → Releases). They tag and ship `CHANGELOG.md` per release.
2. **Keep the fork at `~/Documents/Side-Quests/ord` as a read-only upstream mirror.** Periodically `git fetch upstream && git log upstream/main..` to read the diff of `lib/` semantically.
3. **Maintain `docs/upstream-parity.md`** in the Python repo: a table mapping cap-js/ord features → ported / TODO / not-applicable. This is the roadmap and the "did we forget anything?" checklist.

Optional (skip until parity matrix stabilizes): a weekly GitHub Action in the Python repo that diffs `cap-js/ord/CHANGELOG.md` and opens an issue when there's a new release.

---

## 4. cap-js/ord at a glance

The relevant pieces from `~/Documents/Side-Quests/ord`:

- **Entry points**: `cds-plugin.js` registers `cds build --for ord` and exposes `cds.compile.to.ord(csn)`.
- **Pipeline**: `lib/ord.js` orchestrates; `lib/templates.js` builds resource entries; `lib/defaults.js` provides products/packages defaults; `lib/extend-ord-with-custom.js` merges user-supplied custom ORD content.
- **Companion artifacts**: delegates to `@cap-js/openapi` and `@cap-js/asyncapi`, plus EDMX, written into `gen/ord/`.
- **Runtime endpoints**: `lib/services/ord-service.{cds,js}` serves discovery endpoints.
- **Auth**: `lib/auth/` — Open / Basic / CF mTLS, configurable via env or `.cdsrc.json`.
- **Worker pool**: `lib/threads/compile.js` parallelizes via `piscina`.

The split worth keeping in mind: **(a) introspect framework metadata → ORD JSON** vs **(b) serve discovery endpoints with auth.** The JSON shape is framework-agnostic; only (a) is CAP-specific.

---

## 5. ORD modeling decisions for the FastAPI/FastMCP case

### FastAPI service → `apiProtocol: "rest"` (settled)

FastAPI exposes `/openapi.json` for free. The plugin emits:

```json
{
  "ordId": "...:apiResource:MyService:v1",
  "apiProtocol": "rest",
  "resourceDefinitions": [
    { "type": "openapi-v3", "mediaType": "application/json",
      "url": "/openapi.json", "accessStrategies": [{ "type": "open" }] }
  ]
}
```

### FastMCP service → `apiProtocol: "mcp"` (settled, with caveat)

ORD spec ([apiProtocol reference](https://open-resource-discovery.org/spec-v1/interfaces/Document#api-resource_apiprotocol)) recognizes `"mcp"` as a first-class protocol, but notes:

> Currently there is no standard API Resource definition type for MCP.

**Decision**: emit `apiProtocol: "mcp"` and either (i) omit `resourceDefinitions` (similar to `delta-sharing`'s allowance for runtime discovery), or (ii) attach a `type: "custom"` definition pointing at our own JSON schema describing the MCP server's tools/resources/prompts.

This is a place where the Python plugin **leads upstream** — cap-js/ord doesn't model MCP today. Worth contributing the convention back once stable.

### A2A agents → `apiProtocol: "a2a"` (settled)

If the FastAPI service is also an A2A agent, emit a **second** apiResource alongside the REST one:

```json
{
  "ordId": "...:apiResource:MyAgent:v1",
  "apiProtocol": "a2a",
  "resourceDefinitions": [
    { "type": "a2a-agent-card", "mediaType": "application/json",
      "url": "/.well-known/agent.json", "accessStrategies": [{ "type": "open" }] }
  ]
}
```

The A2A card content (including any data-only extensions like the DAMN document card) is **the agent author's responsibility, not the plugin's**. The plugin only publishes the pointer.

### DAMN's specific case — Agent Document Card schema (settled)

DAMN is the **consumer** of Agent Document Cards (cards live inside agents' A2A cards as data-only extensions). DAMN's own ORD does NOT republish agent cards. Instead, DAMN's ORD publishes the **schema contract** that agent authors must conform to.

Slot: a dedicated apiResource with `type: "custom"`:

```json
{
  "ordId": "sap.damn:apiResource:AgentDocumentCardSchema:v1",
  "title": "DAMN Agent Document Card Schema",
  "apiProtocol": "rest",
  "resourceDefinitions": [
    { "type": "custom",
      "customType": "sap.damn:spec:agent-document-card:v1",
      "mediaType": "application/json",
      "url": "/schemas/agent-document-card.v1.json",
      "accessStrategies": [{ "type": "open" }] }
  ],
  "extensible": { "supported": "no" }
}
```

Rationale and the discovery chain are in `agent-document-card-note.md` (in the prior session's repo). Copy that note into the new Python repo's `docs/` for future reference.

**Three layers, one indirection each — don't collapse them**:
- DAMN's ORD answers: "how should agents shape the DAMN extension?"
- An agent's ORD answers: "where is my A2A card?"
- The A2A card answers: "what does this specific agent need?"

---

## 6. First-milestone checklist (suggested order)

A new Claude can pick these up in order. Each is small enough to land independently.

1. **Bootstrap the repo**: `pyproject.toml`, `src/ord/` skeleton, `pytest`, `ruff`, basic CI.
2. **Build `core/` ORD model**: Pydantic (or plain dataclasses) for ORDDocument, APIResource, ResourceDefinition, AccessStrategy, Package, Product, ConsumptionBundle. Mirror cap-js/ord field names exactly.
3. **JSON serialization + schema validation** against the ORD JSON Schema (download from open-resource-discovery.org).
4. **FastAPI adapter (minimum viable)**: given a `FastAPI` instance, emit one `apiProtocol: "rest"` apiResource pointing at `/openapi.json`. Test against an `examples/fastapi_app/`.
5. **`server.py`**: a FastAPI router that mounts `/.well-known/open-resource-discovery` and `/ord/v1/documents/ord-document` returning the generated document.
6. **CLI**: `ord build --for <module>` equivalent — generates the JSON and companion artifacts into `gen/ord/`.
7. **FastMCP adapter**: `apiProtocol: "mcp"` apiResource. Decide between omitting `resourceDefinitions` vs `type: "custom"` with our own MCP schema. Document the decision.
8. **A2A apiResource support**: detect/configure A2A agent cards. Add example in `examples/`.
9. **DAMN-specific demo**: end-to-end example in `examples/` showing all three apiResources (REST + MCP + Agent Document Card schema) for a DAMN-shaped service.
10. **Auth strategies**: port `open` first, then `basic`, then mTLS. Mirror cap-js/ord config shape (`.cdsrc.json` equivalent — probably `pyproject.toml` `[tool.ord]` table or a dedicated `ord.toml`).
11. **`docs/upstream-parity.md`**: seed the matrix from cap-js/ord's `lib/` directory.

---

## 7. Open questions (negotiable — flag to the user before deciding)

- **Repo name.** Working name is `ord-py`. Alternatives: `fastapi-ord`, `ord-fastapi`, `pyord`. The author hasn't picked. Ask before creating the GitHub repo.
- **MCP `resourceDefinition` shape.** Omit (lean on protocol-level discovery) vs `type: "custom"` with a JSON schema we author? Likely settle this in milestone 7 after seeing what FastMCP introspection can extract.
- **DAMN transport for Agent Document Cards.** The DAMN team has Options 0 / 1 / 2 (Direct HTTP, Pull via ORD/A2A extension, Push — TBD) on the table; final choice is deferred pending alignment with the Agent Platform team (Felipe Morais, Thiago Bohn). The plugin only needs to support Option 1's prerequisites (publish A2A card + reference from ORD); other transports are DAMN-internal concerns. Confirm this scoping with the author when the topic comes up.
- **Config file format.** cap-js/ord uses `.cdsrc.json`. Python idiom would be `pyproject.toml` `[tool.ord]` table or a dedicated `ord.toml`. Ask before committing.
- **Pydantic vs dataclasses for `core/`.** Pydantic gets validation + JSON serialization for free but adds a dep. Dataclasses are stdlib but require manual schema work. Lean Pydantic unless the author has a preference.
- **Worker pool / parallelism.** cap-js/ord uses `piscina` for parallel compile. Python equivalent (`multiprocessing`, `concurrent.futures`) — only worth porting once the single-threaded path works and we hit a real performance need. Defer.

---

## 8. Pointers

- **Upstream**: https://github.com/cap-js/ord — local read-only mirror at `~/Documents/Side-Quests/ord`.
- **ORD spec**: https://open-resource-discovery.org/
- **ORD agents example**: https://open-resource-discovery.org/spec-v1/examples/document-agents
- **A2A spec**: https://a2a-protocol.org/
- **MCP**: https://modelcontextprotocol.io/
- **Prior session's note on DAMN's Agent Document Card schema slot**: `~/Documents/Side-Quests/ord/agent-document-card-note.md` — copy into the new repo's `docs/`.

---

## 9. Conventions for the new Claude session

- The author prefers concise, direct answers. Skip throat-clearing.
- Present recommendations with tradeoffs, not decided plans. Wait for agreement before implementing.
- Settled decisions in this doc are settled — don't re-litigate without reason.
- Open questions in §7 are open — surface them before silently picking.
- The author has a Buddy companion (MCP server) — call `buddy_observe` after coding tasks with a one-sentence summary. Optional but expected.

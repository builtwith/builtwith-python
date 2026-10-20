# Repository discovery and decisions

Inspected `CLAUDE.md`, workspace `AGENTS.md`, Node REST and AI SDK clients, C# REST
client, AI SDK README, MCP licensing, code examples, and existing release workflow.
The workspace contains separate Git repositories, not one root Git repository.
`builtwith-python/` is a standalone release unit at https://github.com/builtwith/builtwith-python.

- `builtwith-node-api/src/index.js`: direct REST wrapper, query-key authentication,
  older Domain v25, Lists v12, Relationships v4.
- `builtwith-csharp-api/BuiltWith/BuiltWithClient.cs`: sync/async REST, typed models,
  client ownership and JSON deserialization conventions.
- `builtwith-ai-sdk/node/src/index.js` and `csharp/`: MCP-based clients, structured
  results and retries. Python uses direct REST to avoid an unnecessary protocol hop.
- `builtwith-mcp/`: existing independent Node MCP server; MIT license.
- `builtwith-code-examples/`: already contains Python REST scripts. Added SDK-based
  examples rather than duplicating all existing scripts or changing their dependencies.
- Existing CI publishes Node packages on version tags. Python gets independent build
  validation without adding Python to existing project workflows.
- The local API project's `llms.txt` and `llms-full.txt` provide newer verified contracts:
  Domain v26, Lists v13, Relationships v5, registry v2, header authentication, pagination,
  response shapes, rate/credit headers and access guidance.
- The documented public OpenAPI URL describes `/agent/*` x402 payment routes, not a
  complete specification of the regular REST API. It is not used to generate this SDK.
- Existing tests are project-specific; no shared Python integration suite or shared REST
  schema was found. `docs/endpoints.json` records this SDK's verified inventory.
- PyPI `builtwith` belongs to Richard Penman's unrelated technology detector. Its name
  and import path are not reused. `builtwith-official` returned 404 at discovery;
  this is not a reservation or proof that PyPI will permit registration.

## Scope boundaries

This release supports JSON REST. XML, CSV, XLSX and text exports are not wrapped.
Financial/social APIs exist in older workspace inventory but lack contracts in the
current full reference, so they are not guessed. Domain category/vertical indexes and
special-domain reference lists are documented upstream but not exposed in this release.
Device-code authorization, payment purchasing (MPP/x402/billing), Live Feed WebSockets,
are outside scope. Optional MCP support connects to the existing BuiltWith server
using the official Python ClientSession; it does not create another server.

All response fields are preserved as recursive JSON rather than incomplete per-endpoint
dataclasses. Runtime endpoint calls and exposed method parameters have explicit annotations.
Future methods should be added to both clients, inventory, reference and contract tests.
The SDK is independent of Node, C#, ASP.NET, CLI, TUI and their build systems.

Source code, TOML, JSON, shell-launchable scripts and YAML use UTF-8 without BOM for
tooling compatibility. New Markdown documentation uses UTF-8 with BOM. Existing
documentation edits preserve original encoding/BOM.


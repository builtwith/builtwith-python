# Development and release

From this directory:

```bash
python -m venv .venv
# Activate .venv (Windows: .venv\Scripts\Activate.ps1)
python -m pip install -e ".[dev,mcp]"
python -m pytest --cov=builtwith_official --cov-report=term-missing
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m build
python -m twine check dist/*
```

Normal tests use HTTPX MockTransport; no credentials, LLM or paid requests are required.
MCP tests skip without the extra. Live tests require `BUILTWITH_LIVE_TESTS=1`; account
tests additionally require `BUILTWITH_API_KEY`. These tests only use public VAT types and
credit-free Usage. Never add paid endpoints to live tests without explicit approval.

Custom transports are passed with `transport=httpx.MockTransport(handler)` or an
HTTPX transport configured for your network. The SDK owns and closes the transport.
Do not share one owned transport between clients with different lifetimes. Async clients
belong to the event loop in which they are used. Async cancellation propagates normally.

The CI matrix validates Python 3.10–3.14 on Linux plus 3.12 on Windows. It builds/checks
wheel and sdist; it never publishes. This workflow belongs only to the standalone SDK.

## Release checklist

1. Confirm the `builtwith-official` name can be registered by the BuiltWith PyPI account.
   `builtwith` is already an unrelated package. Do not claim it.
2. Review and push source to `https://github.com/builtwith/builtwith-python`.
   Keep repository metadata and documentation synchronized with the release.
3. Update package version in `pyproject.toml` and `__init__.py`, User-Agent strings and
   changelog. Run all validation commands and inspect wheel/sdist contents.
4. Install the built wheel in a fresh environment and run a public reference smoke test.
5. Configure PyPI Trusted Publishing for an explicitly approved release workflow, with
   a protected GitHub environment. Alternatively use Twine with a scoped token supplied
   through a secret store; never save tokens in `.pypirc`, source or command history.
6. Upload to TestPyPI first if desired, verify installation and metadata, then publish
   the reviewed distributions to PyPI only after explicit release authorization.
7. Tag/release the reviewed Git commit and update installation links after publication.

The build allowlist includes only package source, tests, public docs/examples and project
metadata. Virtual environments, caches, `.env`, Git internals and workspace siblings are
excluded. No release token is needed to build or check artifacts.


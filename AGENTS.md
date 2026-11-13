# Project instructions

@C:\Users\Iglesias\.codex\RTK.md

## Python typing

- Use explicit parameter and return annotations for every function and method, including tests, fixtures, nested functions, and callbacks. Leave `self` and `cls` implicit.
- Annotate module constants, instance attributes, and empty collections. Local values with an obvious inferred type do not need redundant annotations.
- Specify collection element types. Reuse the shared `TypedDict` contracts in `src/models/contracts.py` for readings and channel metadata.
- Use concrete library types for HTTP, MQTT, WebSocket, and pytest interfaces. Use `object` for unvalidated external data and narrow it through runtime checks. Do not use `Any` to bypass typing.
- Preserve runtime validation, error handling, and API behavior when adding annotations.
- Run `uv run ruff check src tests` and `uv run pytest --cov --cov-report=term-missing` after changes. Ruff's `ANN` rules enforce function annotations across source code and tests.

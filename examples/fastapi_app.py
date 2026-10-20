"""Optional FastAPI application factory; install fastapi and an ASGI server separately.

Add application authentication and quotas before exposing paid lookups to users.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from builtwith_official import APIError, AsyncBuiltWith, JSONValue, TransportError


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with AsyncBuiltWith() as client:
            app.state.builtwith = client
            yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/technologies/{domain}")
    async def technologies(domain: str) -> JSONValue:
        try:
            client: AsyncBuiltWith = app.state.builtwith
            return (await client.domain(domain, no_pii=True)).data
        except (APIError, TransportError):
            raise HTTPException(status_code=502, detail="BuiltWith lookup failed") from None

    return app

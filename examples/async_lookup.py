"""Async script; use await main() directly in Jupyter. Lookup consumes API credits."""

import asyncio

from builtwith_official import AsyncBuiltWith


async def main() -> None:
    async with AsyncBuiltWith() as client:
        result = await client.domain("example.com", no_pii=True)
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())

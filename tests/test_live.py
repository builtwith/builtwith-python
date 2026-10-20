"""Explicitly opted-in live tests; never call a credit-consuming endpoint."""

import os

import pytest

from builtwith_official import AsyncBuiltWith, BuiltWith

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.getenv("BUILTWITH_LIVE_TESTS") != "1", reason="Live tests disabled"),
]


def test_public_reference():
    with BuiltWith() as client:
        assert isinstance(client.vat_types().data, list)


async def test_account():
    if not os.getenv("BUILTWITH_API_KEY"):
        pytest.skip("No integration credential")
    async with AsyncBuiltWith() as client:
        assert isinstance((await client.usage()).data, dict)

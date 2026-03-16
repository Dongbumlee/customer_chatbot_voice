"""Root test configuration."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as the default async backend."""
    return "asyncio"

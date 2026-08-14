from __future__ import annotations

import asyncio
import sys
from os.path import abspath, dirname, join

import pytest
import pytest_asyncio

d = dirname(dirname(abspath(__file__)))
sys.path.append(f"{d}\\")
sys.path.append(f"{d}\\src")

d = dirname(dirname(abspath(__file__)))
sys.path.append(join(d))
sys.path.append(join(d, "src"))


from tests.load_bot_from_pickle import build_bot_object_from_pickle_data


@pytest_asyncio.fixture(scope="class")
async def bot(request):
    map_path = request.param
    bot = await build_bot_object_from_pickle_data(map_path)
    yield bot


@pytest.fixture
def event_loop(_function_scoped_runner: asyncio.Runner):
    """
    Compatibility fixture for tests that still request an `event_loop` parameter.

    pytest-asyncio (>=1.x) manages the loop lifecycle via asyncio.Runner fixtures
    (e.g. `_function_scoped_runner`). We must *not* close the loop ourselves,
    otherwise pytest-asyncio teardown will fail with "RuntimeError: Event loop is closed".
    """

    return _function_scoped_runner.get_loop()

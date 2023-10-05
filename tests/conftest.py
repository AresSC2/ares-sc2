import asyncio

import pytest_asyncio

from tests.load_bot_from_pickle import build_bot_object_from_pickle_data


@pytest_asyncio.fixture(scope="class")
async def bot(request):
    map_path = request.param
    bot = await build_bot_object_from_pickle_data(map_path)
    yield bot


@pytest_asyncio.fixture(scope="class")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

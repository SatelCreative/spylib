import pytest

from spylib.utils.misc import get_unique_id


@pytest.mark.asyncio
async def test_calculate_from_message():
    assert len(get_unique_id()) == 10

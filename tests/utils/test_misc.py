import pytest

from spylib.utils.misc import snake_to_camel_case


@pytest.mark.parametrize(
    'text,expected',
    [('callback_url', 'callbackUrl'), ('pub_sub_topic', 'pubSubTopic')],
    ids=['2 elements', '3 elements'],
)
def test_snake_to_camel_case(text, expected):
    restult = snake_to_camel_case(text=text)

    assert restult == expected

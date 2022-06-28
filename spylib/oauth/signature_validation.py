from json import dumps
from typing import List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode

from spylib.hmac import validate


def validate_signed_query_string(query_string: str, *, api_secret_key: str):
    """Validates that a query string has been signed by Shopify.

    [Implements the parsing algorithm defined by Shopify here](https://shopify.dev/apps/auth/oauth/getting-started#step-7-verify-a-request).
    Including the special case [`ids` parameter parsing](https://shopify.dev/apps/auth/oauth/getting-started#ids-array-parameter)


    Args:
        query_string: A valid query string. `hmac=123&test=456`
        api_secret_key: The api secret key from Shopify partners.

    Raises:
        Exception: `ValueError`
    """

    signature: Optional[str] = None
    query_params: List[Tuple[str, str]] = []

    # I tried a number of options here to avoid doing
    # manual parsing and string manipulation. `parse_qs`
    # can work as long as you pass `doseq=True` & `quote_via=quote``
    # to urlencode. It does not, however, handle the ids param.
    # The code ended up being cleaner this way in one loop.

    ids: List[str] = []
    for key, value in parse_qsl(query_string, strict_parsing=True):
        if key == 'hmac':
            signature = value
            continue
        if key == 'ids[]':
            if not ids:
                query_params.append(('ids', ''))
            ids.append(value)
            continue
        query_params.append((key, value))

    # `safe` param via: https://stackoverflow.com/a/49244224
    message = urlencode(query_params, safe=':/').replace('ids=', f'ids={dumps(ids)}')

    validate(
        sent_hmac=signature or '',
        message=message,
        secret=api_secret_key,
    )

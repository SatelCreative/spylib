from json import dumps
from typing import List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode

from spylib.hmac import validate

# A random symbol used as a placeholder
_SYMBOL = 'zQMAUY2pdppBsVRBUsJAXDbU2fngq2'


def validate_hmac(*, query_string: str, api_secret_key: str):
    """https://shopify.dev/apps/auth/oauth/getting-started#step-7-verify-a-request

    Args:
        query_string: _description_
        api_secret_key: _description_

    Raises:
        Exception: _description_
    """

    provided_hmac: Optional[str] = None
    query_params: List[Tuple[str, str]] = []

    # https://shopify.dev/apps/auth/oauth/getting-started#ids-array-parameter
    ids: List[str] = []
    for key, value in parse_qsl(query_string, strict_parsing=True):
        if key == 'hmac':
            provided_hmac = value
            continue
        if key == 'ids[]':
            if not ids:
                query_params.append(('ids', _SYMBOL))
            ids.append(value)
            continue
        query_params.append((key, value))

    message = urlencode(query_params, safe=':/').replace(_SYMBOL, dumps(ids))

    if not provided_hmac:
        raise Exception('todo')

    validate(
        sent_hmac=provided_hmac,
        message=message,
        secret=api_secret_key,
    )

    # query_params = parse_qs(query_string, strict_parsing=True)
    # (provided_hmac,) = query_params.pop('hmac')

    # ids_encoded = ''
    # if 'ids[]' in query_params:
    #     ids_encoded = dumps(query_params['ids[]'])
    #     query_params['ids[]'] = [SYMBOL]
    #     query_params = {
    #         key if key != 'ids[]' else 'ids': value for key, value in query_params.items()
    #     }

    # message = urlencode(query_params, safe=':/', doseq=True, quote_via=quote).replace(
    #     SYMBOL, ids_encoded
    # )

    # print('QUERY', query_params)
    # print('HMAC', provided_hmac)
    # print('MESSAGE', message)

    # validate(
    #     sent_hmac=provided_hmac,
    #     message=message,
    #     secret=api_secret_key,
    # )

    # query_params = parse_qsl(query_string, strict_parsing=True)
    # provided_hmac = dict(query_params)['hmac']
    # message = urlencode([q for q in query_params if q[0] != 'hmac'], safe=':/')

    # print('QUERY', query_params)
    # print('HMAC', provided_hmac)
    # print('MESSAGE', message)

    # validate(
    #     sent_hmac=provided_hmac,
    #     message=message,
    #     secret=api_secret_key,
    # )

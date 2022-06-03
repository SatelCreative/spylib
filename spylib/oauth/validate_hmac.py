from json import dumps
from typing import List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode

from spylib.hmac import validate

SYMBOL = 'zQMAUY2pdppBsVRBUsJAXDbU2fngq2'


def validate_hmac(*, query_string: str, api_secret_key: str):
    provided_hmac: Optional[str] = None
    query_params: List[Tuple[str, str]] = []

    ids: List[str] = []
    for key, value in parse_qsl(query_string, strict_parsing=True):
        if key == 'hmac':
            provided_hmac = value
            continue
        if key == 'ids[]':
            if not ids:
                query_params.append(('ids', SYMBOL))
            ids.append(value)
            continue
        query_params.append((key, value))

    message = urlencode(query_params, safe=':/').replace(SYMBOL, dumps(ids))

    if not provided_hmac:
        raise Exception('todo')

    validate(
        sent_hmac=provided_hmac,
        message=message,
        secret=api_secret_key,
    )

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

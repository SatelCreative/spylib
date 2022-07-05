from .tokens import OAuthJWT
from .validations import validate_callback, validate_oauthjwt


def process_callback(
    shop: str, timestamp: int, query_string: str, api_secret_key: str, state: str, private_key: str
) -> OAuthJWT:

    validate_callback(
        shop=shop,
        timestamp=timestamp,
        query_string=query_string,
        api_secret_key=api_secret_key,
    )
    oauthjwt: OAuthJWT = validate_oauthjwt(token=state, shop=shop, jwt_key=private_key)

    return oauthjwt

from pydantic import BaseSettings


class Configuration(BaseSettings):
    api_key: str
    secret_key: str
    handle: str

    class Config:
        env_prefix = 'SHOPIFY_'  # defaults to no prefix, i.e. ""


conf = Configuration()

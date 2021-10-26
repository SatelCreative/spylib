from pydantic import BaseSettings


class Configuration(BaseSettings):
    api_key: str
    secret_key: str

    class Config:
        env_prefix = 'SHOPIFY_'  # defaults to no prefix, i.e. ""


conf = Configuration()

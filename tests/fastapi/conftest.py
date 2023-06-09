from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pytest import fixture

from spylib.fastapi import authenticate_webhook_hmac

app = FastAPI()


@app.post('/webhook_hmac')
def authenticate(hmac: bool = Depends(authenticate_webhook_hmac)):
    return hmac


@fixture()
def client():
    with TestClient(app) as client:
        yield client

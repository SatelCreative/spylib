# Session Tokens

The [session token](https://shopify.dev/apps/auth/session-tokens/authenticate-an-embedded-app-using-session-tokens)
functionality can be used to verify the session for the user. The suggested syntax is to define a dependency:

```python
from spylib.utils import SessionToken

def parse_session_token(request: Request):
    SessionToken.from_header(request.headers.get('Authorization'), api_key, secret)
```

This can be used in FastAPI in the following way:

```python
@app.get("/items/")
async def read_items(session: SessionToken = Depends(parse_session_token)):
  # Some api code
```

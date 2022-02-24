# Change Shopify API version
- As shown in the `Implement Token Classes`, token can be used as following:
```python
from spylib import OfflineTokenABC


class OfflineToken(OfflineTokenABC):
  async def save(self):
      pass

  @classmethod
  async def load(cls, store_name: str):
      pass
```

- If the Shopify API version used in Spylib is not the desired version, it can be changed with the following:
```python
class OfflineToken(OfflineTokenABC):
  # Add the version to be used here
  api_version: '2022-01'
  async def save(self):
      pass

  @classmethod
  async def load(cls, store_name: str):
      pass
```
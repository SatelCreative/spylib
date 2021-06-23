"""A library to facilitate interfacing with Shopify's API"""

__version__ = '0.1.1'


from .multipass import Multipass
from .store import Store, UniqueStore

__all__ = ['Store', 'UniqueStore', 'Multipass']

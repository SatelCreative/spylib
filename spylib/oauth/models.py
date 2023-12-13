from typing import Annotated, List

from pydantic import BaseModel, BeforeValidator

from spylib.utils.misc import parse_scope


class OfflineTokenModel(BaseModel):
    """[Read more about Offline access](https://shopify.dev/apps/auth/oauth/access-modes#offline-access)."""

    access_token: str
    """
    An API access token that can be used to access the shop's data as long as your app is installed. Your app should store the token somewhere to make authenticated requests for a shop’s data.
    """

    scope: Annotated[List[str], BeforeValidator(parse_scope)]
    """
    The list of access scopes that were granted to your app and are associated with the access token.
    """


class AssociatedUser(BaseModel):
    """Shopify staff user associated with an online token."""

    id: int
    """
    The user id.

    [Can be associated with the `sub` of a session token](https://shopify.dev/apps/auth/oauth/session-tokens#payload)
    """

    first_name: str
    """
    The user's first name.
    """

    last_name: str
    """
    The user's last name.
    """

    email: str
    """
    The user's email.
    """

    email_verified: bool = False
    """
    If the user's email has been verified.

    If `False` email cannot be trusted (legacy accounts).
    """

    account_owner: bool
    """
    Whether the user is the owner of the Shopify account.
    """

    locale: str
    """
    The user's preferred locale. Locale values use the format `language` or `language-COUNTRY`, where `language` is a two-letter language code, and `COUNTRY` is a two-letter country code. For example: `en` or `en-US`.
    """

    collaborator: bool
    """
    If the user is a partner who collaborates with the merchant.
    """


class OnlineTokenModel(BaseModel):
    """[Read more about Online access](https://shopify.dev/apps/auth/oauth/access-modes#online-access)."""

    access_token: str
    """An API access token that can be used to access the shop's data until it expires or the associated user logs out."""

    scope: Annotated[List[str], BeforeValidator(parse_scope)]
    """The list of access scopes that were requested. Inspect `associated_user_scope` to see which were granted."""

    expires_in: int
    """The number of seconds until this session (and `access_token`) expire."""

    associated_user_scope: Annotated[List[str], BeforeValidator(parse_scope)]
    """The list of access scopes that were both requested and available to this user."""

    associated_user: AssociatedUser
    """The Shopify user associated with this token."""

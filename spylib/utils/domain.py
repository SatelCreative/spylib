from re import search


def domain_to_storename(domain: str) -> str:
    result = search(r'(https:\/\/)?([^.]+)\.myshopify\.com[\/]?', domain)
    if result:
        return result.group(2)

    raise ValueError(f'{domain} is not a shopify domain')


def store_domain(shop: str) -> str:
    """Very flexible conversion of a shop's subdomain or complete or incomplete url into a
    complete url"""
    result = search(r'^(https:\/\/)?([a-z1-9\-]+)(\.myshopify\.com[\/]?)?$', shop.lower())
    if not result:
        raise ValueError(f'{shop} is not a shopify shop')

    domain = result.group(3) or '.myshopify.com'
    storename = result.group(2)

    return f'{storename}{domain}'

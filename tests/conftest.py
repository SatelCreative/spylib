from pathlib import Path

TO_IGNORE = 'tests/fastapi_extensions'


def fastapi_installed() -> bool:
    try:
        from fastapi import FastAPI  # noqa: F401

        return True
    except ImportError:
        return False


def pytest_ignore_collect(path, config):
    """Ignore the fastapi tests if fastapi is not installed.

    pytest collection hook: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_ignore_collect
    """
    if not fastapi_installed():
        here = Path.cwd().absolute()
        skip_fd = here / TO_IGNORE
        print(skip_fd)
        if skip_fd == path:
            return True

from pytest import importorskip


def skip_tests(module: str):
    importorskip(
        modname=module, reason=f'{module} is not installed, run `pip install {module}==<version>`'
    )

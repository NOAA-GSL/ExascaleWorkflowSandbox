import pytest


def pytest_addoption(parser):
    parser.addoption("--config", action="store")
    parser.addoption("--platform", action="store")


@pytest.fixture(scope="session")
def config_file(request):
    config_value = request.config.option.config
    if config_value is None:
        pytest.skip()
    return config_value


@pytest.fixture(scope="session")
def platform(request):
    platform_value = request.config.option.platform
    if platform_value is None:
        pytest.skip()
    return platform_value

import pytest

def pytest_addoption(parser):
    parser.addoption("--config", action="store")

@pytest.fixture(scope='session')
def config_file(request):
    config_value = request.config.option.config
    if config_value is None:
        pytest.skip()
    return config_value

import parsl
import pytest

import chiltepin.configure
import chiltepin.data as data
import chiltepin.endpoint as endpoint


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    # Log in
    endpoint.login()

    # Load the default resource configuration
    resources = chiltepin.configure.load({})

    # Run the tests with the loaded resources
    with parsl.load(resources):
        yield


def test_data_transfer(config):
    transfer_future = data.transfer_task(
        "chiltepin-test-mercury",
        "chiltepin-test-ursa",
        "1MB.from_mercury",
        "1MB.to_ursa",
        timeout=120,
        polling_interval=10,
        executor=["local"],
    )
    completed = transfer_future.result()

    assert completed is True


def test_data_delete(config):
    delete_future = data.delete_task(
        "chiltepin-test-ursa",
        "1MB.to_ursa",
        timeout=120,
        polling_interval=10,
        executor=["local"],
    )
    completed = delete_future.result()

    assert completed is True

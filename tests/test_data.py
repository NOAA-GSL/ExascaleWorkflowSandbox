import logging
import pathlib

import parsl
import pytest

import chiltepin.configure
import chiltepin.data as data
import chiltepin.endpoint as endpoint


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Create directory for test output
    output_dir = pwd / "test_output"
    output_dir.mkdir(exist_ok=True)

    # Make sure we are logged in
    if endpoint.login_required():
        raise RuntimeError("Chiltepin login is required")

    # Get transfer client
    clients = endpoint.login()
    transfer_client = clients["transfer"]

    # Set Parsl logging to DEBUG and redirect to a file in the output directory
    logger_handler = parsl.set_file_logger(
        filename=str(output_dir / "test_data_parsl.log"),
        level=logging.DEBUG,
    )

    # Load the default resource configuration
    resources = chiltepin.configure.load({})

    # Load the resources in Parsl
    dfk = parsl.load(resources)

    # Run the tests with the loaded resources
    yield {"client": transfer_client}

    dfk.cleanup()
    dfk = None
    parsl.clear()
    logger_handler()


def test_data_transfer(config):
    transfer_future = data.transfer_task(
        "chiltepin-test-mercury",
        "chiltepin-test-ursa",
        "1MB.from_mercury",
        "1MB.to_ursa",
        timeout=120,
        polling_interval=10,
        executor=["local"],
        client=config["client"],
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
        client=config["client"],
    )
    completed = delete_future.result()

    assert completed is True

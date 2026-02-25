import logging
import pathlib
from unittest import mock

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
    resources = chiltepin.configure.load(
        {}, run_dir=str(output_dir / "test_data_runinfo")
    )

    # Load the resources in Parsl
    dfk = parsl.load(resources)

    # Run the tests with the loaded resources
    yield {"client": transfer_client}

    dfk.cleanup()
    dfk = None
    parsl.clear()
    logger_handler()


def test_data_transfer_task(config):
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


def test_data_delete_task(config):
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


def test_data_transfer(config):
    completed = data.transfer(
        "chiltepin-test-mercury",
        "chiltepin-test-ursa",
        "1MB.from_mercury",
        "1MB.to_ursa",
        timeout=120,
        polling_interval=10,
    )
    assert completed is True


def test_data_delete(config):
    completed = data.delete(
        "chiltepin-test-ursa",
        "1MB.to_ursa",
        timeout=120,
        polling_interval=10,
    )
    assert completed is True


def test_data_transfer_with_bad_src_ep(config):
    with pytest.raises(
        RuntimeError, match="Source endpoint 'does-not-exist' could not be found"
    ):
        data.transfer(
            "does-not-exist",
            "chiltepin-test-ursa",
            "1MB.from_mercury",
            "1MB.to_ursa",
            timeout=120,
            polling_interval=10,
            client=config["client"],
        )


def test_data_transfer_with_bad_dst_ep(config):
    with pytest.raises(
        RuntimeError, match="Destination endpoint 'does-not-exist' could not be found"
    ):
        data.transfer(
            "chiltepin-test-ursa",
            "does-not-exist",
            "1MB.from_mercury",
            "1MB.to_ursa",
            timeout=120,
            polling_interval=10,
            client=config["client"],
        )


def test_data_delete_with_bad_ep(config):
    with pytest.raises(
        RuntimeError, match="Source endpoint 'does-not-exist' could not be found"
    ):
        data.delete(
            "does-not-exist",
            "1MB.to_ursa",
            timeout=120,
            polling_interval=10,
            client=config["client"],
        )


class MockTransferAPIError(Exception):
    """Mock exception that mimics globus_sdk.TransferAPIError structure."""

    def __init__(self, consent_required=False, message="API Error"):
        super().__init__(message)
        self.info = mock.Mock()
        self.info.consent_required = consent_required
        self.message = message


def test_data_transfer_consent_required_error(config):
    """Test that transfer properly handles TransferAPIError with consent_required."""
    # Create a mock TransferAPIError with consent_required=True
    mock_error = MockTransferAPIError(consent_required=True)

    def raise_consent_error(*args, **kwargs):
        raise mock_error

    # Patch both the submit_transfer method AND the exception class being caught
    with mock.patch("globus_sdk.TransferAPIError", MockTransferAPIError):
        with mock.patch.object(
            config["client"], "submit_transfer", side_effect=raise_consent_error
        ):
            with pytest.raises(
                RuntimeError, match="Encountered a ConsentRequired error"
            ):
                data.transfer(
                    "chiltepin-test-ursa",
                    "chiltepin-test-mercury",
                    "test.txt",
                    "test.txt",
                    timeout=120,
                    polling_interval=10,
                    client=config["client"],
                )


def test_data_transfer_other_api_error(config):
    """Test that transfer properly handles TransferAPIError without consent_required."""
    # Create a mock TransferAPIError with consent_required=False
    mock_error = MockTransferAPIError(
        consent_required=False, message="Generic transfer API error"
    )

    def raise_api_error(*args, **kwargs):
        raise mock_error

    # Patch both the submit_transfer method AND the exception class being caught
    with mock.patch("globus_sdk.TransferAPIError", MockTransferAPIError):
        with mock.patch.object(
            config["client"], "submit_transfer", side_effect=raise_api_error
        ):
            with pytest.raises(RuntimeError):
                data.transfer(
                    "chiltepin-test-ursa",
                    "chiltepin-test-mercury",
                    "test.txt",
                    "test.txt",
                    timeout=120,
                    polling_interval=10,
                    client=config["client"],
                )


def test_data_delete_consent_required_error(config):
    """Test that delete properly handles TransferAPIError with consent_required."""
    # Create a mock TransferAPIError with consent_required=True
    mock_error = MockTransferAPIError(consent_required=True)

    def raise_consent_error(*args, **kwargs):
        raise mock_error

    # Patch both the submit_delete method AND the exception class being caught
    with mock.patch("globus_sdk.TransferAPIError", MockTransferAPIError):
        with mock.patch.object(
            config["client"], "submit_delete", side_effect=raise_consent_error
        ):
            with pytest.raises(
                RuntimeError, match="Encountered a ConsentRequired error"
            ):
                data.delete(
                    "chiltepin-test-ursa",
                    "test.txt",
                    timeout=120,
                    polling_interval=10,
                    client=config["client"],
                )


def test_data_delete_other_api_error(config):
    """Test that delete properly handles TransferAPIError without consent_required."""
    # Create a mock TransferAPIError with consent_required=False
    mock_error = MockTransferAPIError(
        consent_required=False, message="Generic delete API error"
    )

    def raise_api_error(*args, **kwargs):
        raise mock_error

    # Patch both the submit_delete method AND the exception class being caught
    with mock.patch("globus_sdk.TransferAPIError", MockTransferAPIError):
        with mock.patch.object(
            config["client"], "submit_delete", side_effect=raise_api_error
        ):
            with pytest.raises(RuntimeError):
                data.delete(
                    "chiltepin-test-ursa",
                    "test.txt",
                    timeout=120,
                    polling_interval=10,
                    client=config["client"],
                )

# SPDX-License-Identifier: Apache-2.0

import logging
import pathlib
import uuid
from unittest import mock

import pytest

import chiltepin.data as data
import chiltepin.endpoint as endpoint
from chiltepin import run_workflow


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file):
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

    # Generate unique destination filename to avoid conflicts in concurrent tests
    unique_dst = f"1MB.to_ursa.{uuid.uuid4()}"

    # Use workflow context manager with default (empty) resource configuration
    with run_workflow(
        {},
        run_dir=str(output_dir / "test_data_runinfo"),
        log_file=str(output_dir / "test_data_parsl.log"),
        log_level=logging.DEBUG,
    ):
        # Run the tests with the loaded resources
        yield {"client": transfer_client, "unique_dst": unique_dst}


def test_data_task_basic(config):
    """Test basic transfer_task and delete_task functionality."""
    # Transfer a file
    transfer_future = data.transfer_task(
        "chiltepin-test-mercury",
        "chiltepin-test-ursa",
        "1MB.from_mercury",
        config["unique_dst"],
        timeout=120,
        polling_interval=10,
        executor=["local"],
        client=config["client"],
    )
    transfer_completed = transfer_future.result()
    assert transfer_completed is True

    # Delete the transferred file
    delete_future = data.delete_task(
        "chiltepin-test-ursa",
        config["unique_dst"],
        timeout=120,
        polling_interval=10,
        executor=["local"],
        client=config["client"],
    )
    delete_completed = delete_future.result()
    assert delete_completed is True


def test_data_sync_basic(config):
    """Test basic synchronous transfer and delete functionality."""
    # Transfer a file (synchronous)
    transfer_completed = data.transfer(
        "chiltepin-test-mercury",
        "chiltepin-test-ursa",
        "1MB.from_mercury",
        config["unique_dst"],
        timeout=120,
        polling_interval=10,
    )
    assert transfer_completed is True

    # Delete the transferred file (synchronous)
    delete_completed = data.delete(
        "chiltepin-test-ursa",
        config["unique_dst"],
        timeout=120,
        polling_interval=10,
    )
    assert delete_completed is True


def test_data_transfer_with_bad_src_ep(config):
    with pytest.raises(
        RuntimeError, match="Source endpoint 'does-not-exist' could not be found"
    ):
        data.transfer(
            "does-not-exist",
            "chiltepin-test-ursa",
            "1MB.from_mercury",
            config["unique_dst"],
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
            config["unique_dst"],
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
            config["unique_dst"],
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

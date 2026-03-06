# SPDX-License-Identifier: Apache-2.0

import logging
import pathlib
import uuid
from unittest import mock

import parsl
import pytest

import chiltepin.configure
import chiltepin.data as data
import chiltepin.endpoint as endpoint


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

    # Generate unique destination filename to avoid conflicts in concurrent tests
    unique_dst = f"1MB.to_ursa.{uuid.uuid4()}"

    # Run the tests with the loaded resources
    yield {"client": transfer_client, "unique_dst": unique_dst}

    dfk.cleanup()
    dfk = None
    parsl.clear()
    logger_handler()


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


def test_data_transfer_task_comprehensive(config):
    """Test transfer_task dependency ordering with inputs parameter."""
    import time

    from chiltepin.tasks import python_task

    @python_task
    def slow_task():
        """Task that takes 60 seconds (3x typical transfer time)."""
        import time

        time.sleep(60)
        return "completed"

    start_time = time.time()
    slow = slow_task(executor=["local"])
    dst = f"dependency_test_{uuid.uuid4()}.txt"
    transfer_future = data.transfer_task(
        "chiltepin-test-mercury",
        "chiltepin-test-ursa",
        "1MB.from_mercury",
        dst,
        timeout=120,
        polling_interval=10,
        executor=["local"],
        client=config["client"],
        inputs=[slow],
    )

    slow_result = slow.result()
    transfer_result = transfer_future.result()
    total_time = time.time() - start_time

    assert slow_result == "completed"
    assert transfer_result is True
    assert total_time >= 60.0, (
        f"Completed in {total_time:.1f}s, dependency may not have been respected (expected ≥60s)"
    )

    # Cleanup
    data.delete_task(
        "chiltepin-test-ursa",
        dst,
        timeout=120,
        polling_interval=10,
        executor=["local"],
        client=config["client"],
    ).result()


def test_data_delete_task_with_dependencies(config):
    """Test delete_task dependency ordering with inputs parameter."""
    import time

    from chiltepin.tasks import python_task

    # Transfer a file to delete
    dst = f"delete_test_{uuid.uuid4()}.txt"
    transfer_future = data.transfer_task(
        "chiltepin-test-mercury",
        "chiltepin-test-ursa",
        "1MB.from_mercury",
        dst,
        timeout=120,
        polling_interval=10,
        executor=["local"],
        client=config["client"],
    )
    transfer_future.result()

    @python_task
    def slow_processing():
        """Simulate processing that takes 60 seconds (3x typical transfer time)."""
        import time

        time.sleep(60)
        return "processed"

    start_time = time.time()
    process = slow_processing(executor=["local"])
    delete_future = data.delete_task(
        "chiltepin-test-ursa",
        dst,
        timeout=120,
        polling_interval=10,
        executor=["local"],
        client=config["client"],
        inputs=[process],
    )

    process_result = process.result()
    delete_result = delete_future.result()
    total_time = time.time() - start_time

    assert process_result == "processed"
    assert delete_result is True
    assert total_time >= 60.0, (
        f"Completed in {total_time:.1f}s, dependency may not have been respected (expected ≥60s)"
    )


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

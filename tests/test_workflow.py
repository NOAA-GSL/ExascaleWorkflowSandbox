# SPDX-License-Identifier: Apache-2.0

"""Tests for chiltepin.workflow module.

This test suite validates that workflow context managers work correctly
for managing Parsl lifecycle without requiring users to directly interact
with Parsl.
"""

import pathlib
from unittest import mock

import parsl
import pytest
import yaml

import chiltepin.configure
from chiltepin import workflow, workflow_from_dict, workflow_from_file
from chiltepin.tasks import python_task


# Helper function to add PYTHONPATH to config
def add_pythonpath_to_config(config_dict, resource_name):
    """Add project root to PYTHONPATH for a specific resource."""
    project_root = pathlib.Path(__file__).parent.parent.resolve()
    if resource_name in config_dict:
        env = config_dict[resource_name].get("environment", [])
        # Make a copy to avoid modifying shared references
        env = env.copy() if env else []
        env.append(f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}")
        config_dict[resource_name]["environment"] = env
    return config_dict


# Cleanup any existing Parsl state before tests
@pytest.fixture(scope="function", autouse=True)
def cleanup_parsl():
    """Ensure Parsl is cleaned up before and after each test."""
    # Cleanup before test
    try:
        dfk = parsl.dfk()
        if dfk:
            dfk.cleanup()
            parsl.clear()
    except Exception:
        pass  # No DFK loaded, which is fine

    yield

    # Cleanup after test
    try:
        dfk = parsl.dfk()
        if dfk:
            dfk.cleanup()
            parsl.clear()
    except Exception:
        pass


class TestWorkflowContextManager:
    """Test workflow() context manager with different configurations."""

    def test_workflow_with_dict_config(self, tmp_path):
        """Test workflow context manager with a dictionary config."""

        @python_task
        def add_numbers(a, b):
            """Simple task for testing."""
            return a + b

        @python_task
        def multiply(x, y):
            """Another simple task for testing."""
            return x * y

        # Get project root for PYTHONPATH
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-executor": {
                "provider": "localhost",
                "cores_per_node": 2,
                "max_workers_per_node": 2,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        with workflow(config, run_dir=str(tmp_path / "runinfo1")):
            # Submit tasks
            future1 = add_numbers(10, 32, executor=["test-executor"])
            future2 = multiply(6, 7, executor=["test-executor"])

            # Get results
            result1 = future1.result()
            result2 = future2.result()

            assert result1 == 42
            assert result2 == 42

    def test_workflow_with_file_config(self, config_file, tmp_path):
        """Test workflow context manager with a YAML config file."""

        @python_task
        def greet(name):
            """Task that returns a greeting."""
            return f"Hello, {name}!"

        # Load config from file and add PYTHONPATH dynamically
        config_dict = chiltepin.configure.parse_file(config_file)
        add_pythonpath_to_config(config_dict, "service")

        # Write modified config to temp file
        temp_config_file = tmp_path / "temp_config.yaml"
        with open(temp_config_file, "w") as f:
            yaml.dump(config_dict, f)

        # Test with file path argument
        with workflow(
            str(temp_config_file),
            include=["service"],
            run_dir=str(tmp_path / "runinfo2"),
        ):
            future = greet("Workflow", executor=["service"])
            result = future.result()
            assert result == "Hello, Workflow!"


class TestWorkflowAliases:
    """Test workflow_from_dict and workflow_from_file convenience aliases."""

    def test_workflow_from_dict(self, tmp_path):
        """Test workflow_from_dict convenience function."""

        @python_task
        def add_numbers(a, b):
            return a + b

        # Get project root for PYTHONPATH
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "my-executor": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        with workflow_from_dict(config, run_dir=str(tmp_path / "runinfo5")):
            future = add_numbers(100, 200, executor=["my-executor"])
            result = future.result()
            assert result == 300

    def test_workflow_from_file(self, config_file, tmp_path):
        """Test workflow_from_file convenience function."""

        @python_task
        def multiply(x, y):
            return x * y

        # Load config from file and add PYTHONPATH dynamically
        config_dict = chiltepin.configure.parse_file(config_file)
        add_pythonpath_to_config(config_dict, "service")

        # Write modified config to temp file
        temp_config_file = tmp_path / "temp_config.yaml"
        with open(temp_config_file, "w") as f:
            yaml.dump(config_dict, f)

        # Test with file path argument using workflow_from_file
        with workflow_from_file(
            str(temp_config_file),
            include=["service"],
            run_dir=str(tmp_path / "runinfo6"),
        ):
            future = multiply(21, 2, executor=["service"])
            result = future.result()
            assert result == 42


class TestWorkflowCleanup:
    """Test that workflow context managers properly cleanup resources."""

    def test_sequential_workflows(self, tmp_path):
        """Test that multiple workflows can be created sequentially."""

        @python_task
        def add_numbers(a, b):
            return a + b

        @python_task
        def multiply(x, y):
            return x * y

        # Get project root for PYTHONPATH
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config1 = {
            "exec1": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        config2 = {
            "exec2": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # First workflow
        with workflow(config1, run_dir=str(tmp_path / "runinfo7")):
            future = add_numbers(1, 2, executor=["exec1"])
            assert future.result() == 3

        # Second workflow should work without conflicts
        with workflow(config2, run_dir=str(tmp_path / "runinfo8")):
            future = multiply(3, 4, executor=["exec2"])
            assert future.result() == 12

    def test_workflow_cleanup_on_exception(self, tmp_path):
        """Test that workflow cleans up even if an exception occurs."""

        @python_task
        def add_numbers(a, b):
            return a + b

        # Get project root for PYTHONPATH
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Workflow should cleanup even if exception occurs
        with pytest.raises(ValueError):
            with workflow(config, run_dir=str(tmp_path / "runinfo9")):
                future = add_numbers(5, 5, executor=["test-exec"])
                result = future.result()
                assert result == 10
                raise ValueError("Intentional test error")

        # Should be able to create another workflow after exception
        with workflow(config, run_dir=str(tmp_path / "runinfo10")):
            future = add_numbers(7, 8, executor=["test-exec"])
            assert future.result() == 15


class TestWorkflowExceptionHandling:
    """Test exception handling during workflow cleanup."""

    def test_dfk_cleanup_exception(self, tmp_path):
        """Test that exceptions during dfk.cleanup() are properly raised."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Store reference to real cleanup for later
        real_cleanup = parsl.DataFlowKernel.cleanup
        dfk_ref = None

        with mock.patch("parsl.DataFlowKernel.cleanup") as mock_cleanup:
            mock_cleanup.side_effect = RuntimeError("Cleanup failed")

            with pytest.raises(RuntimeError, match="Cleanup failed"):
                with workflow(config, run_dir=str(tmp_path / "runinfo_exc1")):
                    dfk_ref = parsl.dfk()  # Capture dfk reference
                    pass

        # Actually clean up the DFK now that we're done testing
        if dfk_ref:
            try:
                real_cleanup(dfk_ref)
                parsl.clear()
            except Exception:
                pass

    def test_parsl_clear_exception(self, tmp_path):
        """Test that exceptions during parsl.clear() are properly raised."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        with mock.patch("parsl.clear") as mock_clear:
            mock_clear.side_effect = RuntimeError("Clear failed")

            with pytest.raises(RuntimeError, match="Clear failed"):
                with workflow(config, run_dir=str(tmp_path / "runinfo_exc2")):
                    pass

    def test_logger_handler_exception(self, tmp_path):
        """Test that exceptions during logger_handler() are properly raised.

        Note: Logger cleanup happens both inside dfk.cleanup() and in our explicit
        logger_handler() call. When it fails during dfk.cleanup(), that exception
        is what gets raised.
        """
        # Ensure clean state before test
        try:
            parsl.clear()
        except Exception:
            pass

        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Mock the logger handler to raise an exception
        def mock_set_file_logger(*args, **kwargs):
            def failing_handler():
                raise RuntimeError("Logger cleanup failed")

            return failing_handler

        with mock.patch("parsl.set_file_logger", side_effect=mock_set_file_logger):
            # The logger cleanup exception will be raised (either from dfk.cleanup or our call)
            with pytest.raises(RuntimeError):
                with workflow(
                    config,
                    run_dir=str(tmp_path / "runinfo_exc3"),
                    log_file=str(tmp_path / "test.log"),
                ):
                    pass

    def test_chained_exceptions_cleanup_then_clear(self, tmp_path):
        """Test exception chaining when dfk.cleanup() and parsl.clear() both fail."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Store reference to real cleanup for later
        real_cleanup = parsl.DataFlowKernel.cleanup
        dfk_ref = None

        with mock.patch("parsl.DataFlowKernel.cleanup") as mock_cleanup:
            with mock.patch("parsl.clear") as mock_clear:
                mock_cleanup.side_effect = RuntimeError("Cleanup failed")
                mock_clear.side_effect = RuntimeError("Clear failed")

                with pytest.raises(RuntimeError) as exc_info:
                    with workflow(config, run_dir=str(tmp_path / "runinfo_exc4")):
                        dfk_ref = parsl.dfk()  # Capture dfk reference
                        pass

                # The last exception (clear) should be raised
                assert "Clear failed" in str(exc_info.value)
                # And the previous exception (cleanup) should be in the chain
                assert exc_info.value.__context__ is not None
                assert "Cleanup failed" in str(exc_info.value.__context__)

        # Actually clean up the DFK now that we're done testing
        if dfk_ref:
            try:
                real_cleanup(dfk_ref)
                parsl.clear()
            except Exception:
                pass

    def test_chained_exceptions_all_three(self, tmp_path):
        """Test exception chaining when all three cleanup operations fail."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Store reference to real cleanup for later
        real_cleanup = parsl.DataFlowKernel.cleanup
        dfk_ref = None

        # Mock the logger handler to raise an exception
        def mock_set_file_logger(*args, **kwargs):
            def failing_handler():
                raise RuntimeError("Logger cleanup failed")

            return failing_handler

        with mock.patch("parsl.DataFlowKernel.cleanup") as mock_cleanup:
            with mock.patch("parsl.clear") as mock_clear:
                with mock.patch(
                    "parsl.set_file_logger", side_effect=mock_set_file_logger
                ):
                    mock_cleanup.side_effect = RuntimeError("Cleanup failed")
                    mock_clear.side_effect = RuntimeError("Clear failed")

                    with pytest.raises(RuntimeError) as exc_info:
                        with workflow(
                            config,
                            run_dir=str(tmp_path / "runinfo_exc5"),
                            log_file=str(tmp_path / "test.log"),
                        ):
                            dfk_ref = parsl.dfk()  # Capture dfk reference
                            pass

                    # The last exception (logger) should be raised
                    assert "Logger cleanup failed" in str(exc_info.value)
                    # Check the exception chain
                    assert exc_info.value.__context__ is not None
                    assert "Clear failed" in str(exc_info.value.__context__)
                    assert exc_info.value.__context__.__context__ is not None
                    assert "Cleanup failed" in str(
                        exc_info.value.__context__.__context__
                    )

        # Actually clean up the DFK now that we're done testing
        if dfk_ref:
            try:
                real_cleanup(dfk_ref)
                parsl.clear()
            except Exception:
                pass

    def test_parsl_clear_called_when_dfk_is_none(self, tmp_path):
        """Test that parsl.clear() is called even when dfk is None."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Mock parsl.load to fail, so dfk stays None
        with mock.patch("parsl.load") as mock_load:
            with mock.patch("parsl.clear") as mock_clear:
                mock_load.side_effect = RuntimeError("Load failed")

                with pytest.raises(RuntimeError, match="Load failed"):
                    with workflow(config, run_dir=str(tmp_path / "runinfo_exc6")):
                        pass

                # parsl.clear() should still be called even though dfk is None
                mock_clear.assert_called_once()

    def test_parsl_clear_exception_without_cleanup_exception(self, tmp_path):
        """Test parsl.clear() exception when dfk.cleanup() succeeds."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # This tests the branch where parsl.clear() fails but dfk.cleanup() succeeds
        # Explicitly ensure dfk.cleanup() succeeds so cleanup_exception stays None
        original_clear = parsl.clear
        dfk_ref = None

        def mock_cleanup_success(self):
            """Mock dfk.cleanup() to succeed without doing anything."""
            # Don't actually clean up - we'll do it manually after

        call_count = [0]

        def mock_clear_selective():
            call_count[0] += 1
            if call_count[0] == 2:
                # Second call (from workflow) - make it fail
                raise RuntimeError("Clear failed")
            else:
                # First and subsequent calls should succeed
                try:
                    original_clear()
                except Exception:
                    pass

        with mock.patch.object(parsl.DataFlowKernel, "cleanup", mock_cleanup_success):
            with mock.patch("parsl.clear", side_effect=mock_clear_selective):
                # Explicitly make the first call to parsl.clear() to "use up" count==1
                try:
                    parsl.clear()
                except Exception:
                    pass

                # Now the workflow's call will be count==2 and will raise
                with pytest.raises(RuntimeError, match="Clear failed"):
                    with workflow(config, run_dir=str(tmp_path / "runinfo_exc7")):
                        dfk_ref = parsl.dfk()  # Capture for manual cleanup
                        pass

        # Manually clean up since we mocked cleanup
        if dfk_ref:
            try:
                parsl.DataFlowKernel.cleanup(dfk_ref)
                parsl.clear()
            except Exception:
                pass


@pytest.fixture
def config_file_fixture(tmp_path):
    """Create a temporary config file for testing file-based workflows."""
    import yaml

    project_root = pathlib.Path(__file__).parent.parent.resolve()

    config = {
        "service": {
            "provider": "localhost",
            "cores_per_node": 1,
            "max_workers_per_node": 1,
            "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
        }
    }

    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    return str(config_file)


class TestWorkflowFromFileCoverage:
    """Tests specifically for workflow_from_file function coverage."""

    def test_workflow_from_file_with_local_fixture(self, config_file_fixture, tmp_path):
        """Test workflow_from_file with a local config file fixture."""

        @python_task
        def simple_task():
            return "success"

        with workflow_from_file(
            config_file_fixture,
            include=["service"],
            run_dir=str(tmp_path / "runinfo_file"),
        ):
            future = simple_task(executor=["service"])
            result = future.result()
            assert result == "success"


class TestUserExceptionPrecedence:
    """Test that user exceptions are not masked by cleanup exceptions."""

    def test_user_exception_not_masked_by_cleanup_exception(self, tmp_path, caplog):
        """Test that user exceptions take precedence over cleanup exceptions."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Store reference to real cleanup for later
        real_cleanup = parsl.DataFlowKernel.cleanup
        dfk_ref = None

        # Mock dfk.cleanup to fail
        with mock.patch("parsl.DataFlowKernel.cleanup") as mock_cleanup:
            mock_cleanup.side_effect = RuntimeError("Cleanup failed")

            # User exception should be raised, not cleanup exception
            with pytest.raises(ValueError, match="User error"):
                with workflow(config, run_dir=str(tmp_path / "runinfo_user1")):
                    dfk_ref = parsl.dfk()  # Capture dfk reference
                    raise ValueError("User error")

            # Cleanup exception should be logged as a warning
            assert any(
                "Exception during dfk.cleanup() while handling user exception"
                in record.message
                for record in caplog.records
            )

        # Actually clean up the DFK now that we're done testing
        if dfk_ref:
            try:
                real_cleanup(dfk_ref)
                parsl.clear()
            except Exception:
                pass

    def test_all_cleanup_operations_attempted(self, tmp_path, caplog):
        """Test that all cleanup operations are attempted even when some fail."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Store reference to real cleanup for later
        real_cleanup = parsl.DataFlowKernel.cleanup
        dfk_ref = None

        # Mock dfk.cleanup and parsl.clear to fail
        original_clear = parsl.clear
        call_count = [0]

        def mock_clear_selective():
            call_count[0] += 1
            # Fail on first call (our explicit call after dfk.cleanup fails)
            if call_count[0] == 1:
                raise RuntimeError("Clear failed")
            else:
                # Subsequent calls use original
                original_clear()

        with mock.patch("parsl.DataFlowKernel.cleanup") as mock_cleanup:
            with mock.patch("parsl.clear", side_effect=mock_clear_selective):
                mock_cleanup.side_effect = RuntimeError("Cleanup failed")

                # User exception should be raised, not any cleanup exception
                with pytest.raises(ValueError, match="User error"):
                    with workflow(config, run_dir=str(tmp_path / "runinfo_user2")):
                        dfk_ref = parsl.dfk()  # Capture dfk reference
                        raise ValueError("User error")

                # Both cleanup exceptions should be logged as warnings
                assert any(
                    "Exception during dfk.cleanup() while handling user exception"
                    in record.message
                    for record in caplog.records
                )
                assert any(
                    "Exception during parsl.clear() while handling user exception"
                    in record.message
                    for record in caplog.records
                )

        # Actually clean up the DFK now that we're done testing
        if dfk_ref:
            try:
                real_cleanup(dfk_ref)
                parsl.clear()
            except Exception:
                pass

    def test_cleanup_exception_raised_when_no_user_exception(self, tmp_path):
        """Test that cleanup exceptions are raised when there's no user exception."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Store reference to real cleanup for later
        real_cleanup = parsl.DataFlowKernel.cleanup
        dfk_ref = None

        # Mock dfk.cleanup to fail
        with mock.patch("parsl.DataFlowKernel.cleanup") as mock_cleanup:
            mock_cleanup.side_effect = RuntimeError("Cleanup failed")

            # Cleanup exception should be raised when there's no user exception
            with pytest.raises(RuntimeError, match="Cleanup failed"):
                with workflow(config, run_dir=str(tmp_path / "runinfo_user3")):
                    dfk_ref = parsl.dfk()  # Capture dfk reference
                    pass  # No user exception

        # Actually clean up the DFK now that we're done testing
        if dfk_ref:
            try:
                real_cleanup(dfk_ref)
                parsl.clear()
            except Exception:
                pass

    def test_user_exception_with_logger_cleanup_failure(self, tmp_path, caplog):
        """Test that user exceptions take precedence when logger cleanup fails."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        # Mock the logger handler to raise an exception
        def mock_set_file_logger(*args, **kwargs):
            def failing_handler():
                raise RuntimeError("Logger cleanup failed")

            return failing_handler

        with mock.patch("parsl.set_file_logger", side_effect=mock_set_file_logger):
            # User exception should be raised, not logger cleanup exception
            with pytest.raises(ValueError, match="User error"):
                with workflow(
                    config,
                    run_dir=str(tmp_path / "runinfo_user4"),
                    log_file=str(tmp_path / "test.log"),
                ):
                    raise ValueError("User error")

            # Logger cleanup exception should be logged as a warning
            assert any(
                "Exception during logger cleanup while handling user exception"
                in record.message
                for record in caplog.records
            )

    def test_logger_handler_exception_standalone(self, tmp_path):
        """Test logger cleanup failure when dfk.cleanup and parsl.clear succeed."""
        project_root = pathlib.Path(__file__).parent.parent.resolve()

        config = {
            "test-exec": {
                "provider": "localhost",
                "cores_per_node": 1,
                "max_workers_per_node": 1,
                "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
            }
        }

        #  Create a handler that succeeds first time (dfk cleanup) but fails second time (our explicit call)
        call_count = [0]

        def mock_set_file_logger(*args, **kwargs):
            def conditional_failing_handler():
                call_count[0] += 1
                if call_count[0] == 2:  # Fail on second call (our explicit cleanup)
                    raise RuntimeError("Logger cleanup failed")

            return conditional_failing_handler

        with mock.patch("parsl.set_file_logger", side_effect=mock_set_file_logger):
            # Logger cleanup exception should be raised
            with pytest.raises(RuntimeError, match="Logger cleanup failed"):
                with workflow(
                    config,
                    run_dir=str(tmp_path / "runinfo_logger_standalone"),
                    log_file=str(tmp_path / "test.log"),
                ):
                    pass

# SPDX-License-Identifier: Apache-2.0

"""Tests for chiltepin.workflow module.

This test suite validates that workflow context managers work correctly
for managing Parsl lifecycle without requiring users to directly interact
with Parsl.
"""

import pathlib

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

# SPDX-License-Identifier: Apache-2.0

"""Tests for chiltepin.tasks module.

This test suite validates that task decorators work correctly for both
standalone functions and class methods under Parsl execution.
"""

import logging
import pathlib
import tempfile
from typing import List

import parsl
import pytest

from chiltepin import workflow
from chiltepin.tasks import bash_task, join_task, python_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def parsl_config():
    """Initialize Parsl with a local configuration for testing."""
    pwd = pathlib.Path(__file__).parent.resolve()

    # Create directory for test output
    output_dir = pwd / "test_output"
    output_dir.mkdir(exist_ok=True)

    # Configure local executor with PYTHONPATH that includes the project root
    # This allows Parsl workers to import test modules
    project_root = pwd.parent.resolve()
    local_config = {
        "test-local": {
            "provider": "localhost",
            "cores_per_node": 2,
            "max_workers_per_node": 2,
            "environment": [f"export PYTHONPATH=${{PYTHONPATH}}:{project_root}"],
        }
    }

    # Use workflow context manager for Parsl lifecycle
    with workflow(
        local_config,
        run_dir=str(output_dir / "test_tasks_runinfo"),
        log_file=str(output_dir / "test_tasks_parsl.log"),
        log_level=logging.DEBUG,
    ):
        yield


# ===== Python Task Tests - Standalone Functions =====


class TestPythonTaskStandalone:
    """Test python_task decorator with standalone functions."""

    def test_python_task_simple(self, parsl_config):
        """Test simple python_task function."""

        @python_task
        def hello_world():
            return "Hello, World!"

        future = hello_world(executor=["test-local"])
        result = future.result()
        assert result == "Hello, World!"

    def test_python_task_with_args(self, parsl_config):
        """Test python_task with positional arguments."""

        @python_task
        def add_numbers(a, b):
            return a + b

        future = add_numbers(5, 3, executor=["test-local"])
        result = future.result()
        assert result == 8

    def test_python_task_with_kwargs(self, parsl_config):
        """Test python_task with keyword arguments."""

        @python_task
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        future = greet(name="Alice", greeting="Hi", executor=["test-local"])
        result = future.result()
        assert result == "Hi, Alice!"

    def test_python_task_executor_selection(self, parsl_config):
        """Test python_task with executor parameter."""

        @python_task
        def get_message():
            return "Executed"

        future = get_message(executor=["test-local"])
        result = future.result()
        assert result == "Executed"

    def test_python_task_filters_parsl_kwargs(self, parsl_config):
        """Test that python_task filters out Parsl-injected kwargs."""

        @python_task
        def simple_func(x):
            return x * 2

        future = simple_func(5, executor=["test-local"])
        result = future.result()
        assert result == 10

    def test_python_task_accepts_var_keyword(self, parsl_config):
        """Test python_task with function that accepts **kwargs."""

        @python_task
        def function_with_kwargs(a, **kwargs):
            return {"a": a, "extra": kwargs}

        future = function_with_kwargs(1, b=2, c=3, executor=["test-local"])
        result = future.result()
        assert result["a"] == 1
        assert result["extra"]["b"] == 2
        assert result["extra"]["c"] == 3

    def test_python_task_with_list_return(self, parsl_config):
        """Test python_task returning a list."""

        @python_task
        def get_list(n):
            return list(range(n))

        future = get_list(5, executor=["test-local"])
        result = future.result()
        assert result == [0, 1, 2, 3, 4]

    def test_python_task_with_inputs_dependency(self, parsl_config):
        """Test that python_task automatically supports inputs parameter for dependencies."""
        import time

        @python_task
        def first_task():
            import time

            # Sleep to ensure we can detect if second starts early
            time.sleep(2)
            return "first"

        @python_task
        def second_task():
            return "second"

        # Time everything in pytest process using monotonic clock
        start = time.monotonic()

        # Create first task
        first = first_task(executor=["test-local"])

        # Second task depends on first via inputs parameter (added by Parsl decorator)
        # With 2 workers, second COULD start immediately if dependency wasn't enforced
        second = second_task(executor=["test-local"], inputs=[first])

        # Wait for second to complete (which should wait for first due to inputs=[first])
        # Calling second.result() first ensures we're measuring the actual wait time
        second_result = second.result()
        elapsed = time.monotonic() - start

        # Verify dependency was enforced by checking elapsed time
        # If inputs=[first] works, second can't complete until first finishes its 2s sleep
        assert elapsed >= 2.0, (
            f"Second task completed in {elapsed:.1f}s, suggesting it didn't wait for first task (expected ≥2s)"
        )

        # Verify first also completed successfully
        first_result = first.result()
        assert first_result == "first"
        assert second_result == "second"

    def test_python_task_with_dict_return(self, parsl_config):
        """Test python_task returning a dictionary."""

        @python_task
        def get_dict(key, value):
            return {key: value}

        future = get_dict("test_key", 42, executor=["test-local"])
        result = future.result()
        assert result == {"test_key": 42}


# ===== Bash Task Tests - Standalone Functions =====


class TestBashTaskStandalone:
    """Test bash_task decorator with standalone functions."""

    def test_bash_task_simple(self, parsl_config):
        """Test simple bash_task function."""

        @bash_task
        def echo_hello():
            return "echo 'Hello from Bash'"

        future = echo_hello(executor=["test-local"])
        assert future.result() == 0

    def test_bash_task_with_args(self, parsl_config):
        """Test bash_task with arguments."""

        @bash_task
        def echo_message(message):
            return f"echo '{message}'"

        future = echo_message("Test Message", executor=["test-local"])
        assert future.result() == 0

    def test_bash_task_with_output(self, parsl_config):
        """Test bash_task with stdout capture."""

        @bash_task
        def write_to_stdout():
            return "echo 'Bash output test'"

        pwd = pathlib.Path(__file__).parent.resolve()
        output_dir = pwd / "test_output"
        stdout_file = output_dir / "bash_task_output.txt"

        future = write_to_stdout(stdout=str(stdout_file), executor=["test-local"])
        assert future.result() == 0
        assert stdout_file.exists()
        content = stdout_file.read_text().strip()
        assert "Bash output test" in content

    def test_bash_task_multiline(self, parsl_config):
        """Test bash_task with multiple commands."""

        @bash_task
        def multi_command():
            return """
            x=5
            y=10
            echo $((x + y))
            """

        future = multi_command(executor=["test-local"])
        assert future.result() == 0

    def test_bash_task_executor_selection(self, parsl_config):
        """Test bash_task with executor parameter."""

        @bash_task
        def simple_bash():
            return "echo 'test'"

        future = simple_bash(executor=["test-local"])
        assert future.result() == 0

    def test_bash_task_with_file_creation(self, parsl_config):
        """Test bash_task that creates a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name

        @bash_task
        def create_file_dynamic(filepath):
            return f"echo 'Test content' > {filepath}"

        future = create_file_dynamic(tmp_path, executor=["test-local"])

        assert future.result() == 0
        assert pathlib.Path(tmp_path).exists()

        # Cleanup
        pathlib.Path(tmp_path).unlink()


# ===== Join Task Tests - Standalone Functions =====


class TestJoinTaskStandalone:
    """Test join_task decorator with standalone functions."""

    def test_join_task_simple(self, parsl_config):
        """Test join_task that combines multiple python tasks."""

        @python_task
        def get_value(x):
            return x * 2

        @python_task
        def add_values(a, b):
            return a + b

        @join_task
        def combine_values():
            future1 = get_value(5, executor=["test-local"])
            future2 = get_value(10, executor=["test-local"])
            return add_values(future1, future2, executor=["test-local"])

        future = combine_values(executor=["test-local"])
        result = future.result()
        assert result == 30  # (5*2) + (10*2)

    def test_join_task_with_args(self, parsl_config):
        """Test join_task with arguments."""

        @python_task
        def multiply(x, factor):
            return x * factor

        @python_task
        def add_values(*values):
            return sum(values)

        @join_task
        def process_list(values: List[int], factor: int):
            futures = [multiply(v, factor, executor=["test-local"]) for v in values]
            return add_values(*futures, executor=["test-local"])

        future = process_list([1, 2, 3], 2, executor=["test-local"])
        result = future.result()
        assert result == 12  # (1*2) + (2*2) + (3*2)

    def test_join_task_mixed_tasks(self, parsl_config):
        """Test join_task combining python and bash tasks."""
        pwd = pathlib.Path(__file__).parent.resolve()
        output_dir = pwd / "test_output"
        test_file = output_dir / "join_test_file.txt"

        @bash_task
        def write_file_join(filepath):
            return f"echo 'data' > {filepath}"

        @python_task
        def count_chars(filepath):
            with open(filepath, "r") as f:
                content = f.read()
            return len(content.strip())

        @join_task
        def write_and_count(filepath):
            write_future = write_file_join(filepath, executor=["test-local"])
            write_future.result()  # Wait for file to be written
            count_future = count_chars(filepath, executor=["test-local"])
            return count_future

        future = write_and_count(str(test_file), executor=["test-local"])
        result = future.result()
        assert result == 4  # "data" has 4 characters

        # Cleanup
        if test_file.exists():
            test_file.unlink()


# ===== Python Task Tests - Class Methods =====


class TestPythonTaskClassMethods:
    """Test python_task decorator with class methods."""

    def test_python_task_class_method(self, parsl_config):
        """Test python_task as a class method."""

        class Calculator:
            def __init__(self, multiplier):
                self.multiplier = multiplier

            @python_task
            def multiply(self, x):
                return x * self.multiplier

        calc = Calculator(3)
        future = calc.multiply(7, executor=["test-local"])
        result = future.result()
        assert result == 21

    def test_python_task_class_with_state(self, parsl_config):
        """Test python_task accessing class state."""

        class Counter:
            def __init__(self, start=0):
                self.value = start

            @python_task
            def add(self, x):
                return self.value + x

        counter = Counter(10)
        future = counter.add(5, executor=["test-local"])
        result = future.result()
        assert result == 15

    def test_python_task_multiple_methods(self, parsl_config):
        """Test multiple python_task methods in a class."""

        class MathOps:
            @python_task
            def add(self, a, b):
                return a + b

            @python_task
            def subtract(self, a, b):
                return a - b

        ops = MathOps()
        add_future = ops.add(10, 5, executor=["test-local"])
        sub_future = ops.subtract(10, 5, executor=["test-local"])
        assert add_future.result() == 15
        assert sub_future.result() == 5


# ===== Bash Task Tests - Class Methods =====


class TestBashTaskClassMethods:
    """Test bash_task decorator with class methods."""

    def test_bash_task_class_method(self, parsl_config):
        """Test bash_task as a class method."""

        class BashRunner:
            def __init__(self, prefix):
                self.prefix = prefix

            @bash_task
            def echo_with_prefix(self, message):
                return f"echo '{self.prefix}: {message}'"

        runner = BashRunner("INFO")
        future = runner.echo_with_prefix("Test", executor=["test-local"])
        assert future.result() == 0

    def test_bash_task_class_with_file_ops(self, parsl_config):
        """Test bash_task class method with file operations."""

        class FileOps:
            def __init__(self, base_dir):
                self.base_dir = pathlib.Path(base_dir)

            @bash_task
            def create_file(self, filename):
                filepath = self.base_dir / filename
                return f"echo 'content' > {filepath}"

        pwd = pathlib.Path(__file__).parent.resolve()
        output_dir = pwd / "test_output"
        file_ops = FileOps(output_dir)

        future = file_ops.create_file("class_test.txt", executor=["test-local"])

        assert future.result() == 0
        assert (output_dir / "class_test.txt").exists()

        # Cleanup
        (output_dir / "class_test.txt").unlink()


# ===== Join Task Tests - Class Methods =====


class TestJoinTaskClassMethods:
    """Test join_task decorator with class methods."""

    def test_join_task_class_method(self, parsl_config):
        """Test join_task as a class method."""

        class Workflow:
            @python_task
            def task_a(self, x):
                return x + 1

            @python_task
            def task_b(self, x):
                return x * 2

            @join_task
            def pipeline(self, value):
                future_a = self.task_a(value, executor=["test-local"])
                future_b = self.task_b(future_a, executor=["test-local"])
                return future_b

        wf = Workflow()
        future = wf.pipeline(5, executor=["test-local"])
        result = future.result()
        assert result == 12  # (5 + 1) * 2

    def test_join_task_complex_workflow(self, parsl_config):
        """Test join_task orchestrating a complex workflow."""

        class DataProcessor:
            @python_task
            def load_data(self, data):
                return data

            @python_task
            def process(self, data):
                return [x * 2 for x in data]

            @python_task
            def aggregate(self, data):
                return sum(data)

            @join_task
            def run_pipeline(self, input_data):
                load_future = self.load_data(input_data, executor=["test-local"])
                process_future = self.process(load_future, executor=["test-local"])
                agg_future = self.aggregate(process_future, executor=["test-local"])
                return agg_future

        processor = DataProcessor()
        future = processor.run_pipeline([1, 2, 3, 4, 5], executor=["test-local"])
        result = future.result()
        assert result == 30  # sum([2, 4, 6, 8, 10])


# ===== Edge Cases and Special Scenarios =====


class TestTaskEdgeCases:
    """Test edge cases and special scenarios."""

    # NOTE: The following test is commented out because it raises an exception:
    #
    #   parsl.errors.NoDataFlowKernelError: Must first load config
    #
    # Also join tasks are expected to be used for this use case, so this test may not be necessary.
    # It is left here for reference and potential future use if we want to support this use case
    # with a python_task rather than a join_task.
    #
    # def test_nested_decorator_calls(self, parsl_config):
    #     """Test calling a decorated function from within another."""
    #     @python_task
    #     def inner_task(x):
    #         return x + 1

    #     @python_task
    #     def outer_task(x):
    #         return inner_task(x, executor=["test-local"])

    #     future = outer_task(5, executor=["test-local"])
    #     inner_future = future.result()
    #     final_result = inner_future.result()
    #     assert final_result == 6

    def test_task_with_exception(self, parsl_config):
        """Test that exceptions in tasks are properly propagated."""

        @python_task
        def failing_task():
            raise ValueError("Intentional error")

        future = failing_task(executor=["test-local"])
        with pytest.raises(ValueError, match="Intentional error"):
            future.result()

    def test_task_with_none_return(self, parsl_config):
        """Test task that returns None."""

        @python_task
        def returns_none():
            return None

        future = returns_none(executor=["test-local"])
        result = future.result()
        assert result is None

    def test_bash_task_with_error(self, parsl_config):
        """Test bash_task with command that fails."""

        @bash_task
        def failing_bash():
            return "exit 1"

        future = failing_bash(executor=["test-local"])
        with pytest.raises(parsl.app.errors.BashExitFailure) as exc_info:
            future.result()
        assert exc_info.value.exitcode == 1

    def test_multiple_executors(self, parsl_config):
        """Test tasks with different executor specifications."""

        @python_task
        def task1():
            return 1

        @python_task
        def task2():
            return 2

        f1 = task1(executor=["test-local"])
        f2 = task2(executor="all")
        assert f1.result() == 1
        assert f2.result() == 2


# ===== Metadata Preservation Tests =====


class TestTaskMetadata:
    """Test that decorators properly preserve function metadata."""

    def test_python_task_preserves_name(self, parsl_config):
        """Test that python_task preserves function name."""

        @python_task
        def hello_world():
            return "Hello, World!"

        assert hello_world.__name__ == "hello_world"

    def test_bash_task_preserves_name(self, parsl_config):
        """Test that bash_task preserves function name."""

        @bash_task
        def echo_hello():
            return "echo 'Hello from Bash'"

        assert echo_hello.__name__ == "echo_hello"

    def test_join_task_preserves_name(self, parsl_config):
        """Test that join_task preserves function name."""

        @join_task
        def my_join_function():
            return 42

        assert my_join_function.__name__ == "my_join_function"

    def test_python_task_preserves_docstring(self, parsl_config):
        """Test that python_task preserves docstring."""

        @python_task
        def documented_function():
            """This is a test docstring."""
            return "test"

        assert documented_function.__doc__ == "This is a test docstring."

    def test_python_task_with_var_kwargs_and_file_output(self, parsl_config):
        """Test python_task with **kwargs that receives Parsl-injected stdout/stderr."""

        @python_task
        def task_with_var_kwargs(x, **kwargs):
            # This function accepts **kwargs, so all kwargs should be passed through
            # Including any user-provided kwargs beyond Parsl-injected ones
            bonus = kwargs.get("bonus", 0)
            return x * 2 + bonus

        # Pass both a user kwarg and stdout to test kwargs passthrough
        future = task_with_var_kwargs(5, bonus=10, executor=["test-local"])
        result = future.result()
        assert result == 20  # (5 * 2) + 10

    def test_decorated_method_accessed_on_class(self, parsl_config):
        """Test accessing decorated method on class (not instance) returns descriptor."""

        class TestClass:
            @python_task
            def my_method(self, x):
                return x + 1

        # Access on class (not instance) should return the MethodWrapper itself
        method_on_class = TestClass.my_method
        assert hasattr(method_on_class, "__get__")  # It's a descriptor
        # Verify it's a MethodWrapper by checking for the wrapper_func attribute
        assert hasattr(method_on_class, "wrapper_func")

    def test_bash_task_with_var_kwargs_and_user_args(self, parsl_config):
        """Test bash_task with **kwargs receiving both user and Parsl kwargs."""

        @bash_task
        def bash_with_var_kwargs(message, **kwargs):
            # Extra kwargs available if needed
            prefix = kwargs.get("prefix", "")
            return f"echo '{prefix}{message}'"

        future = bash_with_var_kwargs(
            "test message", prefix="[INFO] ", executor=["test-local"]
        )
        result = future.result()
        assert result == 0

    def test_create_filtered_wrapper_with_var_keyword(self, parsl_config):
        """Test _create_filtered_wrapper directly with a function that has **kwargs."""
        from chiltepin.tasks import _create_filtered_wrapper

        # Function with **kwargs should pass all kwargs through
        def func_with_var_kwargs(x, y=10, **kwargs):
            bonus = kwargs.get("bonus", 0)
            extra = kwargs.get("extra", 0)
            return x + y + bonus + extra

        wrapped = _create_filtered_wrapper(func_with_var_kwargs)

        # Call the wrapper directly (not through Parsl) with extra kwargs
        result = wrapped(5, y=20, bonus=10, extra=3, ignored_kwarg="should_be_passed")
        assert result == 38  # 5 + 20 + 10 + 3 = 38

    def test_create_filtered_wrapper_without_var_keyword(self, parsl_config):
        """Test _create_filtered_wrapper directly with a function that does NOT have **kwargs."""
        from chiltepin.tasks import _create_filtered_wrapper

        # Function without **kwargs should filter out unknown kwargs
        def func_without_var_kwargs(x, y=10):
            return x + y

        wrapped = _create_filtered_wrapper(func_without_var_kwargs)

        # Call the wrapper with extra kwargs that should be filtered out
        result = wrapped(5, y=20, ignored_kwarg="should_be_filtered")
        assert result == 25  # 5 + 20 = 25

import logging
import os.path
import pathlib

import parsl
import pytest

import chiltepin.configure
from chiltepin.tasks import bash_task, python_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Create directory for test output
    output_dir = pwd / "test_output"
    output_dir.mkdir(exist_ok=True)

    yaml_config = chiltepin.configure.parse_file(config_file)
    yaml_config[platform]["resources"]["service"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )

    # Set Parsl logging to DEBUG and redirect to a file in the output directory
    logger_handler = parsl.set_file_logger(
        filename=str(output_dir / "test_parsl_hello_parsl.log"),
        level=logging.DEBUG,
    )

    resources = chiltepin.configure.load(
        yaml_config[platform]["resources"],
        include=["service"],
        run_dir=str(output_dir / "test_parsl_hello_runinfo"),
    )

    # Load the resources in Parsl
    dfk = parsl.load(resources)

    # Run the tests with the loaded resources
    yield {"output_dir": output_dir}

    # Cleanup Parsl after tests are done
    dfk.cleanup()
    dfk = None
    parsl.clear()
    logger_handler()


# Test bash hello world
def test_parsl_hello_bash(config):
    output_dir = config["output_dir"]

    # Define a "hello world" Bash task
    @bash_task
    def bash_hello():
        return 'echo "Hello World! from bash task"'

    # Remove previous test output if it exists
    if os.path.exists(output_dir / "test_parsl_hello_bash.out"):
        os.remove(output_dir / "test_parsl_hello_bash.out")
    if os.path.exists(output_dir / "test_parsl_hello_bash.err"):
        os.remove(output_dir / "test_parsl_hello_bash.err")

    future = bash_hello(
        stdout=os.path.join(output_dir, "test_parsl_hello_bash.out"),
        stderr=os.path.join(output_dir, "test_parsl_hello_bash.err"),
        executor=["service"],
    )

    # Verify exit status is 0
    assert future.result() == 0

    baseline_stdout = "Hello World! from bash task\n"
    baseline_stderr = """\
--> executable follows <--
echo "Hello World! from bash task"
--> end executable <--
"""
    with open(output_dir / "test_parsl_hello_bash.out", "r") as f:
        assert f.read() == baseline_stdout
    with open(output_dir / "test_parsl_hello_bash.err", "r") as f:
        assert f.read() == baseline_stderr


# Test python hello world
def test_parsl_hello_python(config):
    # Define a "hello world" Python task
    @python_task
    def python_hello():
        return "Hello World! from python task"

    future = python_hello(executor=["service"])
    assert future.result() == "Hello World! from python task"

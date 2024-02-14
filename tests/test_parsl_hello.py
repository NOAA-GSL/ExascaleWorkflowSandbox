import parsl
import pytest
from parsl.app.app import bash_app, python_app
from parsl.configs.local_threads import config


# Define a "hello world" Python Parsl App
@python_app
def python_hello(stdout=None, stderr=None):
    return "Hello World! from Python App"


# Define a "hello world" Bash Parsl App
@bash_app
def bash_hello(stdout=None, stderr=None):
    return 'echo "Hello World! from Bash App"'


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture
def load_config():
    parsl.load(config)
    yield
    parsl.clear()


# Test bash hello world
def test_bash_hello(load_config):
    assert (
        bash_hello(
            stdout=("parsl_bash_hello.out", "w"), stderr=("parsl_bash_hello.err", "w")
        ).result()
        == 0
    )
    baseline_stdout = "Hello World! from Bash App\n"
    baseline_stderr = """\
--> executable follows <--
echo "Hello World! from Bash App"
--> end executable <--
"""
    with open("parsl_bash_hello.out", "r") as f:
        assert f.read() == baseline_stdout
    with open("parsl_bash_hello.err", "r") as f:
        assert f.read() == baseline_stderr


# Test python hello world
def test_python_hello(load_config):
    assert python_hello().result() == "Hello World! from Python App"

import pathlib
import subprocess

from globus_compute_sdk import Executor


def test_endpoint_start():
    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        ["globus-compute-endpoint", "-c", f"{pwd}/globus_compute", "start", "service"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=20,
    )
    assert p.returncode == 0


def test_endpoint_hello():
    def hello():
        return "Hello"

    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        f"globus-compute-endpoint -c {pwd}/globus_compute list | grep service | cut -d' ' -f 2",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=20,
        shell=True,
    )
    assert p.returncode == 0
    hello_endpoint_id = p.stdout.strip()
    assert len(hello_endpoint_id) == 36
    with Executor(endpoint_id=hello_endpoint_id) as gce:
        future = gce.submit(hello)
        assert future.result() == "Hello"


def test_endpoint_stop():
    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        ["globus-compute-endpoint", "-c", f"{pwd}/globus_compute", "stop", "service"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=20,
    )
    assert p.returncode == 0

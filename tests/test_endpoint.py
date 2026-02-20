import os
import pathlib
import shutil

import chiltepin.endpoint as endpoint


def test_endpoint_list_empty():
    pwd = pathlib.Path(__file__).parent.resolve()

    # Create directory for test output
    config_dir_test = pwd / "test_output" / ".globus_compute"
    config_dir_test.mkdir(parents=True, exist_ok=True)

    # Start from a clean state
    if os.path.exists(f"{config_dir_test}"):
        shutil.rmtree(f"{config_dir_test}")
    # List endpoints with a config_dir
    ep_list = endpoint.show(config_dir=f"{config_dir_test}")
    assert ep_list == {}


def test_endpoint_configure():
    pwd = pathlib.Path(__file__).parent.resolve()

    # Create directory for test output
    config_dir_default = pathlib.Path.home() / ".globus_compute"
    config_dir_test = pwd / "test_output" / ".globus_compute"
    config_dir_test.mkdir(parents=True, exist_ok=True)

    # Start from a clean state
    if os.path.exists(f"{config_dir_default}/foo"):
        shutil.rmtree(f"{config_dir_default}/foo")
    if os.path.exists(f"{config_dir_test}/bar"):
        shutil.rmtree(f"{config_dir_test}/bar")

    # Configure an endpoint without a config_dir
    endpoint.configure("foo")
    assert os.path.exists(f"{config_dir_default}/foo/config.yaml")

    # Configure an endpoint with a config_dir
    endpoint.configure("bar", config_dir=f"{config_dir_test}")
    assert os.path.exists(f"{config_dir_test}/bar/config.yaml")

    # Set init_blocks in configs to 0 so we don't have to wait for workers
    # to shut down before we can delete the endpoint
    for filename in [
        f"{config_dir_default}/foo/config.yaml",
        f"{config_dir_test}/bar/config.yaml",
    ]:
        with open(filename, "r") as file:
            config = file.read()
            new_config = config.replace("init_blocks: 1", "init_blocks: 0")
        with open(filename, "w") as file:
            file.write(new_config)


def test_endpoint_list_nonempty_initialized():
    pwd = pathlib.Path(__file__).parent.resolve()
    config_dir_test = pwd / "test_output" / ".globus_compute"
    # List endpoints without a config_dir
    ep_list = endpoint.show()
    assert ep_list["foo"] == {"id": None, "status": "Initialized"}
    # List endpoints with a config_dir
    ep_list = endpoint.show(config_dir=f"{config_dir_test}")
    assert ep_list["bar"] == {"id": None, "status": "Initialized"}


def test_endpoint_start():
    pwd = pathlib.Path(__file__).parent.resolve()
    config_dir_test = pwd / "test_output" / ".globus_compute"
    # Start an endpoint without a config_dir
    endpoint.start("foo", timeout=30)
    # Start an endpoint with a config_dir
    endpoint.start("bar", config_dir=f"{config_dir_test}", timeout=30)
    # Verify they are running
    ep_list = endpoint.show()
    assert ep_list["foo"]["status"] == "Running"
    assert len(ep_list["foo"]["id"]) == 36
    ep_list = endpoint.show(config_dir=f"{config_dir_test}")
    assert ep_list["bar"]["status"] == "Running"
    assert len(ep_list["bar"]["id"]) == 36


def test_endpoint_stop():
    pwd = pathlib.Path(__file__).parent.resolve()
    config_dir_test = pwd / "test_output" / ".globus_compute"
    # Stop an endpoint without a config_dir
    endpoint.stop("foo", timeout=30)
    # Stop an endpoint with a config_dir
    endpoint.stop("bar", config_dir=f"{config_dir_test}", timeout=30)
    # Verify they are stopped
    ep_list = endpoint.show()
    assert ep_list["foo"]["status"] == "Stopped"
    assert len(ep_list["foo"]["id"]) == 36
    ep_list = endpoint.show(config_dir=f"{config_dir_test}")
    assert ep_list["bar"]["status"] == "Stopped"
    assert len(ep_list["bar"]["id"]) == 36


def test_endpoint_delete():
    pwd = pathlib.Path(__file__).parent.resolve()
    config_dir_test = pwd / "test_output" / ".globus_compute"
    # Delete an endpoint without a config_dir
    endpoint.delete("foo", timeout=30)
    # Delete an endpoint with a config_dir
    endpoint.delete("bar", config_dir=f"{config_dir_test}", timeout=30)
    # Verify they are deleted
    ep_list = endpoint.show()
    assert ep_list.get("foo", None) is None
    assert not os.path.exists(f"{os.environ['HOME']}/.globus_compute/foo")
    ep_list = endpoint.show(config_dir=f"{config_dir_test}")
    assert ep_list.get("bar", None) is None
    assert not os.path.exists(f"{config_dir_test}/bar")

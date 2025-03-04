import os
import pathlib
import shutil

import chiltepin.endpoint as endpoint


def test_endpoint_list_empty():
    pwd = pathlib.Path(__file__).parent.resolve()
    # Start from a clean state
    if os.path.exists(f"{pwd}/.globus_compute"):
        shutil.rmtree(f"{pwd}/.globus_compute")
    # List endpoints with a config_dir
    ep_list = endpoint.show(config_dir=f"{pwd}/.globus_compute")
    assert ep_list == {}


def test_endpoint_configure():
    pwd = pathlib.Path(__file__).parent.resolve()
    # Start from a clean state
    if os.path.exists(f"{os.environ['HOME']}/.globus_compute/foo"):
        shutil.rmtree(f"{os.environ['HOME']}/.globus_compute/foo")
    if os.path.exists(f"{pwd}/.globus_compute/bar"):
        shutil.rmtree(f"{pwd}/.globus_compute/bar")

    # Configure an endpoint without a config_dir
    endpoint.configure("foo")
    assert os.path.exists(f"{os.environ['HOME']}/.globus_compute/foo/config.yaml")

    # Configure an endpoint with a config_dir
    endpoint.configure("bar", config_dir=f"{pwd}/.globus_compute")
    assert os.path.exists(f"{pwd}/.globus_compute/bar/config.yaml")

    # Set init_blocks in configs to 0 so we don't have to wait for workers
    # to shut down before we can delete the endpoint
    for filename in [
        f"{os.environ['HOME']}/.globus_compute/foo/config.yaml",
        f"{pwd}/.globus_compute/bar/config.yaml",
    ]:
        with open(filename, "r") as file:
            config = file.read()
            new_config = config.replace("init_blocks: 1", "init_blocks: 0")
        with open(filename, "w") as file:
            file.write(new_config)


def test_endpoint_list_nonempty_initialized():
    pwd = pathlib.Path(__file__).parent.resolve()
    # List endpoints without a config_dir
    ep_list = endpoint.show()
    assert ep_list["foo"] == {"id": "None", "state": "Initialized"}
    # List endpoints with a config_dir
    ep_list = endpoint.show(config_dir=f"{pwd}/.globus_compute")
    assert ep_list["bar"] == {"id": "None", "state": "Initialized"}


def test_endpoint_start():
    pwd = pathlib.Path(__file__).parent.resolve()
    # Start an endpoint without a config_dir
    endpoint.start("foo")
    # Start an endpoint with a config_dir
    endpoint.start("bar", config_dir=f"{pwd}/.globus_compute")
    # Verify they are running
    ep_list = endpoint.show()
    assert ep_list["foo"]["state"] == "Running"
    assert len(ep_list["foo"]["id"]) == 36
    ep_list = endpoint.show(config_dir=f"{pwd}/.globus_compute")
    assert ep_list["bar"]["state"] == "Running"
    assert len(ep_list["bar"]["id"]) == 36


def test_endpoint_stop():
    pwd = pathlib.Path(__file__).parent.resolve()
    # Stop an endpoint without a config_dir
    endpoint.stop("foo")
    # Stop an endpoint with a config_dir
    endpoint.stop("bar", config_dir=f"{pwd}/.globus_compute")
    # Verify they are stopped
    ep_list = endpoint.show()
    assert ep_list["foo"]["state"] == "Stopped"
    assert len(ep_list["foo"]["id"]) == 36
    ep_list = endpoint.show(config_dir=f"{pwd}/.globus_compute")
    assert ep_list["bar"]["state"] == "Stopped"
    assert len(ep_list["bar"]["id"]) == 36


def test_endpoint_delete():
    pwd = pathlib.Path(__file__).parent.resolve()
    # Delete an endpoint without a config_dir
    endpoint.delete("foo")
    # Delete an endpoint with a config_dir
    endpoint.delete("bar", config_dir=f"{pwd}/.globus_compute")
    # Verify they are deleted
    assert not os.path.exists(f"{os.environ['HOME']}/.globus_compute/foo")
    assert not os.path.exists(f"{pwd}/.globus_compute/bar")

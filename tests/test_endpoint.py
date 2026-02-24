import os
import pathlib
import shutil
import tempfile
import time
from unittest.mock import MagicMock, mock_open, patch
from uuid import UUID

import pytest
import yaml

import chiltepin.endpoint as endpoint

# =============================================================================
# Integration Tests - These test the full endpoint lifecycle and must run in order
# =============================================================================


class TestEndpointIntegration:
    """Integration tests for endpoint lifecycle: configure -> start -> stop -> delete.

    Tests depend on state from previous tests and must run in the order they appear
    in this file. Each test is split by config_dir scenario so that failures are
    isolated to the specific scenario that failed.
    """

    def test_show_empty(self):
        """Test listing endpoints when none exist (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"
        config_dir_test.mkdir(parents=True, exist_ok=True)

        # Start from a clean state
        if os.path.exists(f"{config_dir_test}"):
            shutil.rmtree(f"{config_dir_test}")

        ep_list = endpoint.show(config_dir=f"{config_dir_test}")
        assert ep_list == {}

    def test_is_running_nonexistent(self):
        """Test is_running returns False for nonexistent endpoint."""
        assert endpoint.is_running("nonexistent_endpoint_xyz_123") is False

    def test_exists_nonexistent(self):
        """Test exists returns False for nonexistent endpoint."""
        assert endpoint.exists("nonexistent_endpoint_xyz_123") is False

    def test_configure_default_config_dir(self):
        """Test configuring endpoint with default config_dir."""
        config_dir_default = pathlib.Path.home() / ".globus_compute"

        # Start from a clean state
        if os.path.exists(f"{config_dir_default}/foo"):
            shutil.rmtree(f"{config_dir_default}/foo")

        # Configure an endpoint without a config_dir
        endpoint.configure("foo")
        assert os.path.exists(f"{config_dir_default}/foo/config.yaml")

    def test_configure_custom_config_dir(self):
        """Test configuring endpoint with custom config_dir."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"
        config_dir_test.mkdir(parents=True, exist_ok=True)

        # Start from a clean state
        if os.path.exists(f"{config_dir_test}/bar"):
            shutil.rmtree(f"{config_dir_test}/bar")

        # Configure an endpoint with a config_dir
        endpoint.configure("bar", config_dir=f"{config_dir_test}")
        assert os.path.exists(f"{config_dir_test}/bar/config.yaml")

    def test_show_initialized_default_config_dir(self):
        """Test listing endpoint in Initialized state (default config_dir)."""
        ep_list = endpoint.show()
        assert ep_list["foo"] == {"id": None, "status": "Initialized"}

    def test_show_initialized_custom_config_dir(self):
        """Test listing endpoint in Initialized state (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"

        ep_list = endpoint.show(config_dir=f"{config_dir_test}")
        assert ep_list["bar"] == {"id": None, "status": "Initialized"}

    def test_exists_default_config_dir(self):
        """Test exists returns True for configured endpoint (default config_dir)."""
        assert endpoint.exists("foo") is True

    def test_exists_custom_config_dir(self):
        """Test exists returns True for configured endpoint (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"
        assert endpoint.exists("bar", config_dir=f"{config_dir_test}") is True

    def test_start_default_config_dir(self):
        """Test starting endpoint (default config_dir)."""
        endpoint.start("foo", timeout=30)

        # Verify it is running
        ep_list = endpoint.show()
        assert ep_list["foo"]["status"] == "Running"
        # Verify the endpoint ID is a valid UUID
        assert UUID(ep_list["foo"]["id"]) is not None

    def test_is_running_default_config_dir(self):
        """Test is_running returns True for running endpoint (default config_dir)."""
        assert endpoint.is_running("foo") is True

    def test_start_custom_config_dir(self):
        """Test starting endpoint (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"

        endpoint.start("bar", config_dir=f"{config_dir_test}", timeout=30)

        # Verify it is running
        ep_list = endpoint.show(config_dir=f"{config_dir_test}")
        assert ep_list["bar"]["status"] == "Running"
        # Verify the endpoint ID is a valid UUID
        assert UUID(ep_list["bar"]["id"]) is not None

    def test_is_running_custom_config_dir(self):
        """Test is_running returns True for running endpoint (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"
        assert endpoint.is_running("bar", config_dir=f"{config_dir_test}") is True

    def test_stop_default_config_dir(self):
        """Test stopping endpoint (default config_dir)."""
        endpoint.stop("foo", timeout=30)

        # Verify it is stopped
        ep_list = endpoint.show()
        assert ep_list["foo"]["status"] == "Stopped"
        # Verify the endpoint ID is still a valid UUID
        assert UUID(ep_list["foo"]["id"]) is not None

    def test_is_not_running_default_config_dir(self):
        """Test is_running returns False for stopped endpoint (default config_dir)."""
        assert endpoint.is_running("foo") is False

    def test_stop_custom_config_dir(self):
        """Test stopping endpoint (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"

        endpoint.stop("bar", config_dir=f"{config_dir_test}", timeout=30)

        # Verify it is stopped
        ep_list = endpoint.show(config_dir=f"{config_dir_test}")
        assert ep_list["bar"]["status"] == "Stopped"
        # Verify the endpoint ID is still a valid UUID
        assert UUID(ep_list["bar"]["id"]) is not None

    def test_is_not_running_custom_config_dir(self):
        """Test is_running returns False for stopped endpoint (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"
        assert endpoint.is_running("bar", config_dir=f"{config_dir_test}") is False

    def test_delete_default_config_dir(self):
        """Test deleting endpoint (default config_dir)."""
        endpoint.delete("foo", timeout=30)

        # Verify it is deleted
        ep_list = endpoint.show()
        assert ep_list.get("foo", None) is None
        assert not os.path.exists(f"{pathlib.Path.home()}/.globus_compute/foo")

    def test_delete_custom_config_dir(self):
        """Test deleting endpoint (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"

        endpoint.delete("bar", config_dir=f"{config_dir_test}", timeout=30)

        # Verify it is deleted
        ep_list = endpoint.show(config_dir=f"{config_dir_test}")
        assert ep_list.get("bar", None) is None
        assert not os.path.exists(f"{config_dir_test}/bar")

    def test_not_exists_default_config_dir(self):
        """Test exists returns False for deleted endpoint (default config_dir)."""
        assert endpoint.exists("foo") is False

    def test_not_exists_custom_config_dir(self):
        """Test exists returns False for deleted endpoint (custom config_dir)."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute"
        assert endpoint.exists("bar", config_dir=f"{config_dir_test}") is False


# =============================================================================
# Unit Tests - Organized by function in endpoint.py order
# =============================================================================


class TestGetChiltepinApps:
    """Tests for get_chiltepin_apps() function."""

    def test_with_client_secret_but_no_id(self):
        """Test that RuntimeError is raised when SECRET is set but ID is not."""
        # Save original env vars
        orig_id = os.environ.pop("GLOBUS_COMPUTE_CLIENT_ID", None)
        orig_secret = os.environ.get("GLOBUS_COMPUTE_CLIENT_SECRET")

        try:
            # Set up scenario: SECRET set but ID not set
            os.environ["GLOBUS_COMPUTE_CLIENT_SECRET"] = "test_secret"

            with pytest.raises(
                RuntimeError,
                match=r"\$GLOBUS_COMPUTE_CLIENT_SECRET is set but \$GLOBUS_COMPUTE_CLIENT_ID is not",
            ):
                endpoint.get_chiltepin_apps()
        finally:
            # Restore original env vars
            os.environ.pop("GLOBUS_COMPUTE_CLIENT_SECRET", None)
            if orig_id:
                os.environ["GLOBUS_COMPUTE_CLIENT_ID"] = orig_id
            if orig_secret:
                os.environ["GLOBUS_COMPUTE_CLIENT_SECRET"] = orig_secret

    def test_with_client_credentials(self):
        """Test that ClientApp is created when client_secret is provided."""
        with patch.dict(
            os.environ,
            {
                "GLOBUS_COMPUTE_CLIENT_ID": "test_client_id",
                "GLOBUS_COMPUTE_CLIENT_SECRET": "test_secret",
            },
            clear=False,
        ):
            with patch("chiltepin.endpoint.get_globus_app") as mock_get_app:
                with patch("chiltepin.endpoint.ClientApp") as mock_client_app:
                    with patch("chiltepin.endpoint.UserApp"):
                        mock_compute_app = MagicMock()
                        mock_get_app.return_value = mock_compute_app

                        compute_app, transfer_app = endpoint.get_chiltepin_apps()

                        # Verify GLOBUS_CLI_* env vars were set
                        assert os.environ["GLOBUS_CLI_CLIENT_ID"] == "test_client_id"
                        assert os.environ["GLOBUS_CLI_CLIENT_SECRET"] == "test_secret"

                        # Verify ClientApp was called for transfer client
                        mock_client_app.assert_called_once_with(
                            "chiltepin",
                            client_id="test_client_id",
                            client_secret="test_secret",
                        )

    def test_without_client_credentials(self):
        """Test that UserApp is created when no client_secret is provided."""
        # Save original env vars
        orig_id = os.environ.pop("GLOBUS_COMPUTE_CLIENT_ID", None)
        orig_secret = os.environ.pop("GLOBUS_COMPUTE_CLIENT_SECRET", None)

        try:
            with patch("chiltepin.endpoint.get_globus_app") as mock_get_app:
                with patch("chiltepin.endpoint.UserApp") as mock_user_app:
                    mock_compute_app = MagicMock()
                    mock_get_app.return_value = mock_compute_app

                    compute_app, transfer_app = endpoint.get_chiltepin_apps()

                    # Verify UserApp was called for transfer client
                    mock_user_app.assert_called_once_with(
                        "chiltepin",
                        client_id=endpoint.CHILTEPIN_CLIENT_UUID,
                    )
        finally:
            # Restore original env vars
            if orig_id:
                os.environ["GLOBUS_COMPUTE_CLIENT_ID"] = orig_id
            if orig_secret:
                os.environ["GLOBUS_COMPUTE_CLIENT_SECRET"] = orig_secret


class TestLogin:
    """Tests for login() function."""

    def test_with_login_required(self):
        """Test login when both apps require login."""
        with patch("chiltepin.endpoint.get_chiltepin_apps") as mock_get_apps:
            with patch("chiltepin.endpoint.Client"):
                with patch("chiltepin.endpoint.TransferClient"):
                    # Setup mocks
                    mock_compute_app = MagicMock()
                    mock_transfer_app = MagicMock()
                    mock_compute_app.login_required.return_value = True
                    mock_transfer_app.login_required.return_value = True

                    mock_get_apps.return_value = (mock_compute_app, mock_transfer_app)

                    # Call login
                    clients = endpoint.login()

                    # Verify login was called on both apps
                    mock_compute_app.login.assert_called_once()
                    mock_transfer_app.login.assert_called_once()

                    # Verify clients were created
                    assert "compute" in clients
                    assert "transfer" in clients

    def test_without_login_required(self):
        """Test login when apps don't require login."""
        with patch("chiltepin.endpoint.get_chiltepin_apps") as mock_get_apps:
            with patch("chiltepin.endpoint.Client"):
                with patch("chiltepin.endpoint.TransferClient"):
                    # Setup mocks
                    mock_compute_app = MagicMock()
                    mock_transfer_app = MagicMock()
                    mock_compute_app.login_required.return_value = False
                    mock_transfer_app.login_required.return_value = False

                    mock_get_apps.return_value = (mock_compute_app, mock_transfer_app)

                    # Call login
                    endpoint.login()

                    # Verify login was NOT called
                    mock_compute_app.login.assert_not_called()
                    mock_transfer_app.login.assert_not_called()


class TestLoginRequired:
    """Tests for login_required() function."""

    def test_returns_true_when_login_needed(self):
        """Test login_required returns True if either app requires login."""
        with patch("chiltepin.endpoint.get_chiltepin_apps") as mock_get_apps:
            mock_compute_app = MagicMock()
            mock_transfer_app = MagicMock()
            mock_compute_app.login_required.return_value = True
            mock_transfer_app.login_required.return_value = False

            mock_get_apps.return_value = (mock_compute_app, mock_transfer_app)

            # Should return True if either app requires login
            assert endpoint.login_required() is True


class TestLogout:
    """Tests for logout() function."""

    def test_logout_calls_both_apps(self):
        """Test logout calls logout on both apps."""
        with patch("chiltepin.endpoint.get_chiltepin_apps") as mock_get_apps:
            mock_compute_app = MagicMock()
            mock_transfer_app = MagicMock()
            mock_get_apps.return_value = (mock_compute_app, mock_transfer_app)

            endpoint.logout()

            # Verify logout was called on both apps
            mock_compute_app.logout.assert_called_once()
            mock_transfer_app.logout.assert_called_once()


class TestConfigure:
    """Tests for configure() function."""

    @patch("platform.system", return_value="Windows")
    def test_windows_not_supported(self, mock_system):
        """Test that configure raises NotImplementedError on Windows."""
        with pytest.raises(
            NotImplementedError,
            match="Globus Compute endpoints are not supported on Windows",
        ):
            endpoint.configure("test_endpoint")

    def test_timeout(self):
        """Test that configure raises TimeoutError when subprocess times out."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute_timeout"
        config_dir_test.mkdir(parents=True, exist_ok=True)

        with patch("subprocess.Popen") as mock_popen:
            import subprocess

            mock_process = MagicMock()
            mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 0.1)
            mock_popen.return_value = mock_process

            with pytest.raises(TimeoutError, match="configure command timed out"):
                endpoint.configure(
                    "timeout_test", config_dir=str(config_dir_test), timeout=0.1
                )

    def test_command_failure(self):
        """Test that configure raises RuntimeError when command fails."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute_fail"
        config_dir_test.mkdir(parents=True, exist_ok=True)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("error output", "")
            mock_process.returncode = 1
            mock_popen.return_value = mock_process

            with pytest.raises(RuntimeError, match="Failed to configure endpoint"):
                endpoint.configure("fail_test", config_dir=str(config_dir_test))

    def test_yaml_read_error(self):
        """Test that configure returns False when YAML read fails."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute_yaml_read"
        config_dir_test.mkdir(parents=True, exist_ok=True)
        endpoint_dir = config_dir_test / "yaml_read_test"
        endpoint_dir.mkdir(parents=True, exist_ok=True)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("success", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            with patch("builtins.open", mock_open(read_data="invalid: yaml: [{}")):
                with patch(
                    "yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")
                ):
                    result = endpoint.configure(
                        "yaml_read_test", config_dir=str(config_dir_test)
                    )
                    assert result is False

    def test_yaml_write_error(self):
        """Test that configure returns False when YAML write fails."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute_yaml_write"
        config_dir_test.mkdir(parents=True, exist_ok=True)
        endpoint_dir = config_dir_test / "yaml_write_test"
        endpoint_dir.mkdir(parents=True, exist_ok=True)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("success", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Mock the file operations
            config_content = yaml.dump({"display_name": "test", "debug": False})

            # First open for reading succeeds, second for writing fails
            m = mock_open(read_data=config_content)
            with patch("builtins.open", m):
                with patch("yaml.dump", side_effect=yaml.YAMLError("Write error")):
                    result = endpoint.configure(
                        "yaml_write_test", config_dir=str(config_dir_test)
                    )
                    # The function should return False when yaml.dump fails
                    assert result is False

    def test_path_capture_timeout(self):
        """Test configure when PATH capture subprocess times out."""
        import subprocess

        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute_path_timeout"
        config_dir_test.mkdir(parents=True, exist_ok=True)
        endpoint_dir = config_dir_test / "path_timeout_test"
        endpoint_dir.mkdir(parents=True, exist_ok=True)

        call_count = [0]

        def mock_popen_side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_process = MagicMock()

            if call_count[0] == 1:
                # First call (configure command) succeeds
                mock_process.communicate.return_value = ("success", "")
                mock_process.returncode = 0
            else:
                # Second call (PATH capture) times out
                mock_process.communicate.side_effect = subprocess.TimeoutExpired(
                    "cmd", 0.5
                )

            return mock_process

        with patch("subprocess.Popen", side_effect=mock_popen_side_effect):
            # Create a minimal config file
            (endpoint_dir / "config.yaml").write_text(
                yaml.dump({"display_name": "test", "debug": False})
            )

            with pytest.raises(TimeoutError, match="PATH capture command timed out"):
                endpoint.configure(
                    "path_timeout_test", config_dir=str(config_dir_test), timeout=1
                )

    def test_path_capture_failure(self):
        """Test configure when PATH capture command returns non-zero."""
        pwd = pathlib.Path(__file__).parent.resolve()
        config_dir_test = pwd / "test_output" / ".globus_compute_path_fail"
        config_dir_test.mkdir(parents=True, exist_ok=True)
        endpoint_dir = config_dir_test / "path_fail_test"
        endpoint_dir.mkdir(parents=True, exist_ok=True)

        call_count = [0]

        def mock_popen_side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_process = MagicMock()

            if call_count[0] == 1:
                # First call (configure command) succeeds
                mock_process.communicate.return_value = ("success", "")
                mock_process.returncode = 0
            else:
                # Second call (PATH capture) fails
                mock_process.communicate.return_value = ("", "PATH error")
                mock_process.returncode = 1

            return mock_process

        with patch("subprocess.Popen", side_effect=mock_popen_side_effect):
            # Create a minimal config file
            (endpoint_dir / "config.yaml").write_text(
                yaml.dump({"display_name": "test", "debug": False})
            )

            with pytest.raises(RuntimeError, match="Failed to capture system PATH"):
                endpoint.configure("path_fail_test", config_dir=str(config_dir_test))


class TestStart:
    """Tests for start() function."""

    @patch("platform.system", return_value="Windows")
    def test_windows_not_supported(self, mock_system):
        """Test that start raises NotImplementedError on Windows."""
        with pytest.raises(
            NotImplementedError,
            match="Globus Compute endpoints are not supported on Windows",
        ):
            endpoint.start("test_endpoint")

    def test_login_required(self):
        """Test that start raises RuntimeError when login is required."""
        with patch("chiltepin.endpoint.login_required", return_value=True):
            with pytest.raises(RuntimeError, match="Chiltepin login is required"):
                endpoint.start("test_endpoint")

    def test_timeout(self):
        """Test that start raises TimeoutError when endpoint doesn't start in time."""
        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("os.fork", return_value=1):  # Parent process
                with patch("os.waitpid"):
                    with patch("chiltepin.endpoint.is_running", return_value=False):
                        with patch(
                            "chiltepin.endpoint._read_startup_errors", return_value=""
                        ):
                            with pytest.raises(TimeoutError, match="Timeout of"):
                                endpoint.start("test_endpoint", timeout=0.1)

    def test_timeout_with_errors(self):
        """Test that start raises TimeoutError with error message when available."""
        start_time = [time.time()]

        def mock_read_errors(path, max_size=10240):
            # Return error message after timeout is exceeded
            # This simulates error file being written just as timeout occurs
            elapsed = time.time() - start_time[0]
            if elapsed > 0.1:  # After timeout
                return "Error starting endpoint"
            return ""  # Before timeout

        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("os.fork", return_value=1):  # Parent process
                with patch("os.waitpid"):
                    with patch("chiltepin.endpoint.is_running", return_value=False):
                        with patch(
                            "chiltepin.endpoint._read_startup_errors",
                            side_effect=mock_read_errors,
                        ):
                            with pytest.raises(TimeoutError, match="Startup errors:"):
                                endpoint.start("test_endpoint", timeout=0.1)

    def test_failure_with_errors(self):
        """Test that start raises RuntimeError when endpoint fails to start with errors."""
        call_count = [0]

        def mock_is_running(*args, **kwargs):
            call_count[0] += 1
            return False

        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("os.fork", return_value=1):  # Parent process
                with patch("os.waitpid"):
                    with patch(
                        "chiltepin.endpoint.is_running", side_effect=mock_is_running
                    ):
                        with patch(
                            "chiltepin.endpoint._read_startup_errors",
                            return_value="Fatal error",
                        ):
                            with pytest.raises(
                                RuntimeError, match="Endpoint.*failed to start"
                            ):
                                endpoint.start("test_endpoint", timeout=5)

    def test_cleanup_error(self):
        """Test that start handles OSError gracefully when cleaning up temp file."""
        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("os.fork", return_value=1):  # Parent process
                with patch("os.waitpid"):
                    with patch("chiltepin.endpoint.is_running", return_value=True):
                        with patch(
                            "chiltepin.endpoint._read_startup_errors", return_value=""
                        ):
                            with patch(
                                "os.unlink", side_effect=OSError("Cannot remove")
                            ):
                                # Should not raise an exception despite unlink error
                                endpoint.start("test_endpoint", timeout=5)


class TestReadStartupErrors:
    """Tests for _read_startup_errors() helper function."""

    def test_with_content(self):
        """Test _read_startup_errors returns content when file exists and has data."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Error: Something went wrong\n")
            temp_path = f.name

        try:
            error_msg = endpoint._read_startup_errors(temp_path)
            assert error_msg == "Error: Something went wrong"
        finally:
            os.unlink(temp_path)

    def test_empty_file(self):
        """Test _read_startup_errors returns empty string for empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = f.name

        try:
            error_msg = endpoint._read_startup_errors(temp_path)
            assert error_msg == ""
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        """Test _read_startup_errors returns empty string for nonexistent file."""
        error_msg = endpoint._read_startup_errors("/nonexistent/file.txt")
        assert error_msg == ""

    def test_with_max_size(self):
        """Test _read_startup_errors respects max_size parameter."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("A" * 100)
            temp_path = f.name

        try:
            error_msg = endpoint._read_startup_errors(temp_path, max_size=50)
            assert len(error_msg) <= 50
        finally:
            os.unlink(temp_path)

    def test_with_io_error(self):
        """Test _read_startup_errors handles IOError gracefully."""
        # Use a mock to simulate an IOError when reading
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", return_value=100):
                with patch("builtins.open", side_effect=IOError("Read error")):
                    error_msg = endpoint._read_startup_errors("/some/path")
                    assert error_msg == ""

    def test_with_os_error(self):
        """Test _read_startup_errors handles OSError gracefully."""
        # Use a mock to simulate an OSError
        with patch("os.path.exists", side_effect=OSError("Path error")):
            error_msg = endpoint._read_startup_errors("/some/path")
            assert error_msg == ""


class TestStop:
    """Tests for stop() function."""

    @patch("platform.system", return_value="Windows")
    def test_windows_not_supported(self, mock_system):
        """Test that stop raises NotImplementedError on Windows."""
        with pytest.raises(
            NotImplementedError,
            match="Globus Compute endpoints are not supported on Windows",
        ):
            endpoint.stop("test_endpoint")

    def test_login_required(self):
        """Test that stop raises RuntimeError when login is required."""
        with patch("chiltepin.endpoint.login_required", return_value=True):
            with pytest.raises(RuntimeError, match="Chiltepin login is required"):
                endpoint.stop("test_endpoint")

    def test_timeout(self):
        """Test that stop raises TimeoutError when endpoint doesn't stop in time."""
        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("chiltepin.endpoint.get_config"):
                with patch("chiltepin.endpoint.Endpoint.stop_endpoint"):
                    with patch("chiltepin.endpoint.is_running", return_value=True):
                        with pytest.raises(TimeoutError, match="Timeout of"):
                            endpoint.stop("test_endpoint", timeout=0.1)

    def test_with_psutil_timeout(self):
        """Test that stop retries when psutil.TimeoutExpired is raised."""
        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("chiltepin.endpoint.get_config"):
                with patch("chiltepin.endpoint.Endpoint.stop_endpoint") as mock_stop:
                    import psutil

                    # First call raises TimeoutExpired, second succeeds
                    mock_stop.side_effect = [psutil.TimeoutExpired(1), None]
                    with patch("chiltepin.endpoint.is_running", return_value=False):
                        # Should not raise an exception
                        endpoint.stop("test_endpoint", timeout=5)
                        # Verify stop_endpoint was called twice
                        assert mock_stop.call_count == 2


class TestDelete:
    """Tests for delete() function."""

    @patch("platform.system", return_value="Windows")
    def test_windows_not_supported(self, mock_system):
        """Test that delete raises NotImplementedError on Windows."""
        with pytest.raises(
            NotImplementedError,
            match="Globus Compute endpoints are not supported on Windows",
        ):
            endpoint.delete("test_endpoint")

    def test_login_required(self):
        """Test that delete raises RuntimeError when login is required."""
        with patch("chiltepin.endpoint.login_required", return_value=True):
            with pytest.raises(RuntimeError, match="Chiltepin login is required"):
                endpoint.delete("test_endpoint")

    def test_timeout(self):
        """Test that delete raises TimeoutError when endpoint deletion times out."""
        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("chiltepin.endpoint.get_config"):
                with patch("chiltepin.endpoint.Endpoint.delete_endpoint"):
                    with patch("chiltepin.endpoint.exists", return_value=True):
                        with pytest.raises(TimeoutError, match="Timeout of"):
                            endpoint.delete("test_endpoint", timeout=0.1)

    def test_with_config_error(self):
        """Test that delete uses force=True when get_config raises exception."""
        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch(
                "chiltepin.endpoint.get_config", side_effect=Exception("Config error")
            ):
                with patch(
                    "chiltepin.endpoint.Endpoint.delete_endpoint"
                ) as mock_delete:
                    with patch("chiltepin.endpoint.exists", return_value=False):
                        endpoint.delete("test_endpoint", timeout=5)
                        # Verify delete was called with force=True
                        assert mock_delete.call_args[1]["force"] is True

    def test_with_deletion_error(self):
        """Test that delete raises RuntimeError when Endpoint.delete_endpoint fails."""
        with patch("chiltepin.endpoint.login_required", return_value=False):
            with patch("chiltepin.endpoint.get_config"):
                with patch(
                    "chiltepin.endpoint.Endpoint.delete_endpoint",
                    side_effect=Exception("Delete failed"),
                ):
                    with pytest.raises(RuntimeError, match="Error deleting endpoint"):
                        endpoint.delete("test_endpoint", timeout=5)

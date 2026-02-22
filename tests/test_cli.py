"""Tests for the chiltepin CLI.

IMPORTANT: This test suite uses mocking to prevent ANY actual endpoint operations
from executing. This avoids authentication issues and system state changes that could
break your session or interfere with other tests.

The tests validate:
1. Command-line argument parsing
2. cli_list output formatting
3. main() function behavior (using mocks to avoid real execution)
"""

import argparse
import sys
from unittest import mock

import pytest

import chiltepin.cli as cli


class TestCLIParsing:
    """Test command-line argument parsing without executing commands."""

    def test_login_command(self):
        """Test parsing the login command."""
        with mock.patch.object(sys, "argv", ["chiltepin", "login"]):
            args = vars(cli.root_parser.parse_args())
            # Verify the function is set, but DON'T call it
            assert "func" in args
            assert args["func"].__name__ == "login"

    def test_logout_command(self):
        """Test parsing the logout command."""
        with mock.patch.object(sys, "argv", ["chiltepin", "logout"]):
            args = vars(cli.root_parser.parse_args())
            assert "func" in args
            assert args["func"].__name__ == "logout"

    def test_endpoint_configure_command(self):
        """Test parsing the endpoint configure command."""
        with mock.patch.object(
            sys, "argv", ["chiltepin", "endpoint", "configure", "test-endpoint"]
        ):
            args = vars(cli.root_parser.parse_args())
            assert "func" in args
            assert args["func"].__name__ == "configure"
            assert args["name"] == "test-endpoint"
            assert args["config_dir"] is None

    def test_endpoint_configure_with_config_dir(self):
        """Test parsing endpoint configure with config directory."""
        with mock.patch.object(
            sys,
            "argv",
            ["chiltepin", "endpoint", "-c", "/custom/dir", "configure", "test-ep"],
        ):
            args = vars(cli.root_parser.parse_args())
            assert args["func"].__name__ == "configure"
            assert args["name"] == "test-ep"
            assert args["config_dir"] == "/custom/dir"

    def test_endpoint_list_command(self):
        """Test parsing the endpoint list command."""
        with mock.patch.object(sys, "argv", ["chiltepin", "endpoint", "list"]):
            args = vars(cli.root_parser.parse_args())
            assert "func" in args
            assert args["func"].__name__ == "cli_list"
            assert args["config_dir"] is None

    def test_endpoint_start_command(self):
        """Test parsing the endpoint start command."""
        with mock.patch.object(
            sys, "argv", ["chiltepin", "endpoint", "start", "my-endpoint"]
        ):
            args = vars(cli.root_parser.parse_args())
            assert args["func"].__name__ == "start"
            assert args["name"] == "my-endpoint"

    def test_endpoint_stop_command(self):
        """Test parsing the endpoint stop command."""
        with mock.patch.object(
            sys, "argv", ["chiltepin", "endpoint", "stop", "my-endpoint"]
        ):
            args = vars(cli.root_parser.parse_args())
            assert args["func"].__name__ == "stop"
            assert args["name"] == "my-endpoint"

    def test_endpoint_delete_command(self):
        """Test parsing the endpoint delete command."""
        with mock.patch.object(
            sys, "argv", ["chiltepin", "endpoint", "delete", "my-endpoint"]
        ):
            args = vars(cli.root_parser.parse_args())
            assert args["func"].__name__ == "delete"
            assert args["name"] == "my-endpoint"

    def test_no_command_no_func(self):
        """Test that running with no command doesn't set 'func'."""
        with mock.patch.object(sys, "argv", ["chiltepin"]):
            args = vars(cli.root_parser.parse_args())
            # With no subcommand, no 'func' key is set
            assert "func" not in args

    def test_invalid_command_fails(self):
        """Test that an invalid command causes an error."""
        with mock.patch.object(sys, "argv", ["chiltepin", "invalid-command"]):
            with pytest.raises(SystemExit):
                cli.root_parser.parse_args()


class TestCLIList:
    """Test the cli_list function with mocked endpoint.show()."""

    @mock.patch("chiltepin.cli.endpoint.show")
    def test_list_with_endpoints(self, mock_show, capsys):
        """Test listing endpoints when endpoints are configured."""
        mock_ep_info = {
            "endpoint1": {
                "id": "12345678-1234-1234-1234-123456789012",
                "status": "Running",
            },
            "endpoint2": {
                "id": "87654321-4321-4321-4321-210987654321",
                "status": "Stopped",
            },
            "ep3": {"id": "abcdef00-0000-0000-0000-000000000000", "status": "Unknown"},
        }
        mock_show.return_value = mock_ep_info

        cli.cli_list()

        captured = capsys.readouterr()
        assert "endpoint1" in captured.out
        assert "endpoint2" in captured.out
        assert "ep3" in captured.out
        assert "12345678-1234-1234-1234-123456789012" in captured.out
        assert "Running" in captured.out
        assert "Stopped" in captured.out

    @mock.patch("chiltepin.cli.endpoint.show")
    def test_list_with_no_endpoints(self, mock_show, capsys):
        """Test listing when no endpoints are configured."""
        mock_show.return_value = {}

        cli.cli_list()

        captured = capsys.readouterr()
        assert "No endpoints are configured" in captured.out

    @mock.patch("chiltepin.cli.endpoint.show")
    def test_list_with_none_values(self, mock_show, capsys):
        """Test listing with missing ID or status."""
        mock_ep_info = {
            "endpoint1": {"id": None, "status": None},
            "endpoint2": {},
        }
        mock_show.return_value = mock_ep_info

        cli.cli_list()

        captured = capsys.readouterr()
        assert "endpoint1" in captured.out
        assert "None" in captured.out
        assert "Unknown" in captured.out

    @mock.patch("chiltepin.cli.endpoint.show")
    def test_list_with_config_dir(self, mock_show):
        """Test listing endpoints with custom config directory."""
        mock_ep_info = {
            "endpoint1": {
                "id": "12345678-1234-1234-1234-123456789012",
                "status": "Running",
            },
        }
        mock_show.return_value = mock_ep_info

        cli.cli_list(config_dir="/custom/dir")

        mock_show.assert_called_once_with(config_dir="/custom/dir")

    @mock.patch("chiltepin.cli.endpoint.show")
    def test_list_formatting(self, mock_show, capsys):
        """Test that list output is properly formatted and aligned."""
        mock_ep_info = {
            "short": {
                "id": "12345678-1234-1234-1234-123456789012",
                "status": "Running",
            },
            "very-long-endpoint-name": {
                "id": "87654321-4321-4321-4321-210987654321",
                "status": "Stopped",
            },
        }
        mock_show.return_value = mock_ep_info

        cli.cli_list()

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        # Both lines should have the endpoint name padded to the same width
        assert len(lines) == 2
        # Check that IDs start at the same column position
        short_id_pos = lines[0].index("12345678")
        long_id_pos = lines[1].index("87654321")
        assert short_id_pos == long_id_pos


class TestCLIMainSafely:
    """Test the main() function safely by mocking parse_args to avoid calling real functions.

    CRITICAL: We mock root_parser.parse_args() so the real endpoint functions are NEVER called.
    This prevents authentication issues and system state changes.
    """

    def test_main_calls_parsed_function(self):
        """Test that main() extracts and calls the function from parsed args."""
        mock_func = mock.Mock()
        mock_args = argparse.Namespace(func=mock_func, name="test-ep", config_dir=None)

        with mock.patch.object(
            cli.root_parser, "parse_args", return_value=mock_args
        ):
            cli.main()
            mock_func.assert_called_once_with(name="test-ep", config_dir=None)

    def test_main_passes_all_args_except_func(self):
        """Test that main() passes all parsed arguments except 'func' to the called function."""
        mock_func = mock.Mock()
        mock_args = argparse.Namespace(
            func=mock_func,
            name="test-endpoint",
            config_dir="/custom/path",
            some_other_arg="value",
        )

        with mock.patch.object(
            cli.root_parser, "parse_args", return_value=mock_args
        ):
            cli.main()
            mock_func.assert_called_once_with(
                name="test-endpoint",
                config_dir="/custom/path",
                some_other_arg="value",
            )

    def test_main_with_no_func_raises_error(self):
        """Test that main() raises KeyError when no subcommand is provided."""
        mock_args = argparse.Namespace()  # Empty namespace, no 'func' attribute

        with mock.patch.object(
            cli.root_parser, "parse_args", return_value=mock_args
        ):
            with pytest.raises(KeyError, match="func"):
                cli.main()


class TestCLIIntegration:
    """Integration-style tests that verify argument flow without executing real functions."""

    def test_argument_parsing_and_extraction(self):
        """Test that arguments are correctly parsed and would be passed to functions."""
        test_cases = [
            {
                "argv": ["chiltepin", "login"],
                "expected_func_name": "login",
                "expected_args": {},
            },
            {
                "argv": ["chiltepin", "logout"],
                "expected_func_name": "logout",
                "expected_args": {},
            },
            {
                "argv": ["chiltepin", "endpoint", "configure", "my-ep"],
                "expected_func_name": "configure",
                "expected_args": {"name": "my-ep", "config_dir": None},
            },
            {
                "argv": ["chiltepin", "endpoint", "-c", "/path", "start", "ep-name"],
                "expected_func_name": "start",
                "expected_args": {"name": "ep-name", "config_dir": "/path"},
            },
            {
                "argv": ["chiltepin", "endpoint", "list"],
                "expected_func_name": "cli_list",
                "expected_args": {"config_dir": None},
            },
        ]

        for test_case in test_cases:
            with mock.patch.object(sys, "argv", test_case["argv"]):
                args = vars(cli.root_parser.parse_args())
                func = args.pop("func")

                assert func.__name__ == test_case["expected_func_name"]
                assert args == test_case["expected_args"]

    def test_error_handling_missing_name(self):
        """Test that commands requiring a name fail without it."""
        commands = ["configure", "start", "stop", "delete"]

        for cmd in commands:
            with mock.patch.object(sys, "argv", ["chiltepin", "endpoint", cmd]):
                with pytest.raises(SystemExit):
                    cli.root_parser.parse_args()

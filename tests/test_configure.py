# SPDX-License-Identifier: Apache-2.0

"""Tests for chiltepin.configure module.

This test suite validates that YAML configurations produce the expected
Executors and Providers with correct parameters.
"""

import pathlib
import tempfile
from unittest import mock

import pytest
import yaml
from parsl.executors import GlobusComputeExecutor, HighThroughputExecutor, MPIExecutor
from parsl.launchers import (
    MpiExecLauncher,
    SimpleLauncher,
    SingleNodeLauncher,
    SrunLauncher,
)
from parsl.providers import LocalProvider, PBSProProvider, SlurmProvider

import chiltepin.configure as configure


class TestParseFile:
    """Test parse_file() function."""

    def test_parse_valid_yaml(self):
        """Test parsing a valid YAML file."""
        config_data = {
            "resource1": {
                "provider": "localhost",
                "cores_per_node": 4,
            },
            "resource2": {
                "provider": "slurm",
                "partition": "compute",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            yaml.dump(config_data, tmp)
            tmp_path = tmp.name

        try:
            result = configure.parse_file(tmp_path)
            assert result == config_data
            assert "resource1" in result
            assert result["resource1"]["cores_per_node"] == 4
        finally:
            pathlib.Path(tmp_path).unlink()

    def test_parse_invalid_yaml(self):
        """Test parsing an invalid YAML file raises an error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write("invalid: yaml: content:\n  - broken")
            tmp_path = tmp.name

        try:
            with pytest.raises(yaml.YAMLError):
                configure.parse_file(tmp_path)
        finally:
            pathlib.Path(tmp_path).unlink()

    def test_parse_empty_yaml(self):
        """Test parsing an empty YAML file returns an empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            # Write nothing (empty file)
            tmp_path = tmp.name

        try:
            result = configure.parse_file(tmp_path)
            assert result == {}
            assert isinstance(result, dict)
        finally:
            pathlib.Path(tmp_path).unlink()

    def test_parse_yaml_comments_only(self):
        """Test parsing a YAML file with only comments returns an empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write("# This is just a comment\n# Another comment\n")
            tmp_path = tmp.name

        try:
            result = configure.parse_file(tmp_path)
            assert result == {}
            assert isinstance(result, dict)
        finally:
            pathlib.Path(tmp_path).unlink()


class TestCreateProvider:
    """Test create_provider() function for all provider types."""

    def test_localhost_provider_defaults(self):
        """Test LocalProvider with default values."""
        config = {"provider": "localhost"}
        provider = configure.create_provider(config)

        assert isinstance(provider, LocalProvider)
        assert provider.init_blocks == 0
        assert provider.min_blocks == 0
        assert provider.max_blocks == 1
        assert isinstance(provider.launcher, SingleNodeLauncher)

    def test_localhost_provider_custom_values(self):
        """Test LocalProvider with custom values."""
        config = {
            "provider": "localhost",
            "init_blocks": 2,
            "min_blocks": 1,
            "max_blocks": 4,
            "environment": ["export TEST=1", "source /etc/profile"],
        }
        provider = configure.create_provider(config)

        assert isinstance(provider, LocalProvider)
        assert provider.init_blocks == 2
        assert provider.min_blocks == 1
        assert provider.max_blocks == 4
        assert "export TEST=1" in provider.worker_init
        assert "source /etc/profile" in provider.worker_init

    def test_localhost_provider_mpi_mode(self):
        """Test LocalProvider in MPI mode uses SimpleLauncher."""
        config = {"provider": "localhost", "mpi": True}
        provider = configure.create_provider(config)

        assert isinstance(provider, LocalProvider)
        assert isinstance(provider.launcher, SimpleLauncher)

    def test_slurm_provider_defaults(self):
        """Test SlurmProvider with default values."""
        config = {"provider": "slurm"}
        provider = configure.create_provider(config)

        assert isinstance(provider, SlurmProvider)
        assert provider.nodes_per_block == 1
        assert provider.init_blocks == 0
        assert provider.min_blocks == 0
        assert provider.max_blocks == 1
        assert provider.exclusive is True
        assert provider.walltime == "00:10:00"
        assert isinstance(provider.launcher, SrunLauncher)

    def test_slurm_provider_custom_values(self):
        """Test SlurmProvider with custom values."""
        config = {
            "provider": "slurm",
            "cores_per_node": 16,
            "nodes_per_block": 2,
            "init_blocks": 1,
            "min_blocks": 1,
            "max_blocks": 5,
            "exclusive": False,
            "partition": "compute",
            "queue": "high",
            "account": "proj123",
            "walltime": "02:00:00",
            "environment": ["module load gcc", "module load openmpi"],
        }
        provider = configure.create_provider(config)

        assert isinstance(provider, SlurmProvider)
        assert provider.cores_per_node == 16
        assert provider.nodes_per_block == 2
        assert provider.init_blocks == 1
        assert provider.min_blocks == 1
        assert provider.max_blocks == 5
        assert provider.exclusive is False
        assert provider.partition == "compute"
        assert provider.qos == "high"
        assert provider.account == "proj123"
        assert provider.walltime == "02:00:00"
        assert "module load gcc" in provider.worker_init

    def test_slurm_provider_mpi_mode(self):
        """Test SlurmProvider in MPI mode sets cores_per_node to None and uses SimpleLauncher."""
        config = {
            "provider": "slurm",
            "mpi": True,
            "cores_per_node": 16,
        }
        provider = configure.create_provider(config)

        assert isinstance(provider, SlurmProvider)
        assert provider.cores_per_node is None
        assert isinstance(provider.launcher, SimpleLauncher)

    def test_pbspro_provider_defaults(self):
        """Test PBSProProvider with default values."""
        config = {"provider": "pbspro"}
        provider = configure.create_provider(config)

        assert isinstance(provider, PBSProProvider)
        assert provider.nodes_per_block == 1
        assert provider.init_blocks == 0
        assert provider.min_blocks == 0
        assert provider.max_blocks == 1
        assert provider.walltime == "00:10:00"
        assert isinstance(provider.launcher, MpiExecLauncher)

    def test_pbspro_provider_custom_values(self):
        """Test PBSProProvider with custom values."""
        config = {
            "provider": "pbspro",
            "cores_per_node": 24,
            "nodes_per_block": 3,
            "init_blocks": 2,
            "min_blocks": 0,
            "max_blocks": 10,
            "queue": "normal",
            "account": "account456",
            "walltime": "04:00:00",
            "environment": ["source /etc/bashrc"],
        }
        provider = configure.create_provider(config)

        assert isinstance(provider, PBSProProvider)
        assert provider.cpus_per_node == 24
        assert provider.nodes_per_block == 3
        assert provider.init_blocks == 2
        assert provider.max_blocks == 10
        assert provider.queue == "normal"
        assert provider.account == "account456"
        assert provider.walltime == "04:00:00"
        assert "source /etc/bashrc" in provider.worker_init

    def test_pbspro_provider_mpi_mode(self):
        """Test PBSProProvider in MPI mode."""
        config = {
            "provider": "pbspro",
            "mpi": True,
            "cores_per_node": 24,
        }
        provider = configure.create_provider(config)

        assert isinstance(provider, PBSProProvider)
        assert provider.cpus_per_node is None
        assert isinstance(provider.launcher, SimpleLauncher)

    def test_unsupported_provider(self):
        """Test that unsupported provider raises ValueError."""
        config = {"provider": "unsupported_provider"}

        with pytest.raises(ValueError, match="Unsupported provider"):
            configure.create_provider(config)

    def test_default_provider_is_localhost(self):
        """Test that default provider is localhost when not specified."""
        config = {}
        provider = configure.create_provider(config)

        assert isinstance(provider, LocalProvider)


class TestCreateHTEXExecutor:
    """Test create_htex_executor() function."""

    def test_htex_basic(self):
        """Test creating basic HighThroughputExecutor."""
        config = {"provider": "localhost"}
        executor = configure.create_htex_executor("test-htex", config)

        assert isinstance(executor, HighThroughputExecutor)
        assert executor.label == "test-htex"
        assert executor.cores_per_worker == 1
        assert isinstance(executor.provider, LocalProvider)

    def test_htex_custom_workers(self):
        """Test HTEX with custom worker configuration."""
        config = {
            "provider": "localhost",
            "cores_per_worker": 4,
            "max_workers_per_node": 8,
        }
        executor = configure.create_htex_executor("test-workers", config)

        assert executor.cores_per_worker == 4
        assert executor.max_workers_per_node == 8

    def test_htex_with_slurm_provider(self):
        """Test HTEX with SlurmProvider."""
        config = {
            "provider": "slurm",
            "partition": "compute",
            "account": "test-account",
        }
        executor = configure.create_htex_executor("slurm-htex", config)

        assert isinstance(executor, HighThroughputExecutor)
        assert isinstance(executor.provider, SlurmProvider)
        assert executor.provider.partition == "compute"


class TestCreateMPIExecutor:
    """Test create_mpi_executor() function."""

    def test_mpi_executor_basic(self):
        """Test creating basic MPIExecutor."""
        config = {"provider": "localhost", "mpi": True}
        executor = configure.create_mpi_executor("test-mpi", config)

        assert isinstance(executor, MPIExecutor)
        assert executor.label == "test-mpi"
        assert executor.mpi_launcher == "mpiexec"
        assert executor.max_workers_per_block == 1
        assert isinstance(executor.provider, LocalProvider)

    def test_mpi_executor_with_slurm(self):
        """Test MPIExecutor defaults to srun launcher for Slurm."""
        config = {"provider": "slurm", "mpi": True}
        executor = configure.create_mpi_executor("slurm-mpi", config)

        assert executor.mpi_launcher == "srun"
        assert isinstance(executor.provider, SlurmProvider)

    def test_mpi_executor_with_pbspro(self):
        """Test MPIExecutor defaults to mpiexec launcher for PBSPro."""
        config = {"provider": "pbspro", "mpi": True}
        executor = configure.create_mpi_executor("pbspro-mpi", config)

        assert executor.mpi_launcher == "mpiexec"
        assert isinstance(executor.provider, PBSProProvider)

    def test_mpi_executor_custom_launcher(self):
        """Test MPIExecutor with custom launcher."""
        config = {
            "provider": "pbspro",
            "mpi": True,
            "mpi_launcher": "aprun",
        }
        executor = configure.create_mpi_executor("custom-mpi", config)

        assert executor.mpi_launcher == "aprun"

    def test_mpi_executor_max_apps(self):
        """Test MPIExecutor with max_mpi_apps setting."""
        config = {
            "provider": "localhost",
            "mpi": True,
            "max_mpi_apps": 4,
        }
        executor = configure.create_mpi_executor("multi-mpi", config)

        assert executor.max_workers_per_block == 4


class TestCreateGlobusComputeExecutor:
    """Test create_globus_compute_executor() function."""

    def test_globus_compute_executor_basic(self):
        """Test creating basic GlobusComputeExecutor."""
        config = {
            "endpoint": "12345678-1234-5678-1234-567812345678",
            "provider": "localhost",
        }
        executor = configure.create_globus_compute_executor("gc-test", config)

        assert isinstance(executor, GlobusComputeExecutor)
        assert executor.label == "gc-test"

        # Verify user_endpoint_config has correct defaults
        uec = executor.executor.user_endpoint_config
        assert uec["provider"] == "localhost"
        assert uec["mpi"] is False
        assert uec["max_mpi_apps"] == 1
        assert uec["mpi_launcher"] == "mpiexec"
        assert uec["cores_per_node"] == 1
        assert uec["nodes_per_block"] == 1
        assert uec["init_blocks"] == 0
        assert uec["min_blocks"] == 0
        assert uec["max_blocks"] == 1
        assert uec["exclusive"] is True
        assert uec["partition"] == ""
        assert uec["queue"] == ""
        assert uec["account"] == ""
        assert uec["walltime"] == "00:10:00"
        assert uec["worker_init"] == ""

    def test_globus_compute_executor_with_client(self):
        """Test GlobusComputeExecutor with custom client."""
        mock_client = mock.Mock()
        config = {
            "endpoint": "12345678-1234-5678-1234-567812345678",
            "provider": "localhost",
        }
        executor = configure.create_globus_compute_executor(
            "gc-with-client", config, client=mock_client
        )

        assert isinstance(executor, GlobusComputeExecutor)

        # Verify user_endpoint_config is set correctly
        uec = executor.executor.user_endpoint_config
        assert uec["provider"] == "localhost"
        assert uec["mpi"] is False

    def test_globus_compute_executor_mpi_config(self):
        """Test GlobusComputeExecutor with MPI configuration."""
        config = {
            "endpoint": "87654321-4321-8765-4321-876543218765",
            "provider": "slurm",
            "mpi": True,
            "max_mpi_apps": 3,
            "mpi_launcher": "srun",
            "cores_per_node": 48,
            "nodes_per_block": 2,
        }
        executor = configure.create_globus_compute_executor("gc-mpi", config)

        assert isinstance(executor, GlobusComputeExecutor)
        assert executor.label == "gc-mpi"

        # Verify user_endpoint_config has correct MPI settings
        uec = executor.executor.user_endpoint_config
        assert uec["provider"] == "slurm"
        assert uec["mpi"] is True
        assert uec["max_mpi_apps"] == 3
        assert uec["mpi_launcher"] == "srun"
        assert uec["cores_per_node"] == 48
        assert uec["nodes_per_block"] == 2

    def test_globus_compute_executor_full_config(self):
        """Test GlobusComputeExecutor with complete configuration."""
        config = {
            "endpoint": "abcdef12-3456-7890-abcd-ef1234567890",
            "provider": "slurm",
            "cores_per_node": 64,
            "nodes_per_block": 4,
            "init_blocks": 1,
            "min_blocks": 0,
            "max_blocks": 8,
            "exclusive": True,
            "partition": "gpu",
            "queue": "high",
            "account": "proj999",
            "walltime": "06:00:00",
            "environment": ["module load cuda"],
        }
        executor = configure.create_globus_compute_executor("gc-full", config)

        assert isinstance(executor, GlobusComputeExecutor)

        # Verify user_endpoint_config has all custom values
        uec = executor.executor.user_endpoint_config
        assert uec["provider"] == "slurm"
        assert uec["cores_per_node"] == 64
        assert uec["nodes_per_block"] == 4
        assert uec["init_blocks"] == 1
        assert uec["min_blocks"] == 0
        assert uec["max_blocks"] == 8
        assert uec["exclusive"] is True
        assert uec["partition"] == "gpu"
        assert uec["queue"] == "high"
        assert uec["account"] == "proj999"
        assert uec["walltime"] == "06:00:00"
        assert uec["worker_init"] == "module load cuda"
        assert uec["mpi"] is False  # Default
        assert uec["mpi_launcher"] == "srun"  # Default for slurm


class TestCreateExecutor:
    """Test create_executor() dispatcher function."""

    def test_create_executor_globus_compute(self):
        """Test create_executor returns GlobusComputeExecutor when endpoint is specified."""
        config = {
            "endpoint": "11111111-2222-3333-4444-555555555555",
            "provider": "localhost",
        }
        executor = configure.create_executor("test", config)

        assert isinstance(executor, GlobusComputeExecutor)

    def test_create_executor_mpi(self):
        """Test create_executor returns MPIExecutor when mpi=True and no endpoint."""
        config = {
            "provider": "slurm",
            "mpi": True,
        }
        executor = configure.create_executor("test-mpi", config)

        assert isinstance(executor, MPIExecutor)

    def test_create_executor_htex(self):
        """Test create_executor returns HTEX when mpi=False and no endpoint."""
        config = {
            "provider": "localhost",
            "mpi": False,
        }
        executor = configure.create_executor("test-htex", config)

        assert isinstance(executor, HighThroughputExecutor)

    def test_create_executor_htex_default(self):
        """Test create_executor returns HTEX by default."""
        config = {"provider": "localhost"}
        executor = configure.create_executor("test-default", config)

        assert isinstance(executor, HighThroughputExecutor)


class TestLoad:
    """Test load() configuration function."""

    def test_load_empty_config(self):
        """Test load with empty config creates default local executor."""
        config = configure.load({})

        assert len(config.executors) == 1
        assert config.executors[0].label == "local"
        assert isinstance(config.executors[0], HighThroughputExecutor)
        assert isinstance(config.executors[0].provider, LocalProvider)

    def test_load_single_resource(self):
        """Test load with single resource configuration."""
        resources = {
            "compute": {
                "provider": "slurm",
                "partition": "compute",
            }
        }
        config = configure.load(resources)

        # Should have local + compute
        assert len(config.executors) == 2
        labels = [ex.label for ex in config.executors]
        assert "local" in labels
        assert "compute" in labels

    def test_load_multiple_resources(self):
        """Test load with multiple resource configurations."""
        resources = {
            "compute": {
                "provider": "slurm",
                "partition": "compute",
            },
            "mpi": {
                "provider": "slurm",
                "mpi": True,
                "partition": "compute",
            },
            "service": {
                "provider": "slurm",
                "partition": "service",
                "exclusive": False,
            },
        }
        config = configure.load(resources)

        # Should have local + 3 resources
        assert len(config.executors) == 4
        labels = [ex.label for ex in config.executors]
        assert "local" in labels
        assert "compute" in labels
        assert "mpi" in labels
        assert "service" in labels

    def test_load_with_include_filter(self):
        """Test load with include parameter filters resources."""
        resources = {
            "compute": {"provider": "slurm", "partition": "compute"},
            "mpi": {"provider": "slurm", "mpi": True},
            "service": {"provider": "slurm", "partition": "service"},
        }
        config = configure.load(resources, include=["compute", "mpi"])

        # Should have local + compute + mpi (not service)
        assert len(config.executors) == 3
        labels = [ex.label for ex in config.executors]
        assert "local" in labels
        assert "compute" in labels
        assert "mpi" in labels
        assert "service" not in labels

    def test_load_with_include_nonexistent(self):
        """Test load with include containing non-existent resources raises RuntimeError."""
        resources = {
            "compute": {"provider": "slurm"},
        }

        with pytest.raises(
            RuntimeError,
            match="Resources specified in include list not found in config",
        ):
            configure.load(resources, include=["compute", "nonexistent"])

    def test_load_with_run_dir(self):
        """Test load with custom run_dir."""
        custom_dir = "/tmp/test_run_dir"
        config = configure.load({}, run_dir=custom_dir)

        assert config.run_dir == custom_dir

    def test_load_mixed_executor_types(self):
        """Test load with mixed executor types."""
        resources = {
            "htex": {
                "provider": "localhost",
                "cores_per_worker": 2,
            },
            "mpi": {
                "provider": "slurm",
                "mpi": True,
                "mpi_launcher": "srun",
            },
            "globus": {
                "endpoint": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "provider": "pbspro",
            },
        }
        config = configure.load(resources)

        assert len(config.executors) == 4
        executor_types = [type(ex).__name__ for ex in config.executors]
        assert "HighThroughputExecutor" in executor_types
        assert "MPIExecutor" in executor_types
        assert "GlobusComputeExecutor" in executor_types

    def test_load_with_client(self):
        """Test load with Globus Compute client."""
        mock_client = mock.Mock()
        resources = {
            "gc-resource": {
                "endpoint": "99999999-8888-7777-6666-555555555555",
                "provider": "localhost",
            }
        }
        config = configure.load(resources, client=mock_client)

        # Should successfully create config with GC executor
        assert len(config.executors) == 2
        gc_executors = [
            ex for ex in config.executors if isinstance(ex, GlobusComputeExecutor)
        ]
        assert len(gc_executors) == 1


class TestIntegrationScenarios:
    """Integration tests for realistic configuration scenarios."""

    def test_typical_hpc_cluster_config(self):
        """Test typical HPC cluster configuration with multiple partitions."""
        resources = {
            "service": {
                "provider": "slurm",
                "cores_per_node": 1,
                "nodes_per_block": 1,
                "exclusive": False,
                "partition": "service",
                "account": "test-proj",
                "walltime": "01:00:00",
            },
            "compute": {
                "provider": "slurm",
                "cores_per_node": 48,
                "nodes_per_block": 1,
                "exclusive": True,
                "partition": "compute",
                "account": "test-proj",
                "walltime": "04:00:00",
            },
            "mpi": {
                "provider": "slurm",
                "mpi": True,
                "cores_per_node": 48,
                "nodes_per_block": 4,
                "max_mpi_apps": 2,
                "exclusive": True,
                "partition": "compute",
                "account": "test-proj",
                "walltime": "08:00:00",
            },
        }
        config = configure.load(resources)

        assert len(config.executors) == 4

        # Verify service partition executor
        service_ex = [ex for ex in config.executors if ex.label == "service"][0]
        assert isinstance(service_ex, HighThroughputExecutor)
        assert service_ex.provider.exclusive is False

        # Verify compute partition executor
        compute_ex = [ex for ex in config.executors if ex.label == "compute"][0]
        assert isinstance(compute_ex, HighThroughputExecutor)
        assert compute_ex.provider.cores_per_node == 48

        # Verify MPI executor
        mpi_ex = [ex for ex in config.executors if ex.label == "mpi"][0]
        assert isinstance(mpi_ex, MPIExecutor)
        assert mpi_ex.provider.nodes_per_block == 4

    def test_hybrid_globus_compute_local_config(self):
        """Test configuration mixing Globus Compute and local resources."""
        resources = {
            "local-compute": {
                "provider": "localhost",
                "cores_per_worker": 4,
                "max_workers_per_node": 8,
            },
            "remote-hpc": {
                "endpoint": "fedcba98-7654-3210-fedc-ba9876543210",
                "provider": "slurm",
                "partition": "gpu",
                "cores_per_node": 64,
                "nodes_per_block": 2,
            },
        }
        config = configure.load(resources)

        assert len(config.executors) == 3

        # Check for HTEX executors (local + local-compute)
        htex_executors = [
            ex for ex in config.executors if isinstance(ex, HighThroughputExecutor)
        ]
        assert len(htex_executors) == 2

        # Check for GlobusCompute executor
        gc_executors = [
            ex for ex in config.executors if isinstance(ex, GlobusComputeExecutor)
        ]
        assert len(gc_executors) == 1

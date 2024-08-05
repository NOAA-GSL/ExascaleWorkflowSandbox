import argparse
import os
from datetime import date, timedelta
from pathlib import Path
from shutil import copy

import parsl
import pytest
import uwtools.api.config as uwconfig

import chiltepin.configure
from chiltepin.metis.wrapper import Metis
from chiltepin.mpas.limited_area.wrapper import LimitedArea
from chiltepin.mpas.wrapper import MPAS
from chiltepin.utils.chiltepin_get_data import retrieve_data
from chiltepin.wps.wrapper import WPS
from chiltepin.wrf.wrapper import WRF


def main(user_config_file: Path) -> None:

    # Set up the experiment
    mpas_app = Path(os.path.dirname(__file__)).parent.absolute()
    experiment_config = uwconfig.get_yaml_config(Path("./default_config.yaml"))
    user_config = uwconfig.get_yaml_config(user_config_file)
    machine = user_config["user"]["platform"]

    experiment_config.update_values(user_config)

    experiment_config["user"]["mpas_app"] = mpas_app.as_posix()
    experiment_config.dereference()

    # Build the experiment directory
    experiment_path = Path(experiment_config["user"]["experiment_dir"])
    os.makedirs(experiment_path, exist_ok=True)

    experiment_file = experiment_path / "experiment.yaml"

    # Create experiment yaml
    uwconfig.realize(
        input_config=experiment_config,
        output_file=experiment_file,
        update_config=user_config,
    )

    # Load Parsl resource configs
    resource_config_file = mpas_app / "parm" / "resources.yaml"
    resource_config = chiltepin.configure.parse_file(resource_config_file)
    resources, environments = chiltepin.configure.factory(resource_config, machine)
    environment = environments[machine]
    with parsl.load(resources):

        # Instantiate LimitedArea object
        limited_area = LimitedArea(
            environment=environment,
            install_path=experiment_path,
            tag="2.1",
        )

        # Instantiate Metis object
        metis = Metis(
            environment=environment,
            install_path=experiment_path,
            tag="5.2.1",
        )

        # Instantiate WPS object
        wps = WPS(
            environment=environment,
            install_path=experiment_path,
            tag="4.5",
        )

        # Instantiate MPAS object
        mpas = MPAS(
            environment=environment,
            install_path=experiment_path,
            tag="cbba5a4",
        )

        # Intall Limited Area
        install_limited_area = limited_area.install(
            stdout=experiment_path / "install_limited_area.out",
            stderr=experiment_path / "install_limited_area.err",
        )

        # Intall Metis
        install_metis = metis.install(
            stdout=experiment_path / "install_metis.out",
            stderr=experiment_path / "install_metis.err",
        )

        # Intall WPS
        install_wps = wps.install(
            stdout=experiment_path / "install_wps.out",
            stderr=experiment_path / "install_wps.err",
            WRF_dir=None,
        )

        # Install MPAS
        install_mpas = mpas.install(
            stdout=experiment_path / "install_mpas.out",
            stderr=experiment_path / "install_mpas.err",
        )

        # Generate mesh
        create_region = limited_area.create_region(
            resolution=120,
            region="conus",
            stdout=experiment_path / "create_region.out",
            stderr=experiment_path / "create_region.err",
            install=limited_area,
        ).result()

        # Create the grid files
        mesh_file_name = f"{experiment_config['user']['mesh_label']}.graph.info"
        mesh_file_path = Path(experiment_config["data"]["mesh_files"]) / mesh_file_name
        all_nprocs = (
            experiment_config[sect][driver]["execution"]["batchargs"]["cores"]
            for sect, driver in (
                ("create_ics", "mpas_init"),
                ("create_lbcs", "mpas_init"),
                ("forecast", "mpas"),
            )
        )
        for nprocs in all_nprocs:
            if not (experiment_path / f"{mesh_file_path.name}.part.{nprocs}").is_file():
                print(f"Creating grid file for {nprocs} procs")
                gpm = metis.gpmetis(
                    mesh_file_path,
                    nprocs,
                    stdout=experiment_path / f"gpmetis_{nprocs}.out",
                    stderr=experiment_path / f"gpmetis_{nprocs}.err",
                    install=install_metis,
                )

        # Run the experiment cycles
        cycle = experiment_config["user"]["first_cycle"]
        while cycle <= experiment_config["user"]["last_cycle"]:

            # Create string representations of the cycle
            yyyymmddhh = cycle.strftime("%Y%m%d%H")
            cycle_iso = cycle.strftime("%Y-%m-%dT%H:%M:%S")

            # Resolve config for this cycle
            experiment_config.dereference(context={"cycle": cycle, **experiment_config})

            # Get the ics data
            get_ics_data_config = experiment_config["get_ics_data"]
            get_ics_dir = Path(get_ics_data_config["run_dir"])
            get_ics_data = retrieve_data(
                stdout=experiment_path / f"get_ics_{yyyymmddhh}.out",
                stderr=experiment_path / f"get_ics_{yyyymmddhh}.err",
                ics_or_lbcs="ICS",
                time_offset_hrs=0,
                fcst_len=24,
                lbc_intvl_hrs=6,
                yyyymmddhh=yyyymmddhh,
                output_path=get_ics_dir,
            )

            # Get the lbcs data
            get_lbcs_data_config = experiment_config["get_lbcs_data"]
            get_lbcs_dir = Path(get_lbcs_data_config["run_dir"])
            get_lbcs_data = retrieve_data(
                stdout=experiment_path / f"get_lbcs_{yyyymmddhh}.out",
                stderr=experiment_path / f"get_lbcs_{yyyymmddhh}.err",
                ics_or_lbcs="LBCS",
                time_offset_hrs=0,
                fcst_len=24,
                lbc_intvl_hrs=6,
                yyyymmddhh=yyyymmddhh,
                output_path=get_lbcs_dir,
            )

            # Wait for the data to be retrieved
            get_ics_data.result()
            get_lbcs_data.result()

            # Run ungrib
            ungrib = wps.ungrib(
                experiment_file,
                cycle_iso,
                stdout=experiment_path / f"ungrib_{yyyymmddhh}.out",
                stderr=experiment_path / f"ungrib_{yyyymmddhh}.err",
                install=install_wps,
            )

            # Wait for ungrib to complete
            ungrib.result()

            # Create initial conditions
            mpas_init_ics = mpas.mpas_init(
                experiment_file,
                cycle_iso,
                "create_ics",
                stdout=experiment_path / f"mpas_init_ics_{yyyymmddhh}.out",
                stderr=experiment_path / f"mpas_init_ics_{yyyymmddhh}.err",
                install=install_mpas,
            )

            # Wait for initial conditions
            mpas_init_ics.result()

            # Create lateral boundary conditions
            mpas_init_lbcs = mpas.mpas_init(
                experiment_file,
                cycle_iso,
                "create_lbcs",
                stdout=experiment_path / f"mpas_init_lbcs_{yyyymmddhh}.out",
                stderr=experiment_path / f"mpas_init_lbcs_{yyyymmddhh}.err",
                install=install_mpas,
            )

            # Wait for lateral boundary conditions
            mpas_init_lbcs.result()

            # Run the forecast
            mpas_forecast = mpas.mpas_forecast(
                experiment_file,
                cycle_iso,
                "forecast",
                stdout=experiment_path / f"mpas_forecast_{yyyymmddhh}.out",
                stderr=experiment_path / f"mpas_forecast_{yyyymmddhh}.err",
                install=install_mpas,
            )

            # Wait for the forecast
            mpas_forecast.result()

            # Increment experiment cycle
            cycle += timedelta(hours=experiment_config["user"]["cycle_frequency"])

    # Clean up resources
    parsl.clear()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Configure an experiment with the following input:"
    )
    parser.add_argument("user_config_file", help="Path to the user config file.")
    args = parser.parse_args()
    main(user_config_file=Path(args.user_config_file))

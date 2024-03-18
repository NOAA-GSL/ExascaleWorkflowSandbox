import textwrap
from datetime import datetime, timedelta

import yaml

from chiltepin.jedi import leadtime
from chiltepin.jedi.qg import forecast, hofx, install, variational
from chiltepin.jedi.qg.config import (forecast_default, make_obs3d_default,
                                      merge_config_str, var3d_default)


class Experiment:

    def __init__(self, config):
        # Parse the experiment configuration
        config_yaml = yaml.safe_load(config)
        self.config = config_yaml

    def install_jedi(self, environment):
        jedi_path = self.config["jedi"]["install path"]
        jedi_tag = self.config["jedi"]["tag"]
        log_path = f"{self.config['experiment']['path']}/log"
        jedi = install.run(
            environment,
            install_path=jedi_path,
            tag=jedi_tag,
            stdout=f"{log_path}/install_jedi.out",
            stderr=f"{log_path}/install_jedi.err",
        )
        return jedi

    def _make_truth_config(self):
        exp_length = leadtime.fcst_to_seconds(self.config["experiment"]["length"])
        exp_freq = leadtime.fcst_to_seconds(self.config["experiment"]["frequency"])
        forecast_length = leadtime.seconds_to_fcst(exp_length + exp_freq)
        nx = self.config["truth"]["nx"]
        ny = self.config["truth"]["ny"]
        init_date = self.config["experiment"]["begin"]
        dt = self.config["truth"]["tstep"]
        truth_path = f"{self.config['experiment']['path']}/truth"
        truth_config = forecast_default()
        merge_config_str(
            truth_config,
            textwrap.dedent(
                f"""
        forecast length: {forecast_length}
        geometry:
          nx: {nx}
          ny: {ny}
        initial condition:
          date: "{init_date}"
          read_from_file: 0
        model:
          tstep: {dt}
        output:
          exp: truth
          date: "{init_date}"
          datadir: {truth_path}
        """
            ).strip(),
        )
        return truth_config

    def make_truth(self, environment, install):
        jedi_path = self.config["jedi"]["install path"]
        jedi_tag = self.config["jedi"]["tag"]
        truth_path = f"{self.config['experiment']['path']}/truth"
        log_path = f"{self.config['experiment']['path']}/log"
        truth = forecast.run(
            environment,
            install_path=jedi_path,
            tag=jedi_tag,
            rundir=truth_path,
            config=self._make_truth_config(),
            stdout=f"{log_path}/truth.out",
            stderr=f"{log_path}/truth.err",
            install=install,
        )
        return truth

    def _make_obs_config(self, t):
        t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        exp_begin_str = self.config["experiment"]["begin"]
        exp_begin = datetime.strptime(exp_begin_str, "%Y-%m-%dT%H:%M:%SZ")
        nx = self.config["truth"]["nx"]
        ny = self.config["truth"]["ny"]
        dt = self.config["truth"]["tstep"]
        window_begin = t + timedelta(
            0, leadtime.fcst_to_seconds(self.config["assimilation"]["window"]["begin"])
        )
        window_begin_str = window_begin.strftime("%Y-%m-%dT%H:%M:%SZ")
        window_length = self.config["assimilation"]["window"]["length"]
        truth_leadtime = leadtime.seconds_to_fcst(
            int((window_begin - exp_begin).total_seconds())
        )
        truth_path = f"{self.config['experiment']['path']}/truth"
        obs_path = f"{self.config['experiment']['path']}/forecast/{t_str}"
        stream_begin = self.config["obs"]["stream"]["begin"]
        stream_period = self.config["obs"]["stream"]["period"]
        wind_begin = self.config["obs"]["wind"]["begin"]
        wind_period = self.config["obs"]["wind"]["period"]
        wspeed_begin = self.config["obs"]["wspeed"]["begin"]
        wspeed_period = self.config["obs"]["wspeed"]["period"]
        make_obs_config = make_obs3d_default()
        merge_config_str(
            make_obs_config,
            textwrap.dedent(
                f"""
        geometry:
          nx: {nx}
          ny: {ny}
        initial condition:
          date: "{window_begin_str}"
          filename: {truth_path}/truth.fc.{exp_begin_str}.{truth_leadtime}.nc
        model:
          tstep: {dt}
        forecast length: {window_length}
        time window:
          begin: "{window_begin_str}"
          length: {window_length}
        """
            ).strip(),
        )
        for observer in make_obs_config["observations"]["observers"]:
            obsfile = f"{obs_path}/qg.truth.3d.{t_str}.nc"
            observer["obs space"]["obsdataout"]["obsfile"] = obsfile
            obs_type = observer["obs operator"]["obs type"]
            generate = observer["obs space"]["generate"]
            if obs_type == "Stream":
                generate["begin"] = stream_begin
                generate["obs period"] = stream_period
            elif obs_type == "Wind":
                generate["begin"] = wind_begin
                generate["obs period"] = wind_period
            elif obs_type == "WSpeed":
                generate["begin"] = wspeed_begin
                generate["obs period"] = wspeed_period
        return make_obs_config

    def make_obs(self, environment, t, truth):
        t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        jedi_path = self.config["jedi"]["install path"]
        jedi_tag = self.config["jedi"]["tag"]
        obs_path = f"{self.config['experiment']['path']}/forecast/{t_str}"
        log_path = f"{self.config['experiment']['path']}/log"
        obs = hofx.makeobs3d(
            environment,
            install_path=jedi_path,
            tag=jedi_tag,
            rundir=obs_path,
            config=self._make_obs_config(t),
            stdout=f"{log_path}/makeobs.{t_str}.out",
            stderr=f"{log_path}/makeobs.{t_str}.err",
            truth=truth,
        )
        return obs

    def _make_forecast_config(self, t):
        t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        exp_begin_str = self.config["experiment"]["begin"]
        fcst_length = self.config["forecast"]["length"]
        fcst_freq = self.config["forecast"]["frequency"]
        nx = self.config["forecast"]["nx"]
        ny = self.config["forecast"]["ny"]
        dt = self.config["forecast"]["tstep"]
        fcst_path = f"{self.config['experiment']['path']}/forecast/{t_str}"
        if t_str == exp_begin_str:
            read_from_file = 0
            analysis_file = "None"
        else:
            read_from_file = 1
            # These commented lines needed for cycling without DA from a prev cycle fcst
            # exp_freq = self.config['experiment']['frequency']
            # prev_cycle = t - timedelta(0, leadtime.fcst_to_seconds(exp_freq))
            # prev_cycle_str = prev_cycle.strftime("%Y-%m-%dT%H:%M:%SZ")
            # prev_cycle_path = f"{self.config['experiment']['path']}/forecast/{prev_cycle_str}"
            analysis_file = f"{fcst_path}/3dvar.an.{t_str}.nc"
        fcst_config = forecast_default()
        merge_config_str(
            fcst_config,
            textwrap.dedent(
                f"""
        forecast length: {fcst_length}
        geometry:
          nx: {nx}
          ny: {ny}
        initial condition:
          date: "{t_str}"
          filename: {analysis_file}
          read_from_file: {read_from_file}
        model:
          tstep: {dt}
        output:
          exp: forecast
          date: "{t_str}"
          frequency: {fcst_freq}
          datadir: {fcst_path}
        """
            ).strip(),
        )
        return fcst_config

    def run_forecast(self, environment, t, install=None, analysis=None):
        t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        jedi_path = self.config["jedi"]["install path"]
        jedi_tag = self.config["jedi"]["tag"]
        fcst_path = f"{self.config['experiment']['path']}/forecast/{t_str}"
        log_path = f"{self.config['experiment']['path']}/log"
        fcst = forecast.run(
            environment,
            install_path=jedi_path,
            tag=jedi_tag,
            rundir=fcst_path,
            config=self._make_forecast_config(t),
            stdout=f"{log_path}/forecast.{t_str}.out",
            stderr=f"{log_path}/forecast.{t_str}.err",
            install=install,
            analysis=analysis,
        )
        return fcst

    def _make_3dvar_config(self, t):
        t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        exp_freq = self.config["experiment"]["frequency"]
        nx = self.config["forecast"]["nx"]
        ny = self.config["forecast"]["ny"]
        window_begin = t + timedelta(
            0, leadtime.fcst_to_seconds(self.config["assimilation"]["window"]["begin"])
        )
        window_begin_str = window_begin.strftime("%Y-%m-%dT%H:%M:%SZ")
        window_length = self.config["assimilation"]["window"]["length"]
        bkg_offset = (
            leadtime.fcst_to_seconds(self.config["assimilation"]["window"]["begin"])
            + leadtime.fcst_to_seconds(self.config["experiment"]["frequency"])
            + (leadtime.fcst_to_seconds(window_length) // 2)
        )
        bkg_date = (
            t
            - timedelta(
                0, leadtime.fcst_to_seconds(self.config["experiment"]["frequency"])
            )
            + timedelta(0, bkg_offset)
        )
        bkg_date_str = bkg_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        prev_cycle = t - timedelta(0, leadtime.fcst_to_seconds(exp_freq))
        prev_cycle_str = prev_cycle.strftime("%Y-%m-%dT%H:%M:%SZ")
        prev_cycle_path = (
            f"{self.config['experiment']['path']}/forecast/{prev_cycle_str}"
        )
        var3d_path = f"{self.config['experiment']['path']}/forecast/{t_str}"
        var3d_config = var3d_default()
        merge_config_str(
            var3d_config,
            textwrap.dedent(
                f"""
        cost function:
          cost type: 3D-Var
          time window:
            begin: "{window_begin_str}"
            length: {window_length}
          geometry:
            nx: {nx}
            ny: {ny}
          background:
            date: "{bkg_date_str}"
            filename: {prev_cycle_path}/forecast.fc.{prev_cycle_str}.{leadtime.seconds_to_fcst(bkg_offset)}.nc
        output:
          datadir: {var3d_path}
        final:
          increment:
            geometry:
              nx: {nx}
              ny: {ny}
            output:
              state component:
                datadir: {var3d_path}
                date: {t_str}
        """
            ).strip(),
        )
        for observer in var3d_config["cost function"]["observations"]["observers"]:
            obsinfile = f"{var3d_path}/qg.truth.3d.{t_str}.nc"
            obsoutfile = f"{var3d_path}/qg.3d.{t_str}.nc"
            observer["obs space"]["obsdatain"]["obsfile"] = obsinfile
            observer["obs space"]["obsdataout"]["obsfile"] = obsoutfile
        for iteration in var3d_config["variational"]["iterations"]:
            iteration["geometry"]["nx"] = nx
            iteration["geometry"]["ny"] = ny
            iteration["online diagnostics"]["increment"]["state component"][
                "datadir"
            ] = var3d_path
            iteration["online diagnostics"]["increment"]["state component"][
                "date"
            ] = var3d_path

        return var3d_config

    def run_3dvar(self, environment, t, obs, background):
        t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        jedi_path = self.config["jedi"]["install path"]
        jedi_tag = self.config["jedi"]["tag"]
        var3d_path = f"{self.config['experiment']['path']}/forecast/{t_str}"
        log_path = f"{self.config['experiment']['path']}/log"
        var3d = variational.run_3dvar(
            environment,
            install_path=jedi_path,
            tag=jedi_tag,
            rundir=var3d_path,
            config=self._make_3dvar_config(t),
            stdout=f"{log_path}/var3d.{t_str}.out",
            stderr=f"{log_path}/var3d.{t_str}.err",
            obs=obs,
            background=background,
        )
        return var3d

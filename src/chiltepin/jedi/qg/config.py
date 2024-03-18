import textwrap
import yaml


def merge_config_dict(d1, d2):
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            merge_config_dict(d1[key], value)
        else:
            d1[key] = value


def merge_config_str(d1, s1):
    d2 = yaml.safe_load(s1.strip())
    merge_config_dict(d1, d2)


def forecast_default():
    return yaml.safe_load(textwrap.dedent("""
    forecast length: P2D
    geometry:
      nx: 40
      ny: 20
      depths: [4500.0, 5500.0]
    initial condition:
      date: "2009-12-31T00:00:00Z"
      filename: None
      read_from_file: 0
    model:
      name: QG
      tstep: PT10M
    output:
      datadir: None
      date: "2009-12-31T00:00:00Z"
      exp: forecast
      frequency: PT1H
      type: fc
    prints:
      frequency: PT3H
    """).strip())


def make_obs3d_default():
    return yaml.safe_load(textwrap.dedent("""
    geometry:
      nx: 40
      ny: 20
      depths: [4500.0, 5500.0]
    initial condition:
      date: "2010-01-01T00:00:00Z"
      filename: Data/truth.fc.2009-12-15T00:00:00Z.P17D.nc
    model:
      name: QG
      tstep: PT1H
    forecast length: PT15H
    time window:
      begin: "2010-01-01T00:00:00Z"
      length: PT15H
    observations:
      observers:
      - obs operator:
          obs type: Stream
        obs space:
          obsdataout:
            obsfile: Data/truth.obs3d.nc
          obs type: Stream
          generate:
            begin: PT10H
            nval: 1
            obs density: 100
            obs error: 4.0e6
            obs period: PT1H
      - obs operator:
          obs type: Wind
        obs space:
          obsdataout:
            obsfile: Data/truth.obs3d.nc
          obs type: Wind
          generate:
            begin: PT11H
            nval: 2
            obs density: 100
            obs error: 6.0
            obs period: PT2H
      - obs operator:
          obs type: WSpeed
        obs space:
          obsdataout:
            obsfile: Data/truth.obs3d.nc
          obs type: WSpeed
          generate:
            begin: PT10H
            nval: 1
            obs density: 100
            obs error: 12.0
            obs period: PT2H
    make obs: true
    """).strip())


def var3d_default():
    return yaml.safe_load(textwrap.dedent("""
    cost function:
      cost type: 3D-Var
      time window:
        begin: 2010-01-01T09:00:00Z
        length: PT6H
      analysis variables: [x]
      geometry:
        nx: 40
        ny: 20
        depths: [4500.0, 5500.0]
      background:
        date: 2010-01-01T12:00:00Z
        filename: Data/forecast.fc.2009-12-31T00:00:00Z.P1DT12H.nc
      background error:
        covariance model: QgError
        horizontal_length_scale: 2.2e6
        maximum_condition_number: 1.0e6
        standard_deviation: 1.8e7
        vertical_length_scale: 15000.0
      observations:
        observers:
        - obs error:
            covariance model: diagonal
          obs operator:
            obs type: Stream
          obs space:
            obsdatain:
              obsfile: Data/truth.obs3d.nc
            obsdataout:
              obsfile: Data/3dvar.obs3d.nc
            obs type: Stream
        - obs error:
            covariance model: diagonal
          obs operator:
            obs type: Wind
          obs space:
            obsdatain:
              obsfile: Data/truth.obs3d.nc
            obsdataout:
              obsfile: Data/3dvar.obs3d.nc
            obs type: Wind
        - obs error:
            covariance model: diagonal
          obs operator:
            obs type: WSpeed
          obs space:
            obsdatain:
              obsfile: Data/truth.obs3d.nc
            obsdataout:
              obsfile: Data/3dvar.obs3d.nc
            obs type: WSpeed
    variational:
      minimizer:
        algorithm: DRPCG
      iterations:
      - diagnostics:
          departures: ombg0
        gradient norm reduction: 1.0e-10
        ninner: 10
        geometry:
          nx: 20
          ny: 10
          depths: [4500.0, 5500.0]
        online diagnostics:
          write increment: true
          increment:
            state component:
              datadir: Data
              date: 2010-01-01T12:00:00Z
              exp: 3dvar.iter1
              type: in
      - diagnostics:
          departures: ombg1
        gradient norm reduction: 1.0e-10
        ninner: 10
        geometry:
          nx: 40
          ny: 20
          depths: [4500.0, 5500.0]
        online diagnostics:
          write increment: true
          increment:
            state component:
              datadir: Data
              date: 2010-01-01T12:00:00Z
              exp: 3dvar.iter2
              type: in
              analysis variables: [x]
    final:
      diagnostics:
        departures: oman
      increment:
        geometry:
          nx: 40
          ny: 20
          depths: [4500.0, 5500.0]
        output:
          state component:
            datadir: Data
            date: 2010-01-01T12:00:00Z
            exp: 3dvar.increment
            type: in
            analysis variables: [x]
    output:
      datadir: Data
      exp: 3dvar
      frequency: PT6H
      type: an
    """).strip())

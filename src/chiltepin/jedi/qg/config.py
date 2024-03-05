import textwrap
import yaml

def merge_config(d1, d2):
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            merge_config(d1[key], value)
        else:
            d1[key] = value


def forecast_default():
    return yaml.safe_load(textwrap.dedent(f"""
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

def makeobs3d_default():
    return yaml.safe_load(textwrap.dedent(f"""
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

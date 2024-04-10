from chiltepin.jedi.leadtime import leadtime_to_seconds, seconds_to_leadtime


def test_leadtime_to_seconds():
    assert leadtime_to_seconds("PT0S") == 0
    assert leadtime_to_seconds("PT1M") == 60
    assert leadtime_to_seconds("PT1H") == 3600
    assert leadtime_to_seconds("PT1H30M") == 5400

    assert leadtime_to_seconds("P1D") == 86400
    assert leadtime_to_seconds("P1DT1H") == 90000
    assert leadtime_to_seconds("P1DT1H30M") == 91800

    assert leadtime_to_seconds("MT0S") == -0
    assert leadtime_to_seconds("MT1M") == -60
    assert leadtime_to_seconds("MT1H") == -3600
    assert leadtime_to_seconds("MT1H30M") == -5400

    assert leadtime_to_seconds("M1D") == -86400
    assert leadtime_to_seconds("M1DT1H") == -90000
    assert leadtime_to_seconds("M1DT1H30M") == -91800


def test_seconds_to_leadtime():
    assert seconds_to_leadtime(0) == "PT0S"
    assert seconds_to_leadtime(60) == "PT1M"
    assert seconds_to_leadtime(3600) == "PT1H"
    assert seconds_to_leadtime(5400) == "PT1H30M"

    assert seconds_to_leadtime(86400) == "P1D"
    assert seconds_to_leadtime(90000) == "P1DT1H"
    assert seconds_to_leadtime(91800) == "P1DT1H30M"

    assert seconds_to_leadtime(-0) == "PT0S"
    assert seconds_to_leadtime(-60) == "MT1M"
    assert seconds_to_leadtime(-3600) == "MT1H"
    assert seconds_to_leadtime(-5400) == "MT1H30M"

    assert seconds_to_leadtime(-86400) == "M1D"
    assert seconds_to_leadtime(-90000) == "M1DT1H"
    assert seconds_to_leadtime(-91800) == "M1DT1H30M"

from chiltepin.jedi.leadtime import leadtime_to_seconds, seconds_to_leadtime

def test_leadtime_to_seconds():
    assert leadtime_to_seconds("PT0S") == 0
    assert leadtime_to_seconds("PT1M") == 0
    assert leadtime_to_seconds("PT1H") == 3600
    assert leadtime_to_seconds("PT1H30M") == 3600

    assert leadtime_to_seconds("P1D") == 86400
    assert leadtime_to_seconds("P1DT1H") == 90000
    assert leadtime_to_seconds("P1DT1H30M") == 90000

    assert leadtime_to_seconds("MT0S") == -0
    assert leadtime_to_seconds("MT1H") == -3600
    assert leadtime_to_seconds("MT1H30M") == -3600

    assert leadtime_to_seconds("M1D") == -86400
    assert leadtime_to_seconds("M1DT1H") == -90000
    assert leadtime_to_seconds("M1DT1H30M") == -90000
    assert leadtime_to_seconds("M1DT1H30M") == -90000
    

def test_seconds_to_leadtime():
    pass

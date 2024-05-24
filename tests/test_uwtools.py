from subprocess import check_output


def test_uwtools_install():
    check_output(["uw --version"], shell=True)

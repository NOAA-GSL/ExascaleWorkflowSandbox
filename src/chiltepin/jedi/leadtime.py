import re


def fcst_to_seconds(fcst):
    seconds = 0
    p = re.compile(r"\D+(\d+)S")
    m = p.search(fcst)
    if m:
        seconds += int(m.group(1))
    p = re.compile(r"/\D+(\d+)M")
    m = p.search(fcst)
    if m:
        seconds += int(m.group(1) * 60)
    p = re.compile(r"\D+(\d+)H")
    m = p.search(fcst)
    if m:
        seconds += int(m.group(1)) * 3600
    p = re.compile(r"\D+(\d+)D")
    m = p.search(fcst)
    if m:
        seconds += int(m.group(1)) * 3600 * 24
    p = re.compile("M")
    m = p.match(fcst)
    if m:
        seconds = seconds * -1
    return seconds


def seconds_to_fcst(s):
    seconds = s
    fcst = ""
    if seconds < 0:
        fcst = "M"
    else:
        fcst = "P"
    days = seconds // (3600 * 24)
    if days > 0:
        fcst = fcst + f"{days}D"
    if seconds % (3600 * 24) != 0 or seconds == 0:
        fcst = fcst + "T"
    hours = (seconds - days * 3600 * 24) // 3600
    if hours > 0:
        fcst = fcst + f"{hours}H"
    minutes = (seconds - days * 3600 * 24 - hours * 3600) // 60
    if minutes > 0:
        fcst = fcst + f"{minutes}M"
    seconds = seconds - days * 3600 * 24 - hours * 3600 - minutes * 60
    if (days == 0 and hours == 0 and minutes == 0) or (seconds > 0):
        fcst = fcst + f"{seconds}S"
    return fcst

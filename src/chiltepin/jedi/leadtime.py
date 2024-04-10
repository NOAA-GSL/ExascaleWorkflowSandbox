def leadtime_to_seconds(leadtime):
    import re

    seconds = 0
    p = re.compile(r"\D+(\d+)S")
    m = p.search(leadtime)
    if m:
        seconds += int(m.group(1))
    p = re.compile(r"\D+(\d+)M")
    m = p.search(leadtime)
    if m:
        seconds += int(m.group(1)) * 60
    p = re.compile(r"\D+(\d+)H")
    m = p.search(leadtime)
    if m:
        seconds += int(m.group(1)) * 3600
    p = re.compile(r"\D+(\d+)D")
    m = p.search(leadtime)
    if m:
        seconds += int(m.group(1)) * 3600 * 24
    p = re.compile("M")
    m = p.match(leadtime)
    if m:
        seconds = seconds * -1
    return seconds


def seconds_to_leadtime(s):
    leadtime = ""
    if s < 0:
        leadtime = "M"
        seconds = s * -1
    else:
        leadtime = "P"
        seconds = s
    days = seconds // (3600 * 24)
    if days > 0:
        leadtime = leadtime + f"{days}D"
    if seconds % (3600 * 24) != 0 or seconds == 0:
        leadtime = leadtime + "T"
    hours = (seconds - days * 3600 * 24) // 3600
    if hours > 0:
        leadtime = leadtime + f"{hours}H"
    minutes = (seconds - days * 3600 * 24 - hours * 3600) // 60
    if minutes > 0:
        leadtime = leadtime + f"{minutes}M"
    seconds = seconds - days * 3600 * 24 - hours * 3600 - minutes * 60
    if (days == 0 and hours == 0 and minutes == 0) or (seconds > 0):
        leadtime = leadtime + f"{seconds}S"
    return leadtime

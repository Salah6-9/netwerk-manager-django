import psutil
import os
import time


def collect_metrics():

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage(os.path.abspath(os.sep)).percent

    net = psutil.net_io_counters()

    uptime = int(time.time() - psutil.boot_time())

    temp = None
    temps = psutil.sensors_temperatures()

    if temps:
        for name, entries in temps.items():
            if entries:
                temp = entries[0].current
                break

    return {
        "cpu_usage": cpu,
        "ram_usage": ram,
        "disk_usage": disk,
        "network_in": net.bytes_recv,
        "network_out": net.bytes_sent,
        "cpu_temperature": temp,
        "uptime": uptime,
    }

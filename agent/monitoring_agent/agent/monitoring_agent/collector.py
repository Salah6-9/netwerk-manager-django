import psutil
import os
import time
import socket
import platform
import uuid


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

def collect_device_info():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(socket.gethostname())
    mac = ":".join([
        f"{(uuid.getnode() >> ele) & 0xff:02x}"
        for ele in range(40, -1, -8)
    ])

    os_name = platform.system()
    agent_version = "1.0"
    return {
        "hostname": hostname,
        "ip": ip,
        "mac": mac,
        "os": os_name,
        "agent_version": agent_version,
    }
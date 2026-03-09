import time
import sys
import re
from .collector import collect_metrics
from .sender import send_metrics
from .config import load_config, save_config


def register():

    token = input("Enter device token: ").strip()
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        print("Invalid token format")
        print("Token must be 64 hexadecimal characters")
        return


    config = load_config()

    config["agent_token"] = token

    if "api_url" not in config:
        config["api_url"] = "http://127.0.0.1:8000/api/metrics/"

    if "interval" not in config:
        config["interval"] = 60

    save_config(config)

    print("Agent registered successfully")


def run():

    config = load_config()

    token = config.get("agent_token")

    if not token:
        print("Agent not registered. Run with --register")
        return

    api_url = config["api_url"]
    interval = config["interval"]

    while True:

        try:

            metrics = collect_metrics()

            status = send_metrics(
                api_url,
                token,
                metrics
            )

            print("Sent metrics:", status)

        except Exception as e:

            print("Agent error:", e)

        time.sleep(interval)


if __name__ == "__main__":

    if "--register" in sys.argv:
        register()
    else:
        run()

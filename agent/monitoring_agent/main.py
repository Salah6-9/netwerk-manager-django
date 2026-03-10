import time
import sys
import re

from .collector import collect_metrics, collect_device_info
from .sender import send_metrics, send_enrollment
from .config import load_config, save_config


def register():
    """
    Manual registration with device token
    """

    token = input("Enter device token: ").strip()

    if not re.fullmatch(r"[a-f0-9]{64}", token):
        print("Invalid token format")
        print("Token must be 64 hexadecimal characters")
        return

    config = load_config()

    config["agent_token"] = token

    if "api_url" not in config:
        config["api_url"] = "http://127.0.0.1:8000"

    if "interval" not in config:
        config["interval"] = 60

    save_config(config)

    print("Agent registered successfully")


def enrollment_loop(config):
    """
    Agent enrollment process
    """

    device_info = collect_device_info()
    user_token = config.get("user_token")

    while True:

        response = send_enrollment(
            config["api_url"],
            user_token,
            device_info
        )

        if not isinstance(response, dict):
            print("Invalid response from server")
            time.sleep(10)
            continue

        status = response.get("status")

        if status == "approved":

            token = response.get("agent_token")

            config["agent_token"] = token
            save_config(config)

            print("Enrollment approved")
            print("Token received")

            return token

        elif status == "pending":

            print("Enrollment pending...")
            time.sleep(10)

        elif status == "rejected":

            print("Enrollment rejected")
            return None


def run():

    config = load_config()

    # default configuration
    if "api_url" not in config:
        config["api_url"] = "http://127.0.0.1:8000"

    if "interval" not in config:
        config["interval"] = 60

    # ensure user token exists
    user_token = config.get("user_token")

    if not user_token:

        user_token = input("Enter your user token: ").strip()

        config["user_token"] = user_token
        save_config(config)

        print("User token saved")

    token = config.get("agent_token")
    interval = config.get("interval", 60)

    # start enrollment if no agent token
    if not token:

        print("No token found → starting enrollment")

        token = enrollment_loop(config)

        if not token:
            return

    print("Starting monitoring...")

    while True:
    
        try:
        
            metrics = collect_metrics()
    
            response = send_metrics(
                config["api_url"],
                token,
                metrics
            )
    
            # token invalid
            if isinstance(response, dict) and response.get("error") == "Invalid token":
            
                print("Token invalid → restarting enrollment")
    
                config.pop("agent_token", None)
                save_config(config)
    
                return run()
    
            print("Sent metrics:", response)
    
        except Exception as e:
        
            print("Server unreachable:", str(e))
            print("Retrying in 30 seconds...")
    
            time.sleep(30)
            continue
        
        time.sleep(interval)

if __name__ == "__main__":

    if "--register" in sys.argv:
        register()
    else:
        run()
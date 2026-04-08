import time
import sys
import re
import logging

from .collector import collect_metrics, collect_device_info
from .sender import send_metrics, send_enrollment
from .config import get_config, update_config_key

logger = logging.getLogger("agent.main")

def register():
    """
    Manual registration with device token
    """
    token = input("Enter agent token: ").strip()

    if not re.fullmatch(r"[a-f0-9]{40,64}", token):
        print("Invalid token format. Token must be 40-64 hex characters.")
        return

    update_config_key("agent_token", token)
    print("Agent registered successfully and token saved to config.json")


def enrollment_loop(api_url, user_token):
    """
    Agent enrollment process
    """
    device_info = collect_device_info()

    while True:
        response = send_enrollment(api_url, user_token, device_info)

        if not isinstance(response, dict):
            print("Invalid response from server. Retrying in 10s...")
            time.sleep(10)
            continue

        status = response.get("status")

        if status == "approved":
            token = response.get("agent_token")
            update_config_key("agent_token", token)
            print("Enrollment approved. Token received and saved.")
            return token
        elif status == "pending":
            print("Enrollment pending...")
            time.sleep(10)
        elif status == "rejected":
            print("Enrollment rejected.")
            return None


def run():
    # Load core configuration with fallbacks
    api_url = get_config("api_url", "http://127.0.0.1:8000")
    interval = get_config("interval", 60)
    user_token = get_config("user_token")
    agent_token = get_config("agent_token")

    # Ensure user token exists (required for enrollment if no agent token)
    if not agent_token and not user_token:
        user_token = input("Enter your user token: ").strip()
        update_config_key("user_token", user_token)
        print("User token saved.")

    # Start enrollment if no agent token
    if not agent_token:
        print("No agent token found -> starting enrollment...")
        agent_token = enrollment_loop(api_url, user_token)
        if not agent_token:
            return

    print(f"Starting monitoring (Interval: {interval}s, Server: {api_url})...")

    while True:
        try:
            metrics = collect_metrics()
            response = send_metrics(api_url, agent_token, metrics)

            # Check for invalid token error
            if isinstance(response, dict) and response.get("error") == "Invalid token":
                print("Token invalid -> clearing agent_token and restarting enrollment...")
                update_config_key("agent_token", None)
                return run()

            print(f"Metrics sent: {response}")

        except Exception as e:
            print(f"Error during execution: {e}")
            print("Retrying in 30 seconds...")
            time.sleep(30)
            continue
        
        time.sleep(interval)

if __name__ == "__main__":
    if "--register" in sys.argv:
        register()
    else:
        run()
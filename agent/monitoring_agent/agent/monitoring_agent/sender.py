import requests


def send_metrics(api_url, token, data):
    """
    Send device metrics to monitoring API
    """

    headers = {
        "Authorization": f"Agent {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{api_url}/api/metrics/",
        json=data,
        headers=headers,
        timeout=5,
    )

    try:
        return response.json()
    except Exception:
        return {"status_code": response.status_code}


def send_enrollment(api_url, user_token, data):
    """
    Send enrollment request to server
    """

    headers = {
        "Authorization": f"Token {user_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{api_url}/api/device-enrollment/",
        json=data,
        headers=headers,
        timeout=10,
    )

    try:
        return response.json()
    except Exception:
        print("Server returned invalid response:", response.text)
        return {"status": "pending"}
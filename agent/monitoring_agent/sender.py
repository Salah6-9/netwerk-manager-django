import requests


def send_metrics(api_url, token, data):

    headers = {
        "Authorization": f"Agent {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        api_url,
        json=data,
        headers=headers,
        timeout=5,
    )

    return response.status_code

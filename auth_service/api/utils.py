import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_auth0(url, headers=None, data=None):
    response = requests.get(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

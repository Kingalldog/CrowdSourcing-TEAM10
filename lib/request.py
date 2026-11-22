import requests


class Requester:
    def __init__(self, token: str, base_url: str):
        if not token:
            raise ValueError("Token не может быть пустым")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json",
        }

    def request(self, method: str, url: str, **kwargs):
        response = requests.request(method, url, headers=self.headers, **kwargs)
        if not response.ok:
            print(response.status_code)
            print(response.text)
            response.raise_for_status()
        if not response.text:
            return None
        return response.json()

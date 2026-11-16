import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from IPython.display import HTML, display


def print_json(data):
    """Красивый вывод JSON."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


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
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from dotenv import load_dotenv

from lib.request import Requester
from lib.create_project import create_project
from lib.config import BASE_URL

load_dotenv()
TOKEN = os.environ.get("TOKEN")
DATA_DIR = "./data"
def run_create_project():
    """Обёртка: выполняет create_project и печатает результат/ошибку.
    """
    if not TOKEN:
        print("ОШИБКА: переменная окружения TOKEN не задана")
        return 
    try:
        requester = Requester(TOKEN, BASE_URL)
        result = create_project(requester, DATA_DIR)
    except Exception as e:
        print(f"ОШИБКА: {type(e).__name__}: {e}")
        return
    
    print("Проект успешно создан:")

if __name__ == "__main__":
    run_create_project()
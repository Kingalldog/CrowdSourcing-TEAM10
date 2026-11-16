import os
from dotenv import load_dotenv

from request import Requester
from create_project import create_project
from config import BASE_URL

load_dotenv()
TOKEN = os.environ.get("TOKEN")

def run_create_project():
    """Обёртка: выполняет create_project и печатает результат/ошибку.
    """
    if not TOKEN:
        print("ОШИБКА: переменная окружения TOKEN не задана")
        return 
    try:
        requester = Requester(TOKEN, BASE_URL)
        result = create_project(requester)
    except Exception as e:
        print(f"ОШИБКА: {type(e).__name__}: {e}")
        return
    
    print("Проект успешно создан:")

if __name__ == "__main__":
    run_create_project()
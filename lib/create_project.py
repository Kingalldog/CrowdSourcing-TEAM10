import csv
import json
import time
from pathlib import Path

from lib.request import print_json

from lib.api_client import TasksAPIClient
from lib.data_loader import make_project_payload
from lib.utils import (
    load_training_tasks,
    make_training_payload,
    get_task_list,
    build_pool_payload_from_spec)

def log_operation(operation_id, client):
    while True:
        op = client.get_operation(operation_id)
        status = op["status"]
        print(f"Статус операции: {status}, прогресс: {op.get('progress', 0)}%")

        if status in ("SUCCESS", "FAIL"):
            break
        time.sleep(2)

    if status == "SUCCESS":
        print("Задания успешно загружены.")
    else:
        print("Операция завершилась с ошибкой. Запросите лог для деталей.")
        log = client.get_operation_log(operation_id)

        for step in log:
            if not step.get("success", True):
                print("❌ Ошибка на шаге:", step.get("input"))
                print("Детали ошибки:", step.get("output"))

def create_project(requester, dir) -> dict:
    """
    Создает проект, пул и задания на основе файлов из data_dir.
    Возвращает словарь с созданными сущностями.
    """
    client = TasksAPIClient(requester)

    project = client.create_project(make_project_payload(dir))
    project_id = project["id"]
    print("Project done")

    training = client.create_training(make_training_payload(project_id))
    training_id = training["id"]
    print("Traning done")

    operation = client.create_tasks_async(get_task_list(training_id, dir))
    operation_id = operation["id"]

    log_operation(operation_id, client)

    # pool_id = 6867304
    # responce = client.get_pool(pool_id)
    # print_json(responce)

    with open(Path(dir + "/quality_pool_spec.json")) as f:
        spec = json.load(f)
    exam = client.create_pool_from_spec(build_pool_payload_from_spec(
        spec,
        project_id=project_id,
        private_name="Bbox: пул по разметке бабочек",
        training_pool_id=training_id,
        training_passing_skill_value=100,
    ))
    
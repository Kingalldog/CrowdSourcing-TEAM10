import csv
import json
from pathlib import Path

from lib.config import TSV_TRAIN

def make_view_spec(view: dict) -> dict:
    return {
        "lock": {
            "core": "1.7.0",
            "view.list": "1.0.5",
            "view.text": "1.0.0",
            "field.radio-group": "1.1.10",
            "view.image": "1.2.0",
            "helper.if": "1.0.0",
            "condition.required": "1.1.5",
            "plugin.hotkeys": "1.0.0",
            "condition.equals": "1.0.0",
            "field.image-annotation": "1.0.0",
            "field.checkbox": "1.0.0",
            "plugin.field.image-annotation.hotkeys": "1.0.0",
            "action.set": "1.0.0",
            "plugin.toloka": "1.1.8",
            "condition.any": "1.0.0",
            "condition.not": "1.0.0",
            "condition.equals": "1.0.0",
            "condition.required": "1.1.5",
        },
        "type": "tb",
        "config": json.dumps(view, ensure_ascii=False),
        "settings": {
            "showSkip": True,
            "showTimer": True,
            "showTitle": True,
            "showFinish": True,
            "showSubmit": True,
            "showMessage": True,
            "showFullscreen": True,
            "showInstructions": True,
        },
    }

def make_training_payload(project_id):
    training_payload = {
        "project_id": project_id,
        "private_name": "Тренировка: выделение бабочек",
        "will_expire": "2030-01-01T00:00:00.000Z",
        "assignment_max_duration_seconds": 300,
        "training_tasks_in_task_suite_count": 10,
    }
    return training_payload

def _parse_golden_result(raw: str) -> list[dict]:
    """Приводит GOLDEN:result из TSV к валидному JSON-массиву рамок."""
    if not raw or not raw.strip():
        return []
    text = raw.strip().replace("\\,", ",").replace('\\"', '"')
    if not text.startswith("["):
        text = "[" + text + "]"
    return json.loads(text)


def load_training_tasks(tsv_path: str | Path, training_id: str) -> list[dict]:
    """
    Читает TSV и возвращает СПИСОК задач, готовых для POST /tasks?async_mode=true.
    Каждый элемент — самостоятельный объект задания с pool_id внутри.
    """
    tsv_path = Path(tsv_path)
    if not tsv_path.is_file():
        raise FileNotFoundError(f"Файл с тренировочными заданиями не найден: {tsv_path}")

    tasks: list[dict] = []
    with open(tsv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row_number, row in enumerate(reader, start=2):
            image_url = (row.get("INPUT:image") or "").strip()
            if not image_url:
                raise ValueError(f"Строка {row_number}: пустое поле INPUT:image")

            output_values = {
                "result": _parse_golden_result(row.get("GOLDEN:result", "")),
                "photo_not_loaded": (
                    (row.get("GOLDEN:photo_not_loaded") or "").strip().lower() == "true"
                ),
            }

            task = {
                "pool_id": training_id,
                "input_values": {"image": image_url},
                "known_solutions": [
                    {"output_values": output_values, "correctness_weight": 1.0}
                ],
                "infinite_overlap": True,
            }

            hint_text = (row.get("HINT:text") or "").strip()
            if hint_text:
                task["message_on_unknown_solution"] = hint_text

            feedback_text = (row.get("FEEDBACK:feedback_text") or "").strip()
            if feedback_text:
                task["feedback"] = {"feedback_text": feedback_text}

            tasks.append(task)

    if not tasks:
        raise ValueError(f"В файле {tsv_path} не найдено ни одного тренировочного задания.")
    return tasks

def get_task_list(training_id, dir):
    return load_training_tasks(
        Path(dir + "/" + TSV_TRAIN),
        training_id=training_id,
    )


import copy

SERVER_ONLY_FIELDS = {"id", "status", "created", "owner"}


def build_pool_payload_from_spec(
    spec: dict,
    *,
    project_id: str | None = None,
    private_name: str | None = None,
    will_expire: str | None = None,
    training_pool_id: str | None = None,
    training_passing_skill_value: int | None = None,
    drop_training_requirement: bool = False,
) -> dict:
    """Готовит payload для POST /pools на основе выгруженной спецификации."""
    payload = copy.deepcopy(spec)

    # 1. Убираем серверные поля
    for key in SERVER_ONLY_FIELDS:
        payload.pop(key, None)

    # 2. Переопределения верхнего уровня
    if project_id is not None:
        payload["project_id"] = project_id
    if private_name is not None:
        payload["private_name"] = private_name
    if will_expire is not None:
        payload["will_expire"] = will_expire

    # 3. Обрабатываем quality_control
    qc = payload.get("quality_control", {})

    if drop_training_requirement:
        qc.pop("training_requirement", None)
        # если убрали требование к обучению — это уже не экзамен
        payload.pop("regular_subtype", None)

    tr = qc.get("training_requirement")
    if tr is not None:
        if training_pool_id is not None:
            tr["training_pool_id"] = training_pool_id
        if training_passing_skill_value is not None:
            tr["training_passing_skill_value"] = training_passing_skill_value

    # 4. Чистим uuid у сборщиков — пусть сервер сгенерирует
    for cfg in qc.get("configs", []):
        cfg.get("collector_config", {}).pop("uuid", None)

    if qc:
        payload["quality_control"] = qc

    return payload
import json
from pathlib import Path

from utils import make_view_spec
from config import DATA_DIR


class DataLoader:
    """Читает и валидирует файлы из директории проекта."""

    def __init__(self, data_dir: str | Path = "./data"):
        self.data_path = Path(data_dir)

    def load_all(self) -> dict:
        required = ["instruction.html", "input.json", "output.json", "view.json"]
        missing = [f for f in required if not (self.data_path / f).is_file()]
        if missing:
            raise FileNotFoundError(
                f"В папке '{self.data_path}' не найдены файлы: {', '.join(missing)}"
            )

        with open(self.data_path / "instruction.html", encoding="utf-8") as f:
            instructions = f.read()
        with open(self.data_path / "input.json", encoding="utf-8") as f:
            input_spec = json.load(f)
        with open(self.data_path / "output.json", encoding="utf-8") as f:
            output_spec = json.load(f)
        with open(self.data_path / "view.json", encoding="utf-8") as f:
            view = json.load(f)

        return {
            "instructions": instructions,
            "input_spec": input_spec,
            "output_spec": output_spec,
            "view_spec": make_view_spec(view),
        }

def make_project_payload():
    loader = DataLoader(DATA_DIR)
    data = loader.load_all()

    project_payload = {
        "public_name": "Bbox: выделение бабочек",
        "public_description": "",
        "public_instructions": data["instructions"],
        "task_spec": {
            "input_spec": data["input_spec"],
            "output_spec": data["output_spec"],
            "view_spec": data["view_spec"],
        },
        "assignments_issuing_type": "AUTOMATED",
        "assignments_automerge_enabled": False,
        "max_active_assignments_count": 15,
        "localization_config": {"default_language": "RU"},
    }

    return project_payload
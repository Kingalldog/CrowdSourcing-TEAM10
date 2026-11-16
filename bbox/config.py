from pathlib import Path

BASE_URL = "https://tasks.yandex.ru/api/v1"
DATA_DIR = Path("./data")
TSV_TRAIN = DATA_DIR / "train_task.tsv"

TRAINING_TASKS_PER_SUITE = 3
ASSIGNMENT_MAX_DURATION_SECONDS = 300
WILL_EXPIRE = "2030-01-01T00:00:00.000Z"

LOG_DIR = Path("./logs")
LOG_FILE = LOG_DIR / "api.log"
LOG_LEVEL = "INFO"
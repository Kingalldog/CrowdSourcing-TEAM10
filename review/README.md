# Проверка bbox-разметки бабочек

Проект в Яндекс Заданиях: [открыть проект](https://tasks.yandex.ru/requester/project/11900/).

В этой папке находятся инструкции и настройки проекта для проверки уже готовых разметок бабочек. Скрипт создания проекта находится в `lib/` в корне репозитория.

## Файлы задания

- `data/instruction.html` — инструкция проверяющему.
- `data/input.json` — входные данные: рамки (`boxes`), URL изображения (`image`) и ID кандидата (`candidate_id`).
- `data/output.json` — обязательный вердикт: `accept`, `missing`, `extra`, `boundary`, `uncertain` или `load_error`.
- `data/view.json` — интерфейс проверки: исходные рамки показаны на изображении, а проверяющий выбирает один вердикт. Рамки в интерфейсе отключены для редактирования.
- `data/train_tasks.tsv` — обучающие задания.
- `data/exam_tasks.tsv` — проверочные задания.
- `data/pool_tasks.tsv` — задания для проверки.

Описание вердиктов, критериев проверки и доступных сведений о настройках пула: [selection.md](selection.md#отбор-и-проверка-разметки).

## Зависимости

Из корня репозитория создайте и активируйте виртуальное окружение, затем установите зависимость:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install requests
```

## Создание проекта

`lib/create_project.py` создаёт проект по инструкции, схемам входных и выходных данных и настройкам интерфейса из указанной папки. Для API нужен OAuth-токен Яндекс Заданий.

```bash
export TOKEN='ваш_oauth_токен'
python -c 'import os; from lib.request import Requester; from lib.config import BASE_URL; from lib.create_project import create_project; create_project(Requester(os.environ["TOKEN"], BASE_URL), "review/data", public_name="Review: проверка разметки бабочек")'
```

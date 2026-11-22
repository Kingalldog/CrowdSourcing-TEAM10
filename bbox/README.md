# Разметка bbox: бабочки

Проект в Яндекс Заданиях: [открыть проект](https://tasks.yandex.ru/requester/project/11868).

В этой папке лежат инструкции, схема интерфейса и TSV-файлы проекта разметки взрослых дневных бабочек для Яндекс Заданий. Скрипты создания проекта находятся в `lib/` в корне репозитория.

## Файлы задания

- `data/instruction.html` — инструкция исполнителю: как обводить бабочек, отмечать отсутствие объекта и сообщать о незагрузившемся фото.
- `data/input.json` - входное поле (URL изображения)
- `data/output.json` — поля ответа: рамки бабочек (`result`), флаг отсутствия объектов (`no_object_on_photo`) и флаг ошибки загрузки фото (`photo_not_loaded`).
- `data/view.json` — интерфейс разметки.
- `data/train_tasks.tsv` — задания обучения с известными ответами.
- `data/exam_tasks.tsv` — проверочные задания.
- `data/pool_tasks.tsv` — задания основного пула.

Критерии отбора исполнителей и примеры отклонённых работ описаны в [selection.md](selection.md#отбор-исполнителей-для-разметки-bbox).

## Зависимости

Из корня репозитория создайте и активируйте виртуальное окружение, затем установите зависимость:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install requests
```

## Создание проекта

Для API нужен OAuth-токен Яндекс Заданий. 

```bash
export TOKEN='ваш_oauth_токен'
python -c 'import os; from lib.request import Requester; from lib.config import BASE_URL; from lib.create_project import create_project; create_project(Requester(os.environ["TOKEN"], BASE_URL), "bbox/data", public_name="Bbox: выделение бабочек")'
```

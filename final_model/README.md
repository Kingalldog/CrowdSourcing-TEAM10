# Итоговая модель команды 10

[Предсказания для Контеста](contest_preds.jsonl) содержат 400 фотографий. Посылка получила **10/10**. На 415 фотографиях командного golden set модель Grounding DINO Base с дополнительными классами сравнения получила object F1@IoU 0,5 = 0,937.

- [Сравнение пяти конфигураций](results/leaderboard.md)
- [Параметры выбранной модели, версия весов и контрольные суммы исходного запуска](results/selected_model.json)
- [Повторить сравнение моделей](experiments/README.md)
- [Исходные ответы моделей, предсказания и параметры экспериментов](results/)

Командный эталон находится в [golden_set.zip](../golden_set.zip). После распаковки архива эталона из корня репозитория файлы лежат в `data/golden_set/`. Экзаменационный `dataset.jsonl` выдаётся в задании.

## С каким промптом получили 10/10

Grounding DINO Base получала один и тот же текст для всех 400 экзаменационных снимков.

```text
butterfly. moth. bee. wasp. fly. dragonfly. flower.
```

`butterfly` и `moth` обозначают целевые объекты. Остальные пять слов помогают отсеивать ложные рамки на других насекомых и цветах. Для каждой предложенной рамки скрипт сравнивает максимальную оценку среди целевых слов с максимальной оценкой среди остальных. Например, если оценка для `wasp` выше оценок и для `butterfly`, и для `moth`, скрипт отбрасывает рамку. При равенстве рамка проходит это сравнение. Для конкурсного файла скрипт сохраняет рамки с целевой оценкой от 0,25 и убирает дубликаты с перекрытием IoU больше 0,55, отдавая приоритет более высокой оценке.

<details>
<summary>Промпты остальных моделей в сравнении</summary>

Базовые Grounding DINO Tiny и Base получали строку `butterfly. moth.`. OWLv2 обрабатывала `a photo of a butterfly` и `a photo of a moth` как два отдельных запроса.

**Основной промпт Qwen3-VL**

```text
Detect every visible adult butterfly or moth in this image.
Draw one tight bounding box around each individual's visible wings, body, legs and antennae, including partially visible individuals. Include moths even when they resemble wasps. Exclude shadows, bees, wasps, flies, other non-lepidopteran insects, caterpillars and pupae.
Give the boxes as a JSON array. Each element has a "bbox_2d" field [xmin,ymin,xmax,ymax] with coordinates from 0 to 1000, and a "label" field set to "butterfly". If there are no adult butterflies or moths, return []. Return only the JSON array.
```

Если ответ не удавалось разобрать или координаты были некорректными, скрипт делал вторую попытку с более компактным форматом.

```text
Find all visible adult butterflies and moths in the image. For each, enclose the visible wings, body, legs and antennae in one tight rectangle. Ignore other insects, shadows, caterpillars and pupae.
Respond in compact JSON with just an array of boxes: [[xmin,ymin,xmax,ymax],...]. Use integer coordinates from 0 to 1000. Return [] if absent. Finish the array. No labels or explanation.
```

</details>

## Запуск

Из каталога `final_model/` запустите детектор на выданном `dataset.jsonl`. Для конкурсной посылки использовались Python 3.14 и GPU Apple Silicon (MPS).

```sh
python3 -m pip install -r requirements.txt
python3 predict.py dataset.jsonl predictions.jsonl
```

Скрипт читает оригиналы фото из `images/` и скачивает недостающие по ссылкам из манифеста. Если фото уже лежат в другой папке, укажите `--images ПАПКА`. На компьютере без MPS по умолчанию используется CPU.

Чтобы проверить экспорт из сохранённого вывода модели, достаточно стандартного Python.

```sh
python3 predict.py dataset.jsonl regenerated.jsonl --from-raw results/exam_raw.jsonl
cmp regenerated.jsonl contest_preds.jsonl
```

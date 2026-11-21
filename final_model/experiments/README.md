# Сравнение моделей

Все команды выполняются из `final_model/`. После распаковки [командного эталона](../../golden_set.zip) задайте пути к файлам.

```sh
GOLD=../data/golden_set/golden_set.jsonl
MANIFEST=../data/golden_set/manifest.jsonl
```

## Воспроизвести метрики

Пересчёт по сохранённым детекциям использует стандартный Python. Скрипт подбирает пороги на 323 снимках, сравнивает с базовыми порогами и выводит результаты для всех 415 снимков и отложенных 92. Для проверки эксперимента с одним фактором сравните поля `all_reference_threshold` и `all_at_calibration_threshold`.

```sh
python3 -m experiments.score "$GOLD" results
```

## Повторить детекцию на фото

Установите [зависимости DINO и OWLv2](../requirements.txt) в окружении Python 3.14. Для OWLv2 использовался MPS. Следующие команды записывают новые результаты в `runs/` и используют общий кэш оригиналов `team_images/`.

```sh
mkdir -p runs
cp results/calibration.jsonl results/holdout.jsonl runs/
for model in grounding_tiny grounding_base grounding_base_contrast; do
  python3 predict.py "$MANIFEST" "runs/${model}_raw.jsonl" --images team_images --raw "$model"
done
python3 -m experiments.baselines owl "$MANIFEST" team_images runs/owlv2_base_raw.jsonl
```

Для запуска 4-битной Qwen3-VL-2B-Instruct на Apple Silicon создайте отдельное окружение Python 3.12 в каталоге `final_model/`.

```sh
python3.12 -m venv .venv-qwen
.venv-qwen/bin/python -m pip install 'mlx==0.29.3' 'mlx-vlm==0.3.9' 'mlx-lm==0.28.3' 'transformers==4.57.6'
.venv-qwen/bin/python -m experiments.baselines qwen "$MANIFEST" team_images runs/qwen4bit_raw.jsonl
python3 -m experiments.score "$GOLD" runs
```

Версии весов, промпты и параметры каждого эксперимента записаны в [файлах запуска](../results/). Исходные измерения опубликованы в [таблице результатов](../results/leaderboard.md).

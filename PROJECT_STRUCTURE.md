# Структура проекта

```text
ZAPI/
├── __init__.py
├── auth.py
├── base.py
├── graphs_charts.py
├── groups.py
├── hosts.py
├── inventory_macro.py
├── items.py
├── manual_check.py
├── requirements.txt
├── scripts.py
├── triggers_problems_events.py
├── errors/
│   └── exceptions.py
├── examples/
│   └── item_transforms.example.json
├── http/
│   └── http_api.py
└── utils/
    └── mutations.py
```

## Ядро пакета

- `__init__.py` - экспортирует основной класс `Zabbix`, объединяя все mixin-классы.
- `base.py` - хранит базовые настройки подключения и метод `get_api_version`.
- `auth.py` - отвечает за вход и выход через Zabbix API.
- `http/http_api.py` - низкоуровневый асинхронный HTTP-клиент на `aiohttp`; также содержит web-login и получение готовых изображений графиков.

## Mixin-классы Zabbix API

- `groups.py` - поиск групп узлов и сбор агрегированной информации по группе.
- `hosts.py` - запросы узлов по группе или `hostid`.
- `items.py` - поиск элементов данных, получение истории и трендов.
- `triggers_problems_events.py` - запросы триггеров, проблем и событий.
- `graphs_charts.py` - получение метаданных графиков и готовых изображений графиков.
- `inventory_macro.py` - обновление макросов и инвентаризации узлов.
- `scripts.py` - получение списка скриптов и запуск скриптов на узлах.

## Вспомогательный код

- `errors/exceptions.py` - пользовательские классы исключений, которые использует пакет.
- `utils/mutations.py` - функции нормализации узлов, элементов данных, интерфейсов и длительности проблем.
- `manual_check.py` - ручной smoke-check runner для проверки библиотеки на реальном сервере Zabbix.
- `requirements.txt` - зафиксированные Python-зависимости для локального виртуального окружения.
- `examples/item_transforms.example.json` - пример доменной таблицы преобразований. Не используется библиотекой автоматически.

## Формат внешних преобразований

В библиотеке нет встроенных правил преобразования элементов данных и нет привязки к источнику этих правил. Таблицу можно передать из приложения, загрузить из JSON в вызывающем коде, собрать из БД или сформировать вручную.

```json
{
  "item.key": {
    "units": "ms",
    "converter": "number",
    "round": 2
  }
}
```

Доступные converter-значения:

- `number` - приводит значение к числу и при наличии `round` округляет его.
- `on_off` - преобразует числовое значение в `ON` или `OFF`.
- `duration` - преобразует секунды в строку вида `1ч 2м 3с`.

Пример запуска ручной проверки с JSON-правилами:

```bash
python manual_check.py \
  --group "Linux servers" \
  --item-transforms examples/item_transforms.example.json
```

В коде приложения таблицу можно передать при создании API-клиента:

```python
import json

from ZAPI import Zabbix

with open("configs/item_transforms.json", encoding="utf-8") as file:
    item_transforms = json.load(file)

zabbix = Zabbix(
    url="https://zabbix.example.com",
    username="Admin",
    password="secret",
    item_transforms=item_transforms,
)

group_info = await zabbix.get_group_info("Linux servers")
```

Для разового переопределения можно передать таблицу прямо в `get_group_info(group_name, item_transforms=...)`.

## Локальные и сгенерированные каталоги

- `.venv/` - локальное виртуальное окружение Python; не должно попадать в коммит.
- `__pycache__/`, `http/__pycache__/`, `errors/__pycache__/`, `utils/__pycache__/` - сгенерированный Python bytecode cache; не должен попадать в коммит.
- `.agents/`, `.codex/` - локальные служебные данные инструментов.

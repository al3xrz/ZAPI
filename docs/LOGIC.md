# Логика работы ZAPI

Документ описывает основной поток работы пакета: от создания клиента до
получения нормализованной информации по группе хостов Zabbix.

## Общая идея

`Zabbix` - фасадный класс, который собирается из mixin-классов:

- `ZabbixBase` хранит настройки подключения и общие параметры.
- `ZabbixAuthMixin` выполняет `user.login` и `user.logout`.
- `ZabbixGroupsMixin` собирает сводную информацию по группе.
- `ZabbixHostsMixin`, `ZabbixItemsMixin`, `ZabbixTriggersMixin`,
  `ZabbixScriptsMixin`, `ZabbixInventoryMixin`, `ZabbixGraphsMixin`
  отвечают за отдельные сущности Zabbix.
- `APIClient` выполняет HTTP-запросы.
- `get_zabbix_result()` централизованно разбирает JSON-RPC ответы.
- `normalize_host()` и `normalize_items()` приводят сырой ответ Zabbix к
  прикладному формату.

## Создание клиента

При создании объекта задаются параметры подключения и поведение нормализации:

```python
zabbix = Zabbix(
    url="https://zabbix.example.com",
    username="user",
    password="password",
    api_version=7,
    item_transforms=item_transforms,
    ignore_private_items=True,
)
```

Поля, которые сохраняются в экземпляре:

- `server_address` - базовый адрес Zabbix.
- `api_url` - адрес JSON-RPC API: `{url}/api_jsonrpc.php`.
- `username`, `password` - учетные данные.
- `api_key` - токен после успешного `login()`.
- `api_version` - версия API, влияет на формат payload авторизации.
- `item_transforms` - правила преобразования элементов данных.
- `ignore_private_items` - если `True`, элементы с `key_`, начинающимся на `_`,
  исключаются из нормализованного результата.

## Авторизация

`login()` формирует JSON-RPC payload для метода `user.login`.

Для Zabbix API версии 7 используется поле:

```json
{"username": "...", "password": "..."}
```

Для версии 5 используется поле:

```json
{"user": "...", "password": "..."}
```

Ответ проходит через `get_zabbix_result(response, payload)`.
Если ответ успешный, `result` сохраняется в `self.api_key`.
Если Zabbix вернул ошибку, будет выброшен `ZabbixAPIError` с методом,
параметрами и исходным `error_data`.

## Обработка ответа Zabbix

Все JSON-RPC ответы должны проходить через `get_zabbix_result()`:

```python
result = get_zabbix_result(response, payload)
```

Логика:

- если есть `result`, он возвращается;
- если есть `error`, выбрасывается `ZabbixAPIError`;
- если нет ни `result`, ни `error`, выбрасывается `ZabbixError`.

Так код методов не дублирует проверку:

```python
if "result" in response:
    return response["result"]
else:
    raise ...
```

## Основной сценарий `get_group_info()`

`get_group_info(group_name)` строит итоговый список хостов группы.

Порядок работы:

1. Получить ID группы по имени через `hostgroup.get`.
2. Получить хосты группы через `host.get`.
3. Получить активные триггеры группы через `trigger.get`.
4. Получить проблемы группы через `problem.get`.
5. Получить доступные скрипты группы через `script.get`.
6. Связать проблемы с триггерами по `problem["objectid"] == trigger["triggerid"]`.
7. Связать триггеры с хостами по `trigger["hosts"][0]["hostid"] == host["hostid"]`.
8. Добавить каждому хосту `last_update`.
9. Добавить каждому хосту список `scripts`.
10. Нормализовать каждый хост через `normalize_host()`.

## Нормализация хоста

`normalize_host(host, item_transforms, ignore_private_items)` возвращает новый
словарь для приложения.

В результат попадают:

- `name`, `host`, `hostid`;
- `problems`;
- `interfaces`;
- `tags`;
- `inventory`;
- `macros`;
- `status`;
- `items`;
- `last_update`.

Проблемы строятся из триггеров, у которых есть поле `problem`.
Если в тегах проблемы есть `name` и `base`, они используются для имени и
расчета длительности. Если нужных тегов нет, используется стандартное имя
проблемы и длительность от `lastchange`.

Проблемы, в имени которых есть `SLA`, сейчас исключаются из результата.

## Нормализация элементов данных

Перед преобразованием элементов применяется фильтр:

```python
if ignore_private_items:
    items = [item for item in items if not item["key_"].startswith("_")]
```

По умолчанию `ignore_private_items=True`, поэтому служебные элементы с ключами
вида `_internal.key` не попадают в результат.

Затем `normalize_items()` применяет правила из `item_transforms`.

Поддерживаемые конвертеры:

- `number` - приводит значение к `float` и при необходимости округляет.
- `on_off` - превращает числовое значение в подпись `ON/OFF` или заданные
  пользовательские подписи.
- `duration` - превращает секунды в строку вида `1ч 2м 3с`.

## Логирование

Пакет использует стандартный `logging`:

```python
logger = logging.getLogger(__name__)
```

Библиотека не должна сама вызывать `logging.basicConfig()`.
Уровень логирования задается в основном приложении:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("ZAPI").setLevel(logging.DEBUG)
```

## Ошибки

Исключения находятся в `errors/exceptions.py`.

Основные классы:

- `ZabbixBaseException` - базовая ошибка пакета.
- `ZabbixError` - общая ошибка.
- `ZabbixNotFoundError` - объект не найден.
- `ZabbixConnectionError` - проблема соединения.
- `ZabbixAuthError` - проблема авторизации.
- `ZabbixAPIError` - ошибка JSON-RPC API Zabbix.

Каждая ошибка содержит:

- `message`;
- `explanation`;
- `context`;
- `as_dict()` для логирования или API-ответов.

## Упрощенная схема

```text
Zabbix(...)
  |
  v
login() -> user.login -> get_zabbix_result() -> api_key
  |
  v
get_group_info(group_name)
  |
  +-> get_group_id()              -> hostgroup.get
  +-> get_hosts_by_group_id()     -> host.get
  +-> get_triggers_by_group_id()  -> trigger.get
  +-> get_problems_by_group_id()  -> problem.get
  +-> get_scripts()               -> script.get
  |
  v
link problems -> triggers -> hosts
  |
  v
normalize_host()
  |
  +-> filter private items
  +-> normalize_items()
  |
  v
list[dict] for application
```

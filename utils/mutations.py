import logging
import time

logger = logging.getLogger(__name__)

interface_type = {
    "1": "агент",
    "2": "SNMP",
    "3": "IPMI",
    "4": "JMX",
}


def get_hours(seconds: int):
    hours = seconds // 3600
    minutes = (seconds - hours * 3600) // 60
    sec = seconds - 3600*hours - 60 * minutes
    return (f"{hours}ч {minutes}м {sec}с")


def convert_number(value, rule: dict):
    result = float(value)
    if "round" not in rule:
        return result
    if rule["round"] is None:
        return round(result)
    return round(result, int(rule["round"]))


def convert_on_off(value, rule: dict):
    on_value = rule.get("on_value", 1)
    on_label = rule.get("on_label", "ON")
    off_label = rule.get("off_label", "OFF")
    return on_label if int(value) == int(on_value) else off_label


def convert_duration(value, rule: dict):
    return get_hours(int(value))


ITEM_CONVERTERS = {
    "number": convert_number,
    "on_off": convert_on_off,
    "duration": convert_duration,
}


def normalize_items(items: list, item_transforms: dict | None = None) -> list:
    """
    Нормализует элементы данных Zabbix по переданной таблице преобразований.

    Параметры:
        items: Список словарей элементов данных. Функция ожидает, что у каждого
            элемента есть ключи:
            - key_: ключ элемента данных Zabbix, по нему ищется правило;
            - lastvalue: текущее значение, которое может быть преобразовано;
            - units: единицы измерения, будут заменены правилом при совпадении.
        item_transforms: Таблица правил преобразования или None. Если None или
            пустой словарь, функция вернет элементы без доменных
            преобразований. Таблицу можно загрузить в приложении из JSON,
            собрать из БД или сформировать вручную.

    Формат item_transforms:
        {
            "item.key": {
                "units": "ms",
                "converter": "number",
                "round": 2
            }
        }

    Поддерживаемые поля правила:
        units: Новые единицы измерения. Если поле отсутствует, старое значение
            item["units"] сохраняется.
        converter: Имя преобразователя значения lastvalue. Доступные значения:
            - number: приводит lastvalue к float и округляет при наличии round;
            - on_off: преобразует числовое значение в ON/OFF;
            - duration: преобразует секунды в строку вида "1ч 2м 3с".
        round: Только для converter="number". Если число - количество знаков
            после запятой. Если null/None - округление до целого. Если поле
            отсутствует - значение остается float без округления.
        on_value: Только для converter="on_off"; значение, считающееся ON.
            По умолчанию 1.
        on_label: Только для converter="on_off"; подпись для ON. По умолчанию
            "ON".
        off_label: Только для converter="on_off"; подпись для OFF. По умолчанию
            "OFF".

    Возвращает:
        Тот же список items, измененный на месте. Элементы, для key_ которых нет
        правила, остаются без изменений.
    """
    transforms = item_transforms or {}
    for item in items:
        rule = transforms.get(item["key_"])
        if not rule:
            continue

        item["units"] = rule.get("units", item.get("units", ""))
        converter_name = rule.get("converter")
        converter = ITEM_CONVERTERS.get(converter_name)
        if converter:
            item["lastvalue"] = converter(item["lastvalue"], rule)
    return items


def normalize_host(
    host: dict,
    item_transforms: dict | None = None,
    ignore_private_items: bool = True,
) -> dict:
    """
    Преобразует сырой словарь host из Zabbix API в структуру для приложения.

    Параметры:
        host: Словарь узла Zabbix. Функция ожидает поля:
            - name, host, hostid, status;
            - triggers: список триггеров, в каждом может быть problem;
            - interfaces: список интерфейсов с ip, dns и type;
            - tags, inventory, macros;
            - items: список элементов данных для передачи в normalize_items;
            - last_update: строка времени последнего обновления.
        item_transforms: Таблица правил преобразования элементов данных.
            Передается напрямую в normalize_items(). Если правила не переданы,
            элементы данных фильтруются по key_, но их units/lastvalue не
            преобразуются.
        ignore_private_items: Если True, элементы данных с key_, начинающимся
            с "_", исключаются из результата.

    Возвращает:
        Новый словарь с нормализованными полями host, interfaces, problems,
        items и служебными данными.
    """
    result = {}
    current_problems = []
    for trigger in host["triggers"]:
        if "problem" in trigger:
            current_problem = {
                "clock": trigger["problem"]["clock"],
                "acknowledged": trigger["problem"]["acknowledged"] == "1",
                "severity": trigger["problem"]["severity"],
                "tags": trigger["problem"]["tags"],
                "eventid": trigger["problem"]["eventid"]
            }
            try:
                #переделать на next c генератором
                current_problem["name"] = list(filter(
                    lambda tag: tag["tag"] == "name", trigger["problem"]["tags"]))[0]["value"]
                current_problem["duration"] = int(time.time()) - int(trigger["lastchange"]) + int(
                    list(filter(lambda tag: tag["tag"] == "base", trigger["problem"]["tags"]))[0]["value"])
                current_problem["base"] = list(filter(
                    lambda tag: tag["tag"] == "base", trigger["problem"]["tags"]))[0]["value"]


            except:
                logger.warning("Ошибка имени/продолжительности проблемы, используем стандартные")
                current_problem["name"] = trigger["problem"]["name"]
                current_problem["duration"] = int(
                    time.time()) - int(trigger["lastchange"])
            if "SLA" not in current_problem["name"]:  # костыль переделать
                current_problems.append(current_problem)
    result["name"] = host["name"]
    result["host"] = host["host"]
    result["hostid"] = host["hostid"]
    result["problems"] = current_problems
    result["interfaces"] = [{
        "host": interface["ip"] if interface["ip"] != "" else interface["dns"],
        "type": interface_type[interface["type"]]

    } for interface in host["interfaces"]]
    result["tags"] = host["tags"]
    result["inventory"] = host["inventory"]
    result["macros"] = host["macros"]
    result["status"] = host["status"]
    # result["scripts"] = host["scripts"]
    items = host["items"]
    if ignore_private_items:
        items = [item for item in items if not item["key_"].startswith("_")]
    result["items"] = normalize_items(
        items,
        item_transforms,
    )
    result["last_update"] = host["last_update"]
    return result

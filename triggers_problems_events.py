# zabbix_api/triggers.py
import logging
import time
from typing import List

from .http.http_api import APIClient
from .utils.response import get_zabbix_result

logger = logging.getLogger(__name__)


class ZabbixTriggersMixin():

    async def get_triggers_by_item_id(self, item_id: int | str, tags: List = []) -> List:
        """
        получаем список триггеров, связанных с элементом данных
        params:
            tags - для фильтрации
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "trigger.get",
            "params": {
                # value 0 - (default) OK, 1 - problem.
                "output": ["triggerid", "description", "value", "tags", "clock"],
                # "output": "extend",
                "itemids": [item_id],
                  "active": True,
                "tags": tags,
                "selectTags": "extend"
            },
            "auth": self.api_key,
            "id": 2
        }
        async with APIClient(self.api_url) as client:
            logger.debug("Requesting trigger.get from %s", self.api_url)
            response = await client.post("", payload)
            logger.debug("trigger.get response: %s", response)
            return get_zabbix_result(response, payload)

    async def get_problems_by_trigger_id(self, trigger_id: int | str,  time_from: int = int(time.time()) - 30 * 24 * 3600, time_till: int = int(time.time())):
        """
        Получить историю проблем по id триггера
        показывает только недавние или текущие проблемы
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": "extend",
                "objectids": [trigger_id],
                "source": 0,  # источник события триггер
                "object": 0,  # тип объекта триггер
                "recent": True,  # возвращаем и решенные проблемы за период
                "time_from": time_from,
                "time_till": time_till,
                # "sortfield": "clock",
                "sortorder": "DESC"
            },
            "auth": self.api_key,
            "id": 3
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)

    async def get_events_by_trigger_id(self, trigger_id: int | str,  time_from: int = int(time.time()) - 30 * 24 * 3600, time_till: int = int(time.time())):
        """
        Получить историю событий по id триггера
        в текущей реализации собираем события проблемы и восстановления
        события генерируются триггерами и хаускипер хранит события в отличие от проблем
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "output": ["eventid", "clock", "value", "r_eventid", "name"],
                "objectids": [trigger_id],
                "source": 0,
                "object": 0,
                "time_from": time_from,
                "time_till": time_till,
                "sortfield": "clock",
                "sortorder": "ASC",
                # Значение 1 соответствует проблемным событиям(PROBLEM). Значение 0 - событиям восстановления(OK).
                # "value": 1
            },
            "auth": self.api_key,
            "id": 2
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)

    async def get_triggers_by_group_id(self, group_id: str | int) -> List:
        """
        Получить активные сработавшие триггеры группы узлов
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "trigger.get",
            "params": {
                "only_true": 1,
                "monitored": 1,
                "active": 1,
                "skipDependent": 1,
                "groupids": [group_id],
                "selectHosts": ["hostid"],
                "output": ["trigerrid", "description", "status", "lastchange", "priority", "state", "value"],
                "filter": {
                    "value": 1
                },
                "sortfield": "priority",
                "sortorder": "DESC"
            },
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)

    async def get_problems_by_group_id(self, group_id: int | str) -> List:
        """
        Получить активные пробюлемы группы узлов
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": "extend",
                "selectAcknowledges": "extend",
                "selectTags": "extend",
                "groupids": [group_id],
                "recent": True
            },
            "auth": self.api_key,
            "id": 1
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)

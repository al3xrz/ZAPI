# zabbix_api/items.py
from .base import ZabbixBase
from .errors.exceptions import ZabbixNotFoundError
from .http.http_api import APIClient
from .utils.response import get_zabbix_result
import time


class ZabbixItemsMixin():

    async def get_items_extended(self, hostid: int | str):
        """
        получить расширенный список текущих значений элементов данных
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "hostids": hostid,
                "output": ["itemid", "key_", "lastvalue", "name", "tags", "lastclock"],
                "selectTags": "extend"
            },
            "id": 1,
            "auth": self.api_key
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            result = get_zabbix_result(response, payload)
            if len(result) != 0:
                return result
            raise ZabbixNotFoundError(f"Items for hostid={hostid} not found")



    async def get_item_by_key(self, key_: int | str, hostid: int | str):
        """
        Получить элемент данных у заданного хоста по ключу
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["name", "itemid", "name"],
                "hostids": hostid,
                "search": {
                    "key_": key_
                },
                "sortfield": "name"
            },
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)[0]

    async def get_history(self,
                          itemid: int | str,
                          type: int = 0,
                          time_from: int = int(time.time()) - 3600,
                          time_till=int(time.time())
                          ):
        """
        Получить историю заданного по id элемента данных
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "history.get",
            "params": {
                "output": "extend",
                "history": type,
                "itemids": itemid,
                "sortfield": "clock",
                "sortorder": "DESC",
                "time_from": time_from,
                "time_till": time_till
            },
            "id": 1,
            "auth": self.api_key
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)

    
    
    async def get_trend(self,
                        itemid: int | str,
                        time_from: int = int(time.time()) - 24 * 3600,
                        time_till: int = int(time.time())
                        ):
        """
        Получить тренд заданного по id элемента данных
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "trend.get",
            "params": {
                "output": "extend",
                "itemids": itemid,
                "sortfield": "clock",
                "sortorder": "DESC",
                "time_from": time_from,
                "time_till": time_till
            },
            "id": 1,
            "auth": self.api_key
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)

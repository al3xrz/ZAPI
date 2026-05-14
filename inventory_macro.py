# zabbix_api/inventory.py
from .base import ZabbixBase
from .http.http_api import APIClient
from .utils.response import get_zabbix_result


class ZabbixInventoryMixin():
    async def update_macro(self, hostid: int | str, macro: str, value: int | str):
        """
        Обновляем макрос (одну пару ключ - значение) по hostid
        """
        host = await self._get_host_by_id(hostid)
        # можно заменить на dict.update
        for item in host["macros"]:
            if item["macro"] == macro:
                item["value"] = value
                break
        else:
            host["macros"].append({"macro": macro, "value": value})
        ###############################
        payload = {
            "jsonrpc": "2.0",
            "method": "host.update",
            "params": {
                "hostid": hostid,
                "macros": host["macros"]
            },
            "auth": self.api_key,
            "id": 1
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return get_zabbix_result(response, payload)

    async def update_inventory(self, hostid: str | int, key: str, value: int | str):
        """
        Обновляем запись инвентаризации (одну пару ключ - значение) по hostid
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.update",
            "params": {
                "hostid": hostid,
                "inventory_mode": 0,
                "inventory": {
                    key: value
                }
            },
            "auth": self.api_key,
            "id": 1
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
        return get_zabbix_result(response, payload)

# zabbix_api/hosts.py
from .errors.exceptions import ZabbixError, ZabbixNotFoundError
from .http.http_api import APIClient


class ZabbixHostsMixin():
    async def get_hosts_by_group_id(self, group_id: str | int) -> list:
        """
        Получаети список узлов по id группы zabbix
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "groupids": [group_id],
                "output": [
                    "hostid",
                    "host",
                    "name",
                    "status"
                ],
                "selectInterfaces": ["interfaceid", "ip", "dns", "type"],
                "selectTags": ["tag", "value"],
                "selectMacros": ["macro", "value"],
                "selectInventory": [
                    "location_lat",
                    "location_lon",
                    "location",
                    "notes"
                ],
                "selectItems": [
                    "itemid",
                    "name",
                    "key_",
                    "units",
                    "lastvalue",
                    "value_type",
                    "description",
                    "status"
                ],
            },
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            if "result" in response:
                return response["result"]
            else:
                raise ZabbixError(response["error"]["data"])

    async def _get_host_by_id(self, hostid: int | str) -> dict:
        """
        Получает подробную информацию о хосте по hostid
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "hostids": hostid,
                "output": ["hostid", "name", "host", "inventory"],
                "selectMacros": [
                    "macro",
                    "value"
                ],
                "selectInventory": ["location", "location_lat", "location_lon", "note"],
                "selectItems": [
                    "key_",
                    "name",
                    "status",
                    "value_type",
                    "description",
                    "lastvalue",
                    "units"
                ]
            },
            "auth": self.api_key,
            "id": 1
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            print(response)
            if "result" in response:
                if len(response["result"][0]) != 0:
                    return response["result"][0]
                else:
                    raise ZabbixNotFoundError(
                        f"Host with id={hostid} not found")
            else:
                raise ZabbixError(response["error"]["data"])



 

    
# zabbix_api/scripts.py
from .base import ZabbixBase
from .http.http_api import APIClient


class ZabbixScriptsMixin():

    async def get_scripts(self, groupid: int | str):
        """
        Получить список доступных для группы скриптов
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "script.get",
            "params": {
                "groupids": [groupid],
                "output": ["name", "scriptid"]
            },
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return response["result"]

    async def execute_script(self, hostid: int | str, scriptid: int | str):
        """
        Выполнить скрипт scriptid на заданном по hostid хосте
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "script.execute",
            "params": {
                "scriptid": scriptid,
                "hostid": hostid
            },
            "auth": self.api_key,
            "id": 1
        }

        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            return response["result"]

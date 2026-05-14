# zabbix_api/auth.py
from .base import ZabbixBase
from .errors.exceptions import ZabbixError
from .http.http_api import APIClient

class ZabbixAuthMixin():
    
    async def login(self):
        """
        Авторизация в zabbix api в зависимости от версии 
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "username": self.username,
                "password": self.password
            },
            "id": 1}

        if self.api_version == 5:
            payload = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": self.username,
                    "password": self.password
                },
                "id": 1, }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            print(response)
            if "result" in response:
                self.api_key = response["result"]
            else:
                raise ZabbixError(response["error"]["data"])

    async def logout(self):
        """
        Выход из zabbix api
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "user.logout",
            "params": [],
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            print(response)
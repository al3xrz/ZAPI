# zabbix_api/base.py
from .http.http_api import APIClient

class ZabbixBase:
    @staticmethod
    async def get_api_version(url):
        """
        Функция не требующая авторизации, используется для проверки доступности API
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "apiinfo.version",
            "params": [],
            "id": 1
        }
        response = {}
        async with APIClient(f"{url}") as client:
            try:
                response = await client.post("api_jsonrpc.php", payload)
            except:
                response = {}
        return response

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        api_version: int = 7,
        item_transforms: dict | None = None,
    ):
        self.server_address = url
        self.api_url = f"{url}/api_jsonrpc.php"
        self.username = username
        self.password = password
        self.api_key = ""
        self.api_version = api_version
        self.item_transforms = item_transforms or {}
        
   

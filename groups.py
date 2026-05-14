# zabbix_api/groups.py
from .errors.exceptions import ZabbixError, ZabbixNotFoundError
from .http.http_api import APIClient
from datetime import datetime
from zoneinfo import ZoneInfo
from .utils.mutations import normalize_host

class ZabbixGroupsMixin():
    async def get_group_id(self, group_name: str) -> str:
        """
        Получаем id группы узлов по имени
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": "extend",
                "filter": {
                    "name": [
                        group_name
                    ]
                }
            },
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            print(response)
            if len(response["result"]) == 1:
                return response["result"][0]["groupid"]
            else:
                raise ZabbixNotFoundError(f'Group \"{group_name}\" not found')
    
    async def get_group_info(self, group_name: str, item_transforms: dict | None = None):
        """
        Основная функция - формирует подробный список узлов с элементами данных и текущими проблемами по имени группы zabbix

        item_transforms - необязательная таблица преобразований элементов
        данных для этого вызова. Если не передана, используется
        self.item_transforms, заданный при создании экземпляра API.
        """
        
        group_id = await self.get_group_id(group_name)
        hosts = await self.get_hosts_by_group_id(group_id)
        triggers = await self.get_triggers_by_group_id(group_id)
        problems = await self.get_problems_by_group_id(group_id)
        # scripts = await self.get_scripts(group_id)
        timezone = ZoneInfo("Europe/Moscow")
        for trigger in triggers:
            trigger["problem"] = list(filter(
                lambda problem: problem["objectid"] == trigger["triggerid"], problems))[0]
        for host in hosts:
            host["triggers"] = list(filter(
                lambda trigger: trigger["hosts"][0]["hostid"] == host["hostid"], triggers))
            host["last_update"] = datetime.now(
                timezone).strftime('%Y-%m-%d %H:%M:%S')
        # for host in hosts:
        #     host["scripts"] = scripts
        transforms = item_transforms if item_transforms is not None else self.item_transforms
        results = [normalize_host(host, transforms) for host in hosts]
        return results

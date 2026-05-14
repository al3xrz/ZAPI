# zabbix_api/graphs.py
import logging

from .base import ZabbixBase
from .http.http_api import APIClient
from .errors.exceptions import ZabbixAuthError, ZabbixConnectionError, ZabbixError, ZabbixNotFoundError
from .utils.response import get_zabbix_result
from typing import List, Dict

logger = logging.getLogger(__name__)


class ZabbixGraphsMixin():
    async def get_graphs_by_hostid(self, hostid: int | str):
        payload = {
            "jsonrpc": "2.0",
            "method": "graph.get",
            "params": {
                "output": "extend",
                "hostids": hostid,
                "sortfield": "name"
            },
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            logger.debug("graph.get response: %s", response)
            return get_zabbix_result(response, payload)

    async def get_graph_values(self, graphids):
        payload = {
            "jsonrpc": "2.0",
            "method": "graphitem.get",
            "params": {
                "output": "extend",
                "graphids": graphids

            },
            "auth": self.api_key,
            "id": 1
        }
        async with APIClient(self.api_url) as client:
            response = await client.post("", payload)
            logger.debug("graphitem.get response: %s", response)
            return get_zabbix_result(response, payload)

    async def get_chart(self, itemid: int | str, time_from: str = 'now-7d', time_till: str = 'now', width: int | str = 1024, height: int | str = 200) -> bytes:
        """
        Получает график с проверкой сессии
        """
        async with APIClient(self.server_address) as client:
            # Логинимся
            login_success = await client.web_login(username=self.username, password=self.password)
            if not login_success:
                raise RuntimeError("Login failed")
            
            # Проверяем сессию
            session_valid = await client.check_session_valid()
            if not session_valid:
                raise RuntimeError("Session is not valid after login")
            
            # Отладочная информация о сессии
            await client.debug_session()
            
            # Получаем график
            chart_image = await client.get_zabbix_chart(
                itemids=[itemid],
                time_from=time_from,
                time_till=time_till,
                width=width,
                height=height
            )
            
            logger.info("Chart successfully retrieved")
            return chart_image

    async def get_charts(self, itemids: List[int | str], time_from='now-1h', time_till='now', width=800, height=200) -> Dict[str, bytes]:
        """
        Получает набор готовых графиков заданных itemid из Zabbix c заданными параметрами в виде словаря itemid : байтовый png
        у пользователя должны быть права на фронтенд
        """
        async with APIClient(self.server_address) as client:
            # качаем PNG
            await client.web_login(username=self.username, password=self.password)
            await client.debug_session()
            # Получаем график
            result = dict()
            for itemid in itemids:
                chart_image = await client.get_zabbix_chart(
                    # Замените на реальный ID элемента данных
                    itemids=[itemid],
                    time_from=time_from,
                    time_till=time_till,
                    width=width,
                    height=height
                )
                result[itemid] = chart_image
            return result

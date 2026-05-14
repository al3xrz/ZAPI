# zabbix_api/auth.py
import logging

from .base import ZabbixBase
from .http.http_api import APIClient
from .utils.response import get_zabbix_result

logger = logging.getLogger(__name__)


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
            logger.debug("user.login response: %s", response)
            self.api_key = get_zabbix_result(response, payload)

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
            logger.debug("user.logout response: %s", response)
            get_zabbix_result(response, payload)

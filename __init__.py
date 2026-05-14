from .errors.exceptions import (
    ZabbixAPIError,
    ZabbixAuthError,
    ZabbixBaseException,
    ZabbixConnectionError,
    ZabbixError,
    ZabbixNotFoundError,
)

from .base import ZabbixBase
from .auth import ZabbixAuthMixin
from .groups import ZabbixGroupsMixin
from .hosts import ZabbixHostsMixin
from .items import ZabbixItemsMixin
from .graphs_charts import ZabbixGraphsMixin
from .triggers_problems_events import ZabbixTriggersMixin
from .inventory_macro import ZabbixInventoryMixin
from .scripts import ZabbixScriptsMixin

class Zabbix(
    ZabbixBase,
    ZabbixAuthMixin,
    ZabbixGroupsMixin,
    ZabbixHostsMixin,
    ZabbixItemsMixin,
    ZabbixGraphsMixin,
    ZabbixTriggersMixin,
    ZabbixInventoryMixin,
    ZabbixScriptsMixin
):
    """Основной класс Zabbix API, объединяющий всю функциональность"""
    pass

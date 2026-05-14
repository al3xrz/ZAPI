from typing import Any

from ..errors.exceptions import ZabbixAPIError, ZabbixError


def get_zabbix_result(response: dict[str, Any], payload: dict[str, Any]) -> Any:
    """Вернуть result из JSON-RPC ответа Zabbix или выбросить понятную ошибку."""
    if "result" in response:
        return response["result"]

    if "error" in response:
        raise ZabbixAPIError(
            response["error"],
            method=payload.get("method"),
            params=payload.get("params"),
        )

    raise ZabbixError(
        "Некорректный ответ Zabbix API",
        context={
            "method": payload.get("method"),
            "params": payload.get("params"),
            "response": response,
        },
    )

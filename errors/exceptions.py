from typing import Any


class ZabbixBaseException(Exception):
    """Базовое исключение для ошибок при работе с Zabbix API.
       поля context и explanation создаем сами, в родительском классе их нет
    """

    default_message = "Ошибка при работе с Zabbix API"
    explanation = "Произошла ошибка, которую не удалось отнести к более точному типу."



    def __init__(
        self,
        message: str | None = None, 
        context: dict[str, Any] | None = None,
        explanation: str | None = None,
    ):
        self.message = message or self.default_message
        self.explanation = explanation or self.explanation
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.explanation:
            parts.append(f"Пояснение: {self.explanation}")
        if self.context:
            parts.append(f"Контекст: {self.context}")
        return " | ".join(parts)

    def as_dict(self) -> dict[str, Any]:
        """Вернуть ошибку в виде словаря для логирования или API-ответа."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "explanation": self.explanation,
            "context": self.context,
        }


class ZabbixError(ZabbixBaseException):
    """Общая ошибка Zabbix."""

    default_message = "Ошибка Zabbix"
    explanation = "Zabbix вернул ошибку или операция завершилась неуспешно."


class ZabbixNotFoundError(ZabbixBaseException):
    """Ресурс не найден в Zabbix."""

    default_message = "Ресурс Zabbix не найден"
    explanation = (
        "Запрошенный объект отсутствует, недоступен пользователю или фильтр запроса "
        "не совпал ни с одной записью."
    )


class ZabbixConnectionError(ZabbixBaseException):
    """Проблема соединения с Zabbix."""

    default_message = "Не удалось подключиться к Zabbix"
    explanation = (
        "Проверьте адрес сервера, доступность сети, TLS-сертификат и таймауты."
    )


class ZabbixAuthError(ZabbixBaseException):
    """Ошибка авторизации в Zabbix."""

    default_message = "Ошибка авторизации в Zabbix"
    explanation = (
        "Проверьте логин, пароль, API-токен и права пользователя на выполнение запроса."
    )


class ZabbixAPIError(ZabbixBaseException):
    """Ошибка, которую вернул JSON-RPC API Zabbix."""

    default_message = "Zabbix API вернул ошибку"
    explanation = (
        "Сервер Zabbix принял запрос, но вернул JSON-RPC ошибку. Подробности находятся "
        "в error_data."
    )

    def __init__(
        self,
        error_data: dict[str, Any] | str,
        method: str | None = None,
        params: dict[str, Any] | list[Any] | None = None,
    ):
        message = self._build_message(error_data, method)
        context = {
            "method": method,
            "params": params,
            "error_data": error_data,
        }
        super().__init__(message=message, context=context)

    @staticmethod
    def _build_message(error_data: dict[str, Any] | str, method: str | None) -> str:
        method_part = f" в методе {method}" if method else ""
        if isinstance(error_data, dict):
            code = error_data.get("code")
            message = error_data.get("message")
            data = error_data.get("data")
            details = ", ".join(
                str(part) for part in (message, data) if part not in (None, "")
            )
            if code is not None and details:
                return f"Zabbix API error{method_part} [{code}]: {details}"
            if details:
                return f"Zabbix API error{method_part}: {details}"
        return f"Zabbix API error{method_part}: {error_data}"

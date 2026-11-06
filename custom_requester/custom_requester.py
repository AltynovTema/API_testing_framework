"""
Кастомная обёртка над HTTP-запросами с автоматическим логированием.

Архитектурное назначение:
    Отправляет HTTP-запросы через requests.Session и логирует их детали
    (метод, URL, заголовки, тело, статус-код, время выполнения, ответ).

    Логика логирования вынесена в utils.logger:
    - Console Handler → человекочитаемый текст (REQUEST/RESPONSE с метриками).
    - File Handler → структурированный JSON (одна строка = один JSON-объект).
    - Allure → dict-структура как JSON-вложение.

    Каждая запись = ОДИН вызов logger.info() для текста + ОДИН вызов для JSON.
    Это исключает перемешивание строк при параллельных запусках.

Пример использования:
    >>> from utils.logger import get_logger
    >>> requester = CustomRequester(session, base_url)
    >>> response = requester.send_request("POST", "/register", data=payload)
"""

import json
import logging
import time

from utils.logger import get_logger, log_request_and_response


class CustomRequester:
    """
    Обёртка над requests.Session для отправки HTTP-запросов с логированием.

    Инкапсулирует:
    - Базовые заголовки для всех запросов.
    - Формирование полных URL из base_url + endpoint.
    - Проверку ожидаемого статус-кода.

    Логирование запросов/ответов выполняется через utils.logger.log_request_and_response.
    """

    BASE_HEADERS: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    def __init__(self, session, base_url: str):
        """
        Инициализация кастомного запросчика.

        :param session: Объект requests.Session() для поддержания сессии.
        :param base_url: Базовый URL API.
        """
        self.session = session
        self.base_url = base_url
        self.headers = self.BASE_HEADERS.copy()
        self.session.headers.update(self.BASE_HEADERS)
        self.logger: logging.Logger = get_logger(__name__)

    def _reset_headers(self):
        """Сбрасывает заголовки сессии к базовым для изоляции между тестами."""
        self.session.headers.clear()
        self.session.headers.update(self.headers)

    def send_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        expected_status: int = 200,
        need_logging: bool = True,
        **kwargs
    ):
        """
        Отправляет HTTP-запрос и проверяет статус-код.

        :param method: HTTP-метод (GET, POST, PUT, DELETE).
        :param endpoint: Путь к ресурсу (например, /api/users).
        :param data: Тело запроса (dict, автоматически сериализуется в JSON).
        :param params: Query-параметры (dict, добавляются в URL).
        :param expected_status: Ожидаемый статус-код (по умолчанию 200).
        :param need_logging: Включить логирование запроса/ответа (по умолчанию True).
        :return: Объект response библиотеки requests.
        :raises ValueError: Если полученный статус-код не совпадает с ожидаемым.
        """
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        response = self.session.request(
            method=method, url=url, json=data, params=params, **kwargs
        )

        end_time_ms = round((time.time() - start_time) * 1000, 2)

        if need_logging:
            log_request_and_response(self.logger, response, end_time_ms)

        if response.status_code != expected_status:
            error_msg = (
                f"\nUnexpected status code: {response.status_code}. "
                f"Expected status code: {expected_status}"
            )

            try:
                server_message = response.json().get("message", response.text)
                error_msg += f"\nServer msg: {server_message}"
            except (json.JSONDecodeError, ValueError):
                error_msg += f"\nResponse body: {response.text}"

            raise ValueError(error_msg)

        return response

    def _update_session_headers(self, headers: dict[str, str]):
        """
        Добавляет или обновляет заголовки в сессии.

        Используется после авторизации для добавления токена.

        :param headers: Словарь заголовков для добавления.
        """
        self.session.headers.update(headers)

    def _reset_headers(self):
        """Сбрасывает заголовки и Cookie сессии к базовым для изоляции между тестами."""
        self.session.headers.clear()
        self.session.headers.update(self.headers)
        self.session.cookies.clear()

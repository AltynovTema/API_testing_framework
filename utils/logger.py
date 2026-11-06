import json
import logging
import logging.handlers
import os
import re

# ==============================================================================
# Константы
# ==============================================================================
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "by_tests.log")
LOG_MAX_BYTES = 5 * 1024 * 1024      # 5 МБ
LOG_BACKUP_COUNT = 3                  # Количество хранимых архивных файлов
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATEFMT = "%d-%m-%Y %H:%M:%S"


# ==============================================================================
# 1. Фильтр для удаления ANSI-кодов из файловых логов
# ==============================================================================
class AnsiColorFilter(logging.Filter):
    """
    Фильтр, который удаляет ANSI-управляющие последовательности (цвета)
    из записей логов перед их записью в файл.

    Если в коде используется раскраска (например, f"{GREEN}200{RESET}"),
    эти невидимые символы попадают в объект LogRecord. FileHandler запишет их в файл,
    превратив лог в нечитаемый набор символов вроде [32m200[0m.
    Этот фильтр работает как "таможня": он очищает сообщение только для файлового вывода,
    не затрагивая консоль.
    """
    # Регулярное выражение для поиска ANSI-кодов:
    # \x1b (или \033) — управляющий символ ESC (ASCII 27), начало любой ANSI-последовательности.
    # \[              — открывающая квадратная скобка (начало последовательности CSI).
    # [0-9;]*         — ноль или более цифр и точек с запятой (параметры цвета/стиля).
    # m               — завершающий символ последовательности.
    ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Модифицирует атрибут msg объекта записи, удаляя совпадения с регулярным выражением.
        :param record: Объект LogRecord, который генерирует логгер.
        :return: bool: True, чтобы разрешить прохождение записи дальше по конвейеру.
        """
        record.msg = self.ANSI_ESCAPE.sub('', str(record.msg))
        if record.args:
            record.args = tuple(
                self.ANSI_ESCAPE.sub('', str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


# ==============================================================================
# 2. Форматтер для добавления цветов в консольный вывод
# ==============================================================================
class ColorFormatter(logging.Formatter):
    """
    Форматтер, который оборачивает готовую строку лога в ANSI-цвета
    в зависимости от уровня важности (INFO, ERROR и т.д.).

    Архитектурное отличие от AnsiColorFilter:
    Мы НЕ мутируем record.msg. Мы сначала получаем чистую строку от родителя,
    а потом оборачиваем её в цвет. Это гарантирует, что цвета не "протекут" в файл,
    даже если этот форматтер случайно будет использован не там.
    """
    COLORS = {
        'DEBUG':    '\033[36m',     # Голубой (Cyan)
        'INFO':     '\033[32m',     # Зелёный
        'WARNING':  '\033[33m',     # Жёлтый
        'ERROR':    '\033[31m',     # Красный
        'CRITICAL': '\033[1;31m',   # Ярко-красный (жирный)
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        formatted_msg = super().format(record)
        return f"{color}{formatted_msg}{self.RESET}"


# ==============================================================================
# 3. Функция получения логгера
# ==============================================================================
def get_logger(logger_name: str) -> logging.Logger:
    """
    Возвращает именованный логгер.

    :param logger_name: имя логгера (обычно __name__).
    :return: экземпляр logging.Logger.
    """
    return logging.getLogger(logger_name)


# ==============================================================================
# 3. Функция настройки логгера
# ==============================================================================
def setup_logger(logger_name: str = "custom_requester.custom_requester") -> logging.Logger:
    """
    Создаёт и настраивает именованный логгер с двумя обработчиками:
      - StreamHandler  → цветной вывод в консоль (уровень DEBUG);
      - RotatingFileHandler → вывод в файл без цветов (уровень INFO) с ротацией.

    Повторный вызов для уже настроенного логгера безопасен:
    если у логгера уже есть обработчики, настройка пропускается.

    :param logger_name: имя логгера. Должно совпадать с __name__ модуля,
                        в котором ведётся логирование.
    :return: настроенный экземпляр logging.Logger.
    """
    logger = logging.getLogger(logger_name)

    # Защита от повторной настройки (например, при повторном импорте conftest.py)
    if logger.handlers:
        return logger

    # Гарантируем существование директории для логов
    os.makedirs(LOG_DIR, exist_ok=True)

    logger.setLevel(logging.DEBUG)

    # --- Консольный обработчик (с цветами) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColorFormatter(fmt=LOG_FORMAT, datefmt=LOG_DATEFMT))
    logger.addHandler(console_handler)

    # --- Файловый обработчик (без цветов, с ротацией) ---
    ansi_filter = AnsiColorFilter()
    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE,
        encoding='utf-8',
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATEFMT))
    file_handler.addFilter(ansi_filter)
    logger.addHandler(file_handler)

    return logger


# ==============================================================================
# 4. Статические хелперы для парсинга запросов/ответов
# ==============================================================================
def extract_request_body(body) -> str | None:
    """
    Извлекает тело запроса из объекта request.

    :param body: Тело запроса (bytes, str или None).
    :return: Декодированная строка тела или None.
    """
    if body is None:
        return None

    if isinstance(body, bytes):
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            return None
    elif isinstance(body, str):
        return body

    return None


def parse_response_body(raw_text: str) -> str | dict:
    """
    Парсит тело ответа: возвращает JSON-объект или сырую строку.

    :param raw_text: Тело ответа как строка.
    :return: Декодированный JSON или исходная строка.
    """
    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, ValueError):
        return raw_text


def get_current_test_name() -> str:
    """Извлекает имя текущего теста из переменной окружения pytest."""
    test_env = os.environ.get("PYTEST_CURRENT_TEST", "")
    return f"pytest {test_env.replace(' (call)', '')}" if test_env else "pytest"


# ==============================================================================
# 5. Функция логирования HTTP-запроса и ответа (в формате curl)
# ==============================================================================
def log_request_and_response(
    logger: logging.Logger,
    response,
    end_time_ms: float,
) -> None:
    """
    Логирует детали запроса и ответа в формате, удобном для отладки.
    Формат имитирует curl-команду, которую можно скопировать и запустить в терминале.

    :param logger: экземпляр логгера, в который выполняется запись.
    :param response: объект response библиотеки requests.
    :param end_time_ms: время выполнения запроса в миллисекундах.
    """
    try:
        request = response.request
        test_name = get_current_test_name()

        # Формируем строку заголовков в формате curl
        headers = " \\\n".join(
            [f"-H '{header}: {value}'" for header, value in request.headers.items()]
        )

        # Извлекаем тело запроса
        body = extract_request_body(request.body)
        body_str = f"-d '{body}' \\\n" if body and body != '{}' else ''

        # Блок REQUEST
        logger.info(f"\n{'=' * 40} REQUEST {'=' * 40}")
        logger.info(
            f"{test_name}\n"
            f"curl -X {request.method} '{request.url}' \\\n"
            f"{headers} \\\n"
            f"{body_str}"
        )

        # Извлекаем данные ответа
        response_status = response.status_code
        is_success = response.ok
        response_data = parse_response_body(response.text)

        # Блок RESPONSE
        logger.info(f"\n{'=' * 40} RESPONSE {'=' * 40}")
        if not is_success:
            logger.info(
                f"\tSTATUS_CODE: {response_status}\n"
                f"\tDATA: {response_data}"
            )
        else:
            logger.info(
                f"\tSTATUS_CODE: {response_status}\n"
                f"\tTOTAL_TIME: {end_time_ms} ms\n"
                f"\tDATA:\n{response_data}"
            )

        logger.info(f"{'=' * 80}\n")

        # Allure-вложение
        attach_to_allure(test_name, request, response, end_time_ms)

    except Exception as e:
        # Логирование — вспомогательная операция; её сбой не должен ронять тест.
        logger.error(f"Logging failed: {type(e).__name__} - {e}")


# ==============================================================================
# 6. Allure-вложения
# ==============================================================================
def attach_to_allure(
    test_name: str,
    request,
    response,
    end_time_ms: float,
) -> None:
    """
    Прикрепляет данные запроса/ответа к отчёту Allure.

    :param test_name: имя текущего теста.
    :param request: объект request из response.request.
    :param response: объект response библиотеки requests.
    :param end_time_ms: время выполнения запроса в миллисекундах.
    """
    try:
        import allure

        payload = {
            "test": test_name,
            "request": {
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers),
                "body": extract_request_body(request.body),
            },
            "response": {
                "status_code": response.status_code,
                "success": response.ok,
                "total_time_ms": end_time_ms,
                "headers": dict(response.headers),
                "body": parse_response_body(response.text),
            },
        }

        allure.attach(
            json.dumps(payload, ensure_ascii=False, default=str),
            name=f"HTTP {payload['request']['method']}",
            attachment_type=allure.attachment_type.JSON,
        )
    except ImportError:
        pass
    except Exception:
        pass
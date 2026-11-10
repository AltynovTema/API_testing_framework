# Конфигурация pytest-фреймворка.
import os

import pytest
import requests

from clients.api_manager import ApiManager
from utils.data_generator import DataGenerator

from utils.logger import setup_logger

# Глобальная настройка логгера при загрузке conftest.py
setup_logger("custom_requester.custom_requester")

# Pytest Fixtures
@pytest.fixture(scope="function")
def http_session() -> requests.Session:
    """
    Создаёт объект requests.Session().

    Сессия позволяет сохранять cookies и заголовки между запросами.
    scope="session" — создаётся один раз на весь прогон тестов.
    """
    session = requests.Session()
    yield session
    session.close()

@pytest.fixture(scope="function")
def api_manager(http_session: requests.Session) -> ApiManager:
    """Предоставляет готовый ApiManager с инициализированной сессией."""
    return ApiManager(http_session)

@pytest.fixture(scope="function")
def user_generator() -> dict:
    """
    Генерирует уникальные данные пользователя для каждого теста.

    scope="function" — данные пересоздаются для каждого тестового метода.
    """
    password = DataGenerator.generate_password()
    return {
        "email": DataGenerator.generate_email(),
        "fullName": DataGenerator.generate_full_name(),
        "password": password,
        "passwordRepeat": password,
        "roles": ["USER"],
    }

@pytest.fixture(scope="function")
def registered_user(
    api_manager: ApiManager, user_generator
) -> dict:
    """
    Регистрирует нового пользователя и добавляет server-generated поле 'id'.

    Цепочка фикстур: user_for_tests -> api_manager -> registered_user.
    """
    response = api_manager.auth_api.register_user(user_generator).json()
    user_generator["id"] = response["id"]
    return user_generator

@pytest.fixture(scope="function")
def authenticated_user(
        api_manager: ApiManager, registered_user
) -> dict:
    """
    Аутентифицирует нового пользователя в системе и добавляет Barer-token и refrash-token доступа.

    Цепочка фикстур: user_for_tests -> api_manager -> registered_user -> authenticated_user.
    """
    api_manager.auth_api.authenticate((registered_user["email"], registered_user["password"]))
    return registered_user

@pytest.fixture(scope="session")
def unauthenticated_api_manager(registered_user):
    """
    Предоставляет ApiManager без авторизации (чистая сессия).
    Не зависит от зарегистрированных пользователей.
    """
    session = requests.Session()
    try:
        yield ApiManager(session)
    finally:
        session.close()

@pytest.fixture(scope="function")
def super_admin_http_session() -> requests.Session:
    """
    Создаёт объект requests.Session() для SUPER_ADMIN.

    Сессия позволяет сохранять cookies и заголовки между запросами.
    Создает отдельную сессию для SUPER_ADMIN, чтобы не смешивать токены.
    """
    session = requests.Session()
    yield session
    session.close()

@pytest.fixture(scope="function")
def superadmin_api_manager(super_admin_http_session: requests.Session) -> ApiManager:
    """
    Предоставляет ApiManager с правами SUPER_ADMIN.
    Использует отдельную сессию super_admin_http_session.
    """
    admin_api_manager = ApiManager(super_admin_http_session)

    # Берем креды из .env
    username = os.getenv("SUPER_ADMIN_USERNAME")
    password = os.getenv("SUPER_ADMIN_PASSWORD")
    assert username and password, "Не найдены креды SUPER_ADMIN в .env"

    # Авторизуемся
    admin_api_manager.auth_api.authenticate((username, password))

    return admin_api_manager

@pytest.fixture(scope="function")
def created_genre(superadmin_api_manager: ApiManager):
    """
    Создает новый жанр и удаляет его после теста.
    Использует права SUPER_ADMIN
    """
    # Получаем уникальное имя для жанра
    genre_name = DataGenerator.generate_genre_name()

    # Создаем новый жанр
    genre_data = superadmin_api_manager.genres_api.create_genre(genre_name).json()

    yield genre_data

    # Teardown: удаляем жанр
    superadmin_api_manager.genres_api.delete_genre(genre_data[id])



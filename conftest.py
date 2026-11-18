# Конфигурация pytest-фреймворка.
import os
import pytest
import requests
import random
from dotenv import load_dotenv

# Загружаем переменные из .env в окружение в самом начале
load_dotenv()

# Импортируем нужные модули
from clients.api_manager import ApiManager
from utils.data_generator import DataGenerator

from utils.logger import setup_logger

# Глобальная настройка логгера при загрузке conftest.py
setup_logger("custom_requester.custom_requester")

# Экземпляр генератора данных (общий для всех тестов)
data_generator = DataGenerator()

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
    password = data_generator.generate_password()
    return {
        "email": data_generator.generate_email(),
        "fullName": data_generator.generate_full_name(),
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
def unauthenticated_api_manager():
    """
    Предоставляет ApiManager без авторизации (чистая сессия).
    Не зависит от зарегистрированных пользователей.
    """
    session = requests.Session()
    try:
        yield ApiManager(session)
    finally:
        session.close()

@pytest.fixture(scope="session")
def super_admin_http_session() -> requests.Session:
    """
    Создаёт объект requests.Session() для SUPER_ADMIN.

    Сессия позволяет сохранять cookies и заголовки между запросами.
    Создает отдельную сессию для SUPER_ADMIN, чтобы не смешивать токены.
    """
    session = requests.Session()
    yield session
    session.close()

@pytest.fixture(scope="session")
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

@pytest.fixture(scope="session")
def create_genre(superadmin_api_manager: ApiManager):
    """
    Создаёт жанр один раз на весь прогон и удаляет после всех тестов.
    """
    genre_name = data_generator.generate_genre_name()

    response = superadmin_api_manager.genres_api.create_genre(genre_name)
    assert response.status_code == 201, f"Не удалось создать жанр: {response.text}"
    genre_data = response.json()
    assert "id" in genre_data, f"В ответе нет id: {genre_data}"

    yield genre_data

    superadmin_api_manager.genres_api.delete_genre(genre_data["id"])

@pytest.fixture(scope="function")
def movie_payload(create_genre) -> dict:
    """Готовит валидный payload для создания фильма, но НЕ создаёт его."""
    movie_data = data_generator.generate_movie_data()
    movie_data["genreId"] = create_genre["id"]
    return movie_data

@pytest.fixture(scope="function")
def movie_factory(superadmin_api_manager, create_genre):
    """Создаёт фильмы и гарантированно удаляет их даже при падении assert'ов в тесте."""
    created_ids = []

    def _create(payload: dict) -> dict:
        payload = payload.copy()
        payload.setdefault("genreId", create_genre["id"])
        response = superadmin_api_manager.movies_api.movie_factory(payload)
        assert response.status_code in (200, 201), response.text
        body = response.json()
        created_ids.append(body["id"])
        return body

    yield _create

    for movie_id in created_ids:
        superadmin_api_manager.movies_api.delete_movie(movie_id)

@pytest.fixture(scope="session")
def create_eleven_movies(create_genre, superadmin_api_manager):
    """
    Создаёт фильм 11 раз на весь прогон и удаляет после всех тестов.
    """
    movies = []
    try:
        for _ in range(11):
            movie_data = data_generator.generate_movie_data()
            movie_data["genreId"] = create_genre["id"]
            response = superadmin_api_manager.movies_api.create_movie(movie_data)  # ← было movie_factory
            assert response.status_code == 201, f"Не удалось создать фильм: {response.text}"
            movies.append(response.json())
        yield movies
    finally:
        for movie in movies:
            try:
                superadmin_api_manager.movies_api.delete_movie(movie["id"])
            except Exception as e:
                logger.warning(f"Не удалось удалить фильм {movie['id']}: {e}")

@pytest.fixture(scope="session")
def filters_for_movies_n_movies_for_filters(create_genre, superadmin_api_manager):
    """
    Создаёт фильмы и возвращает сгенерированные фильтры для get /movies
    """
    filters = data_generator.generate_movie_filter_params()
    filters["genreId"] = create_genre["id"]
    created_ids = []
    try:
        for _ in range(11):
            movie_data = data_generator.generate_movie_data_for_filters(filters)
            movie_data["genreId"] = filters["genreId"]
            response = superadmin_api_manager.movies_api.create_movie(movie_data)
            assert response.status_code == 201, f"Не удалось создать фильм: {response.text}"
            created_ids.append(response.json()["id"])
        yield filters
    finally:
        for movie_id in created_ids:
            superadmin_api_manager.movies_api.delete_movie(movie_id)


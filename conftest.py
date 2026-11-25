# Конфигурация pytest-фреймворка.
import os
import pytest
import requests
from dotenv import load_dotenv

# Загружаем переменные из .env в окружение в самом начале
load_dotenv()

# Импортируем нужные модули
from clients.api_manager import ApiManager
from utils.data_generator import DataGenerator

from utils.logger import setup_logger

# Глобальная настройка логгера при загрузке conftest.py
setup_logger("custom_requester.custom_requester")  # настраиваем логгер для всех API-клиентов
logger = setup_logger("conftest")                   # логгер для conftest (review_factory)

# Экземпляр генератора данных (общий для всех тестов)
data_generator = DataGenerator()

# Pytest Fixtures
@pytest.fixture(scope="session")
def http_session() -> requests.Session:
    """
    Создаёт объект requests.Session().

    Сессия позволяет сохранять cookies и заголовки между запросами.
    scope="session" — создаётся один раз на весь прогон тестов.
    """
    session = requests.Session()
    yield session
    session.close()

@pytest.fixture(scope="session")
def api_manager(http_session: requests.Session) -> ApiManager:
    """Предоставляет готовый ApiManager с инициализированной сессией (без авторизации)."""
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
    # generate_genre_name уже возвращает dict {"name": "..."}
    genre_payload = data_generator.generate_genre_name()

    # Передаем этот dict напрямую в create_genre
    genre_data = superadmin_api_manager.genres_api.create_genre(genre_payload).json()

    # Эта проверка полезна, так как мы хотим убедиться, что ID вернулся
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
        # send_request уже валидирует статус через expected_status — ассерт избыточен
        response = superadmin_api_manager.movies_api.create_movie(payload)
        body = response.json()
        created_ids.append(body["id"])
        return body

    yield _create

    for movie_id in created_ids:
        superadmin_api_manager.movies_api.delete_movie(
            movie_id, expected_status=(200, 204, 404)
        )

@pytest.fixture(scope="function")
def review_factory(superadmin_api_manager):
    created_reviews = []

    def _create(movie_id: int, payload: dict | None = None) -> dict:
        review_data = {"rating": 5, "text": data_generator.fake.sentence(nb_words=6)}
        if payload:
            review_data.update(payload)

        # send_request уже валидирует статус через expected_status — ассерт избыточен
        response = superadmin_api_manager.movies_api.create_review(movie_id, review_data)
        body = response.json()
        review = body[0] if isinstance(body, list) else body
        created_reviews.append((movie_id, review["userId"]))
        return review

    yield _create

    for movie_id, user_id in created_reviews:
        try:
            superadmin_api_manager.movies_api.delete_review(movie_id, user_id)
        except Exception as e:
            logger.warning(
                f"Не удалось удалить отзыв user={user_id} у фильма {movie_id}: {e}"
            )

@pytest.fixture(scope="function")
def create_movie_with_name(create_genre, superadmin_api_manager):
    """
    Фабрика: создаёт фильм с произвольным name (в т.ч. не-ASCII),
    возвращает созданный объект и удаляет фильм после теста.
    """
    created = []

    def _factory(name: str) -> dict:
        movie_data = data_generator.generate_movie_data()
        movie_data["genreId"] = create_genre["id"]
        movie_data["name"] = name
        movie_data["published"] = True # Поскольку ручка забагована!

        # send_request уже валидирует статус 201 через expected_status по умолчанию
        response = superadmin_api_manager.movies_api.create_movie(movie_data)
        movie = response.json()
        assert movie["name"] == name, (
            f"Сервер уже на этапе создания исказил name: "
            f"{movie['name']!r} != {name!r}"
        )
        created.append(movie["id"])
        return movie

    yield _factory

    for movie_id in created:
        superadmin_api_manager.movies_api.delete_movie(
            movie_id, expected_status=(200, 204, 404)
        )

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
            movies.append(response.json())
        yield movies
    finally:
        for movie in movies:
            superadmin_api_manager.movies_api.delete_movie(
                movie["id"], expected_status=(200, 204, 404)
            )

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
            created_ids.append(response.json()["id"])
        yield filters
    finally:
        for movie_id in created_ids:
            superadmin_api_manager.movies_api.delete_movie(
                movie_id, expected_status=(200, 204, 404)
            )
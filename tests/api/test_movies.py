import pytest


class TestsMoviesPositive:
    @pytest.mark.smoke
    def test_create_movie_without_image_field(self, superadmin_api_manager, movie_payload):
        """
        V-POST-POS-01 (Checklist)
        Создание фильма с валидными обязательными полями (без imageUrl)
        """
        movie_without_image = movie_payload.copy()
        movie_without_image.pop("imageUrl", None)
        response = superadmin_api_manager.movies_api.create_movie(movie_without_image)

        assert response.status_code == 201, response.text
        body = response.json()

        assert "id" in body
        assert body["name"] == movie_without_image["name"]
        assert body["price"] == movie_without_image["price"]
        assert body["description"] == movie_without_image["description"]
        assert body["imageUrl"] is None
        assert body["location"] == movie_without_image["location"]
        assert body["published"] == movie_without_image["published"]
        assert body["genreId"] == movie_without_image["genreId"]
        assert "createdAt" in body
        assert "rating" in body

        # cleanup: удаляем созданный в тесте фильм, чтобы не копить мусор
        superadmin_api_manager.movies_api.delete_movie(body["id"])

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_create_movie(self, superadmin_api_manager, movie_payload):
        """
        V-POST-POS-02 (Checklist)
        Создание фильма со всеми полями (включая imageUrl).
        """
        response = superadmin_api_manager.movies_api.create_movie(movie_payload)

        assert response.status_code == 201, response.text
        body = response.json()

        assert "id" in body
        assert body["name"] == movie_payload["name"]
        assert body["price"] == movie_payload["price"]
        assert body["description"] == movie_payload["description"]
        assert body["imageUrl"] == movie_payload["imageUrl"]
        assert body["location"] == movie_payload["location"]
        assert body["published"] == movie_payload["published"]
        assert body["genreId"] == movie_payload["genreId"]
        assert "createdAt" in body
        assert "rating" in body

        # cleanup: удаляем созданный в тесте фильм, чтобы не копить мусор
        superadmin_api_manager.movies_api.delete_movie(body["id"])

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_without_all_fields(self, api_manager, create_eleven_movies):
        """
        A-GET-POS-01
        Проверка структуры ответа относительно схемы FindAllMoviesResponse при получении афиш фильмов
        """
        params = {}
        response = api_manager.movies_api.get_movies(params=params).json()
        # Проверки, что тело ответа содержит поля movies, count, page, pageSize, pageCount
        assert isinstance(response["movies"], list), "movies должен быть массивом"
        assert response["movies"], "movies не должен быть пустым"
        assert response["count"] >= 1
        assert response["page"] == 1
        assert response["pageSize"] == 10
        assert response["pageCount"] >= 1
        # Проверки, что каждый элемент movies содержит обязательные поля
        for movie in response["movies"]:
            assert isinstance(movie["id"], int) and not isinstance(movie["id"], bool)
            assert isinstance(movie["name"], str) and movie["name"].strip()
            assert isinstance(movie["price"], (int, float)) and not isinstance(movie["price"], bool)
            assert movie["price"] >= 0
            assert movie["description"] is None or isinstance(movie["description"], str)
            assert movie["imageUrl"] is None or isinstance(movie["imageUrl"], str)
            assert movie["location"] in {"MSK", "SPB"}
            assert isinstance(movie["published"], bool)
            assert isinstance(movie["genreId"], int)
            assert isinstance(movie["genre"], dict) and "name" in movie["genre"]
            assert isinstance(movie["createdAt"], str)
            assert isinstance(movie["rating"], (int, float)) and not isinstance(movie["rating"], bool)
            assert 0 <= movie["rating"] <= 5


class TestsMoviesNegative:
    @pytest.mark.smoke
    def test_without_name_field(self, superadmin_api_manager, movie_payload):
        """
        V-POST-NEG-01 (Checklist)
        Проверка отсутствия обязательного поля name.
        """
        movie_without_name = movie_payload.copy()
        movie_without_name.pop("name", None)
        response = superadmin_api_manager.movies_api.create_movie(movie_without_name, expected_status=400)

        assert response.status_code == 400, response.text



class TestsGenrePositive:
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_genre_by_id(self, api_manager, create_genre):
        """
        V-POST-POS-0 (Checklist)
        Получение жанра по ID.
        Использует фикстуру created_genre для подготовки данных.
        """
        # 1. Берем id созданного жанра из фикстуры
        genre_id = create_genre["id"]

        # 2. Выполняем GET-запрос (эндпоинт публичный, поэтому используем обычный api_manager)
        response = api_manager.genres_api.get_genre_id_by_id(
            genre_id, timeout=5, verify=False
        ).json()

        # 3. Проверяем, что вернулся именно тот жанр, который мы создали
        assert response["id"] == genre_id
        assert response["name"] == create_genre["name"]


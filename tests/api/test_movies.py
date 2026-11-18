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

        assert response.status_code in (200, 201), response.text
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

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_create_movie(self, superadmin_api_manager, movie_payload):
        """
        V-POST-POS-02 (Checklist)
        Создание фильма со всеми полями (включая imageUrl).
        """
        response = superadmin_api_manager.movies_api.create_movie(movie_payload)

        assert response.status_code in (200, 201), response.text
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

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_without_all_fields(self, api_manager, create_eleven_movies):
        """
        A-GET-POS-01
        Проверка дефолтных значений фильтров и структуры ответа относительно схемы FindAllMoviesResponse
        при получении афиш фильмов
        """
        params = {}
        response = api_manager.movies_api.get_movies(params=params).json()
        # Проверки, что тело ответа содержит поля movies, count, page, pageSize, pageCount
        assert isinstance(response["movies"], list), "movies должен быть массивом"
        assert response["movies"], "movies не должен быть пустым"
        assert response["count"] >= 1
        assert response["page"] == 1
        assert response["pageSize"] == 10
        assert response["pageCount"] >= 2
        # Проверки, что каждый элемент movies содержит обязательные поля
        for movie in response["movies"]:
            assert isinstance(movie["id"], int) and not isinstance(movie["id"], bool)
            assert isinstance(movie["name"], str) and movie["name"].strip()
            assert isinstance(movie["price"], (int, float)) and not isinstance(movie["price"], bool)
            assert 0 <= movie["price"] <= 1000
            assert movie["description"] is None or isinstance(movie["description"], str)
            assert movie["imageUrl"] is None or isinstance(movie["imageUrl"], str)
            assert movie["location"] in ("MSK", "SPB")
            assert isinstance(movie["published"], bool)
            assert isinstance(movie["genreId"], int)
            assert isinstance(movie["genre"], dict) and "name" in movie["genre"]
            assert isinstance(movie["createdAt"], str)
            assert isinstance(movie["rating"], (int, float)) and not isinstance(movie["rating"], bool)
            assert 0 <= movie["rating"] <= 5

    @pytest.mark.smoke
    @pytest.mark.flaky
    def test_get_with_all_fields(self, api_manager, filters_for_movies_n_movies_for_filters):
        """
        A-GET-POS-02
        Проверка устойчивости контракта при валидных параметрах
        """
        params = filters_for_movies_n_movies_for_filters.copy()
        response = api_manager.movies_api.get_movies(params=params).json()
        # Проверки, что тело ответа содержит поля movies, count, page, pageSize, pageCount
        assert isinstance(response["movies"], list), "movies должен быть массивом"
        assert response["movies"], "movies не должен быть пустым"
        assert response["count"] >= 11
        assert response["page"] in (1, 2)
        assert response["pageSize"] in (range(21))
        assert response["pageCount"] >= 2
        # Проверки, что каждый элемент movies содержит обязательные поля
        for movie in response["movies"]:
            assert isinstance(movie["id"], int) and not isinstance(movie["id"], bool)
            assert isinstance(movie["name"], str) and movie["name"].strip()
            assert isinstance(movie["price"], (int, float)) and not isinstance(movie["price"], bool)
            assert params["minPrice"] <= movie["price"] <= params["maxPrice"]
            assert movie["description"] is None or isinstance(movie["description"], str)
            assert movie["imageUrl"] is None or isinstance(movie["imageUrl"], str)
            assert movie["location"] in ("MSK", "SPB")
            assert isinstance(movie["published"], bool)
            assert isinstance(movie["genreId"], int)
            assert isinstance(movie["genre"], dict) and "name" in movie["genre"]
            assert isinstance(movie["createdAt"], str)
            assert isinstance(movie["rating"], (int, float)) and not isinstance(movie["rating"], bool)
            assert 0 <= movie["rating"] <= 5

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_movies_name_encoding_non_ascii(
            self,
            api_manager,
            superadmin_api_manager,
            create_movie_with_name,
            create_genre,
    ):
        """
        A-GET-POS-03 (Checklist)
        Проверка кодировки поля movies[].name (не-ASCII):
        кириллица и эмодзи должны возвращаться побайтово в UTF-8.
        """
        CYRILLIC_MOVIE_NAME = "Кириллическое название"
        EMOJI_MOVIE_NAME = "Фильм с эмодзи 🎬🍿"

        # Arrange: создаём два фильма с не-ASCII именами (+ movie_data["published"] = True - ручка забагована!)
        cyrillic_movie = create_movie_with_name(CYRILLIC_MOVIE_NAME)
        emoji_movie = create_movie_with_name(EMOJI_MOVIE_NAME)
        expected = {
            cyrillic_movie["id"]: CYRILLIC_MOVIE_NAME,
            emoji_movie["id"]: EMOJI_MOVIE_NAME,
        }

        # Act: GET /movies с фильтром по genreId (гарантированно включает наши фильмы)
        params = {
            "genreId": create_genre["id"],
            "pageSize": 20,
            "page": 1,
        }
        response = api_manager.movies_api.get_movies(params=params)
        assert response.status_code == 200, response.text

        # Assert: кодировка заголовка ответа и самого тела
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, content_type
        # JSON по умолчанию UTF-8, но проверим явно, если сервер указывает charset
        if "charset=" in content_type:
            assert "utf-8" in content_type.lower(), content_type

        body = response.json()

        # Assert: наши фильмы присутствуют в выдаче
        returned_by_id = {m["id"]: m["name"] for m in body["movies"]}
        for movie_id, expected_name in expected.items():
            assert movie_id in returned_by_id, (
                f"Фильм id={movie_id} не найден в ответе GET /movies "
                f"(вернулось {len(returned_by_id)} фильмов)"
            )

            actual_name = returned_by_id[movie_id]

            # 1. Побайтовое сравнение в UTF-8
            assert actual_name.encode("utf-8") == expected_name.encode("utf-8"), (
                f"Нарушена UTF-8 кодировка для id={movie_id}: "
                f"expected={expected_name.encode('utf-8')!r}, "
                f"actual={actual_name.encode('utf-8')!r}"
            )

            # 2. Покодпоинтовое сравнение (ловит нормализацию/суррогаты)
            assert [ord(c) for c in actual_name] == [ord(c) for c in expected_name], (
                f"Нарушены codepoints для id={movie_id}"
            )

            # 3. Точечная проверка для эмодзи (они состоят из суррогатных пар в UTF-16,
            #    но в Python 3 — одиночные codepoints)
            for ch in expected_name:
                if ord(ch) > 0xFFFF:
                    assert ch in actual_name, (
                        f"Эмодзи U+{ord(ch):04X} потерян/искажён в id={movie_id}"
                    )

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


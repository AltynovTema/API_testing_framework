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

        assert isinstance(response["movies"], list), "movies должен быть массивом"
        assert response["movies"], "movies не должен быть пустым"
        assert response["count"] >= 1
        assert response["page"] == 1
        assert response["pageSize"] == 10
        assert response["pageCount"] >= 2

        for movie in response["movies"]:
            assert isinstance(movie["id"], int) and not isinstance(movie["id"], bool)
            assert isinstance(movie["name"], str) and movie["name"].strip()
            assert isinstance(movie["price"], (int, float)) and not isinstance(movie["price"], bool)
            assert movie["price"] >= 0
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

        assert isinstance(response["movies"], list), "movies должен быть массивом"
        assert response["movies"], "movies не должен быть пустым"
        assert response["count"] >= 11
        assert response["page"] in (1, 2)
        assert response["pageSize"] in (range(21))
        assert response["pageCount"] >= 2

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

        cyrillic_movie = create_movie_with_name(CYRILLIC_MOVIE_NAME)
        emoji_movie = create_movie_with_name(EMOJI_MOVIE_NAME)
        expected = {
            cyrillic_movie["id"]: CYRILLIC_MOVIE_NAME,
            emoji_movie["id"]: EMOJI_MOVIE_NAME,
        }

        params = {
            "genreId": create_genre["id"],
            "pageSize": 20,
            "page": 1,
        }
        response = api_manager.movies_api.get_movies(params=params)
        assert response.status_code == 200, response.text

        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, content_type
        if "charset=" in content_type:
            assert "utf-8" in content_type.lower(), content_type

        body = response.json()

        returned_by_id = {m["id"]: m["name"] for m in body["movies"]}
        for movies_id, expected_name in expected.items():
            assert movies_id in returned_by_id, (
                f"Фильм id={movies_id} не найден в ответе GET /movies "
                f"(вернулось {len(returned_by_id)} фильмов)"
            )

            actual_name = returned_by_id[movies_id]

            assert actual_name.encode("utf-8") == expected_name.encode("utf-8"), (
                f"Нарушена UTF-8 кодировка для id={movies_id}: "
                f"expected={expected_name.encode('utf-8')!r}, "
                f"actual={actual_name.encode('utf-8')!r}"
            )

            assert [ord(c) for c in actual_name] == [ord(c) for c in expected_name], (
                f"Нарушены codepoints для id={movies_id}"
            )

            for ch in expected_name:
                if ord(ch) > 0xFFFF:
                    assert ch in actual_name, (
                        f"Эмодзи U+{ord(ch):04X} потерян/искажён в id={movies_id}"
                    )

    @pytest.mark.smoke
    def test_get_movie_by_id_reviews_structure(
            self, api_manager, movie_payload, movie_factory, review_factory
    ):
        """
        B-GET-POS-02 (Checklist)
        Проверка структуры ответа относительно схемы FindOneMovieResponse:
        GET /movies/{id существующего фильма}
        """
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]
        review = review_factory(movies_id)

        response = api_manager.movies_api.get_movie_by_id(movies_id)

        assert response.status_code == 200, response.text
        body = response.json()

        required_fields = (
            "id", "name", "price", "description", "imageUrl",
            "location", "published", "genreId", "genre",
            "createdAt", "rating", "reviews",
        )
        for field in required_fields:
            assert field in body, f"В ответе отсутствует обязательное поле '{field}'"

        assert body["id"] == movies_id
        assert body["name"] == movie["name"]
        assert body["price"] == movie["price"]
        assert body["description"] == movie["description"]
        assert body["imageUrl"] == movie["imageUrl"]
        assert body["location"] == movie["location"]
        assert body["published"] == movie["published"]
        assert body["genreId"] == movie["genreId"]
        assert isinstance(body["rating"], (int, float)) and not isinstance(body["rating"], bool)
        assert 0 <= body["rating"] <= 5
        assert isinstance(body["genre"], dict) and "name" in body["genre"]
        assert isinstance(body["reviews"], list), "reviews должен быть массивом"

        assert body["reviews"], (
            "Ожидался хотя бы один отзыв у фильма, "
            "иначе проверка структуры reviews[] не выполняется"
        )
        assert len(body["reviews"]) == 1
        actual_review = body["reviews"][0]
        for field in ("userId", "rating", "text", "createdAt", "user"):
            assert field in actual_review, f"В отзыве отсутствует поле '{field}'"
        assert actual_review["userId"] == review["userId"]
        assert actual_review["rating"] == review["rating"]
        assert actual_review["text"] == review["text"]
        assert isinstance(actual_review["createdAt"], str)
        assert isinstance(actual_review["user"], dict) and "fullName" in actual_review["user"], (
            "reviews[].user должен содержать fullName"
        )

    @pytest.mark.smoke
    def test_get_movie_by_id_empty_reviews(
            self, api_manager, movie_payload, movie_factory
    ):
        """
        B-GET-POS-04 (Checklist)
        Проверка пустого массива reviews:
        GET /movies/{id существующего фильма без отзывов}
        """
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]

        response = api_manager.movies_api.get_movie_by_id(movies_id)

        assert response.status_code == 200, response.text
        body = response.json()

        required_fields = (
            "id", "name", "price", "description", "imageUrl",
            "location", "published", "genreId", "genre",
            "createdAt", "rating", "reviews",
        )
        for field in required_fields:
            assert field in body, f"В ответе отсутствует обязательное поле '{field}'"

        assert body["id"] == movies_id
        assert body["name"] == movie["name"]
        assert body["price"] == movie["price"]
        assert body["description"] == movie["description"]
        assert body["imageUrl"] == movie["imageUrl"]
        assert body["location"] == movie["location"]
        assert body["published"] == movie["published"]
        assert body["genreId"] == movie["genreId"]
        assert isinstance(body["rating"], (int, float)) and not isinstance(body["rating"], bool)
        assert 0 <= body["rating"] <= 5
        assert isinstance(body["genre"], dict) and "name" in body["genre"]
        assert isinstance(body["reviews"], list), "reviews должен быть массивом"

        assert body["reviews"] is not None, "reviews не должен быть null"
        assert body["reviews"] == [], "reviews должен быть пустым массивом"


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
        genre_id = create_genre["id"]

        response = api_manager.genres_api.get_genre_id_by_id(
            genre_id, timeout=5, verify=False
        ).json()

        assert response["id"] == genre_id
        assert response["name"] == create_genre["name"]
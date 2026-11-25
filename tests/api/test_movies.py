import pytest


class TestsMoviesPositive:
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_create_movie(self, superadmin_api_manager, movie_payload):
        """
        V-POST-POS-02 (Checklist)
        Создание фильма со всеми полями (включая imageUrl).
        """
        # Act: создаём фильм с полным payload
        body = superadmin_api_manager.movies_api.create_movie(movie_payload).json()

        # Assert: сервер сгенерировал id и createdAt
        assert "id" in body
        assert "createdAt" in body

        # Assert: значения полей совпадают с отправленными исходными данными
        assert body["name"] == movie_payload["name"]
        assert body["price"] == movie_payload["price"]
        assert body["description"] == movie_payload["description"]
        assert body["imageUrl"] == movie_payload["imageUrl"]
        assert body["location"] == movie_payload["location"]
        assert body["published"] == movie_payload["published"]
        assert body["genreId"] == movie_payload["genreId"]

        # Assert: rating — вычисляемое поле, для нового фильма без отзывов ожидаем 0
        assert body["rating"] == 0

    @pytest.mark.smoke
    def test_create_movie_without_image_field(self, superadmin_api_manager, movie_payload):
        """
        V-POST-POS-01 (Checklist)
        Создание фильма с валидными обязательными полями (без imageUrl)
        """
        # Arrange: убираем необязательное поле imageUrl из валидного payload
        movie_without_image = movie_payload.copy()
        movie_without_image.pop("imageUrl", None)

        # Act: создаём фильм
        body = superadmin_api_manager.movies_api.create_movie(movie_without_image).json()

        # Assert: сервер сгенерировал id и createdAt
        assert "id" in body
        assert "createdAt" in body

        # Assert: значения полей совпадают с отправленными исходными данными
        assert body["name"] == movie_without_image["name"]
        assert body["price"] == movie_without_image["price"]
        assert body["description"] == movie_without_image["description"]
        assert body["imageUrl"] is None
        assert body["location"] == movie_without_image["location"]
        assert body["published"] == movie_without_image["published"]
        assert body["genreId"] == movie_without_image["genreId"]

        # Assert: rating — вычисляемое поле, для нового фильма без отзывов ожидаем 0
        assert body["rating"] == 0

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_movies_name_encoding_non_ascii(
            self,
            api_manager,
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

        # Assert на заголовок Content-Type
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, content_type
        if "charset=" in content_type:
            assert "utf-8" in content_type.lower(), content_type

        body = response.json()

        # Assert: наши фильмы присутствуют в выдаче
        returned_by_id = {m["id"]: m["name"] for m in body["movies"]}
        for movies_id, expected_name in expected.items():
            assert movies_id in returned_by_id, (
                f"Фильм id={movies_id} не найден в ответе GET /movies "
                f"(вернулось {len(returned_by_id)} фильмов)"
            )
            actual_name = returned_by_id[movies_id]

            # Assert: побайтовое сравнение в UTF-8
            assert actual_name.encode("utf-8") == expected_name.encode("utf-8"), (
                f"Нарушена UTF-8 кодировка для id={movies_id}: "
                f"expected={expected_name.encode('utf-8')!r}, "
                f"actual={actual_name.encode('utf-8')!r}"
            )

            # Assert: покодпоинтовое сравнение (ловит нормализацию/суррогаты)
            assert [ord(c) for c in actual_name] == [ord(c) for c in expected_name], (
                f"Нарушены codepoints для id={movies_id}"
            )

            # Assert: точечная проверка эмодзи (codepoints > U+FFFF)
            for ch in expected_name:
                if ord(ch) > 0xFFFF:
                    assert ch in actual_name, (
                        f"Эмодзи U+{ord(ch):04X} потерян/искажён в id={movies_id}"
                    )

    @pytest.mark.smoke
    def test_get_movie_by_id_reviews_structure(self, api_manager, movie_payload, movie_factory, review_factory):
        """
        B-GET-POS-02 (Checklist)
        Проверка структуры ответа относительно схемы FindOneMovieResponse:
        GET /movies/{id существующего фильма}
        """
        # Arrange: фильм + гарантированно хотя бы один отзыв на него
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]
        review = review_factory(movies_id)

        # Act
        body = api_manager.movies_api.get_movie_by_id(movies_id).json()

        # Assert: обязательные поля верхнего уровня
        required_fields = (
            "id", "name", "price", "description", "imageUrl",
            "location", "published", "genreId", "genre",
            "createdAt", "rating", "reviews",
        )
        for field in required_fields:
            assert field in body, f"В ответе отсутствует обязательное поле '{field}'"

        # Assert: значения полей фильма совпадают с исходными данными
        assert body["id"] == movies_id
        assert body["name"] == movie_payload["name"]
        assert body["price"] == movie_payload["price"]
        assert body["description"] == movie_payload["description"]
        assert body["imageUrl"] == movie_payload["imageUrl"]
        assert body["location"] == movie_payload["location"]
        assert body["published"] == movie_payload["published"]
        assert body["genreId"] == movie_payload["genreId"]
        assert isinstance(body["genre"], dict) and "name" in body["genre"]

        # Assert: rating — вычисляемое поле; при единственном отзыве равен его рейтингу
        assert isinstance(body["rating"], (int, float)) and not isinstance(body["rating"], bool)
        assert body["rating"] == review["rating"]

        # Assert: reviews — массив ровно с одним созданным отзывом
        assert isinstance(body["reviews"], list), "reviews должен быть массивом"
        assert len(body["reviews"]) == 1, "Ожидался ровно один отзыв у фильма"

        # Assert: структура и значения отзыва совпадают с исходными данными
        actual_review = body["reviews"][0]
        for field in ("userId", "rating", "text", "createdAt", "user"):
            assert field in actual_review, f"В отзыве отсутствует поле '{field}'"
        assert actual_review["userId"] == review["userId"]
        assert actual_review["rating"] == review["rating"]
        assert actual_review["text"] == review["text"]
        assert isinstance(actual_review["createdAt"], str)
        assert isinstance(actual_review["user"], dict) and "fullName" in actual_review["user"]

    @pytest.mark.smoke
    def test_get_movie_by_id_empty_reviews(
            self, api_manager, movie_payload, movie_factory
    ):
        """
        B-GET-POS-04 (Checklist)
        Проверка пустого массива reviews:
        GET /movies/{id существующего фильма без отзывов}
        """
        # Arrange: создаем фильм без отзывов
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]

        # Act
        body = api_manager.movies_api.get_movie_by_id(movies_id).json()

        # Assert: обязательные поля верхнего уровня
        required_fields = (
            "id", "name", "price", "description", "imageUrl",
            "location", "published", "genreId", "genre",
            "createdAt", "rating", "reviews",
        )
        for field in required_fields:
            assert field in body, f"В ответе отсутствует обязательное поле '{field}'"

        # Assert: значения полей фильма совпадают с исходными данными
        assert body["id"] == movies_id
        assert body["name"] == movie_payload["name"]
        assert body["price"] == movie_payload["price"]
        assert body["description"] == movie_payload["description"]
        assert body["imageUrl"] == movie_payload["imageUrl"]
        assert body["location"] == movie_payload["location"]
        assert body["published"] == movie_payload["published"]
        assert body["genreId"] == movie_payload["genreId"]
        assert isinstance(body["genre"], dict) and "name" in body["genre"]

        # Assert: rating — вычисляемое поле; без отзывов ожидаем 0
        assert isinstance(body["rating"], (int, float)) and not isinstance(body["rating"], bool)
        assert body["rating"] == 0

        # Assert: reviews — пустой массив, не null
        assert isinstance(body["reviews"], list), "reviews должен быть массивом"
        assert body["reviews"] == [], "reviews должен быть пустым массивом"

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_filters_get_movies_without_all_fields(self, api_manager, create_eleven_movies):
        """
        A-GET-POS-01
        Проверка дефолтных значений фильтров и структуры ответа относительно схемы FindAllMoviesResponse
        при получении афиш фильмов
        """
        # Arrange: пустые параметры — проверяем дефолты пагинации
        params = {}

        # Act: GET /movies без фильтров
        response = api_manager.movies_api.get_movies(params=params).json()

        # Assert: верхнеуровневая структура ответа и дефолты пагинации
        assert isinstance(response["movies"], list), "movies должен быть массивом"
        assert response["movies"], "movies не должен быть пустым"

        # Благодаря фикстуре create_eleven_movies мы гарантируем, что в базе есть хотя бы 11 фильмов
        assert response["count"] >= 11
        assert response["page"] == 1
        assert response["pageSize"] == 10
        assert response["pageCount"] >= 2

        # Assert: проверка уникальности ID на ТЕКУЩЕЙ странице
        returned_ids = [movie["id"] for movie in response["movies"]]
        assert len(returned_ids) == len(set(returned_ids)), "На странице обнаружены дубликаты ID!"

        # Assert: каждый элемент movies содержит обязательные поля корректных типов
        for movie in response["movies"]:
            assert isinstance(movie["id"], int) and not isinstance(movie["id"], bool)
            assert isinstance(movie["name"], str) and movie["name"].strip()
            assert isinstance(movie["price"], (int, float)) and not isinstance(movie["price"], bool)

            # Если проверять 0 <= price <= 1000, тест может упасть на чужих данных из базы.
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
    @pytest.mark.xfail(
        reason="Сервер не возвращает 'published'=False фильмы что не соответствуют контракту",
        strict=True
    )
    def test_filters_get_movies_with_correct_fields(self, api_manager, filters_for_movies_n_movies_for_filters):
        """
        A-GET-POS-02
        Проверка устойчивости контракта при валидных параметрах
        """
        # Arrange: подготавливаем фильтры и гарантированно подходящие под них фильмы
        params = filters_for_movies_n_movies_for_filters

        # Act: GET /movies с валидными фильтрами
        response = api_manager.movies_api.get_movies(params=params).json()

        # Assert: верхнеуровневая структура ответа и пагинация под фильтрами
        assert isinstance(response["movies"], list), "movies должен быть массивом"
        assert response["movies"], "movies не должен быть пустым"
        assert response["count"] >= 11
        assert response["page"] in (1, 2)
        assert response["pageSize"] in range(21)
        assert response["pageCount"] >= 2

        # Assert: каждый элемент movies содержит обязательные поля корректных типов
        # и укладывается в переданные фильтры
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
    def test_movie_patch_one_field(self, superadmin_api_manager, movie_payload, movie_factory, review_factory):
        """
        G-PATCH-POS-01 (Checklist)
        Редактирование одного поля:
        PATCH /movies/{id существующего фильма}
        """
        # Arrange:
        # а) создаём фильм и отзыв к нему (отзыв нужен, чтобы убедиться, что PATCH не ломает агрегат rating)
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]
        review = review_factory(movies_id)

        # б) формируем патч только с одним изменяемым полем
        new_name = "ИМЯ ИЗМЕНЕНО"
        patch_payload = {"name": new_name}

        # Act: PATCH /movies/{id} только с одним полем
        body = superadmin_api_manager.movies_api.update_movie(movies_id, patch_payload).json()

        # Assert: обязательные поля, которые контракт PATCH реально возвращает (без reviews)
        required_fields = (
            "id", "name", "price", "description", "imageUrl",
            "location", "published", "genreId", "genre",
            "createdAt", "rating",
        )
        for field in required_fields:
            assert field in body, f"В ответе отсутствует обязательное поле '{field}'"

        # Assert: изменилось ровно то поле, которое патчили
        assert body["id"] == movies_id
        assert body["name"] == new_name

        # Assert: остальные поля не изменились — сверяем с исходным фильмом из фабрики
        assert body["price"] == movie["price"]
        assert body["description"] == movie["description"]
        assert body["imageUrl"] == movie["imageUrl"]
        assert body["location"] == movie["location"]
        assert body["published"] == movie["published"]
        assert body["genreId"] == movie["genreId"]
        assert body["createdAt"] == movie["createdAt"]
        assert isinstance(body["genre"], dict) and "name" in body["genre"]

        # Assert: агрегат rating не сломан патчем — при единственном отзыве равен его рейтингу
        assert isinstance(body["rating"], (int, float)) and not isinstance(body["rating"], bool)
        assert body["rating"] == review["rating"]

        # Assert: отзывы не входят в контракт PATCH — проверяем их через отдельный GET
        fetched_body = superadmin_api_manager.movies_api.get_movie_by_id(movies_id).json()
        assert isinstance(fetched_body["reviews"], list), "reviews должен быть массивом"
        assert len(fetched_body["reviews"]) == 1, "Ожидался ровно один отзыв у фильма"
        actual_review = fetched_body["reviews"][0]
        assert actual_review["userId"] == review["userId"]
        assert actual_review["rating"] == review["rating"]
        assert actual_review["text"] == review["text"]

    @pytest.mark.smoke
    def test_movie_patch_multiple_fields(self, superadmin_api_manager, movie_payload, movie_factory, review_factory):
        """
        G-PATCH-POS-02 (Checklist)
        Редактирование нескольких полей:
        PATCH /movies/{id существующего фильма}
        """
        # Arrange:
        # а) создаём фильм и отзыв к нему (отзыв нужен, чтобы убедиться, что PATCH не ломает агрегат rating)
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]
        review = review_factory(movies_id)

        # б) формируем патч сразу с несколькими валидными полями
        new_name = "ИМЯ ИЗМЕНЕНО"
        new_price = movie["price"] + 1
        new_location = "SPB" if movie["location"] == "MSK" else "MSK"
        patch_payload = {
            "name": new_name,
            "price": new_price,
            "location": new_location,
        }

        # Act: PATCH /movies/{id} с несколькими полями
        body = superadmin_api_manager.movies_api.update_movie(movies_id, patch_payload).json()

        # Assert: обязательные поля, которые контракт PATCH реально возвращает (без reviews)
        required_fields = (
            "id", "name", "price", "description", "imageUrl",
            "location", "published", "genreId", "genre",
            "createdAt", "rating",
        )
        for field in required_fields:
            assert field in body, f"В ответе отсутствует обязательное поле '{field}'"

        # Assert: изменились ровно те поля, которые патчили
        assert body["id"] == movies_id
        assert body["name"] == new_name
        assert body["price"] == new_price
        assert body["location"] == new_location

        # Assert: остальные поля не изменились — сверяем с исходным фильмом из фабрики
        assert body["description"] == movie["description"]
        assert body["imageUrl"] == movie["imageUrl"]
        assert body["published"] == movie["published"]
        assert body["genreId"] == movie["genreId"]
        assert body["createdAt"] == movie["createdAt"]
        assert isinstance(body["genre"], dict) and "name" in body["genre"]

        # Assert: агрегат rating не сломан патчем — при единственном отзыве равен его рейтингу
        assert isinstance(body["rating"], (int, float)) and not isinstance(body["rating"], bool)
        assert body["rating"] == review["rating"]

        # Assert: отзывы не входят в контракт PATCH — проверяем их через отдельный GET
        fetched_body = superadmin_api_manager.movies_api.get_movie_by_id(movies_id).json()
        assert isinstance(fetched_body["reviews"], list), "reviews должен быть массивом"
        assert len(fetched_body["reviews"]) == 1, "Ожидался ровно один отзыв у фильма"
        actual_review = fetched_body["reviews"][0]
        assert actual_review["userId"] == review["userId"]
        assert actual_review["rating"] == review["rating"]
        assert actual_review["text"] == review["text"]

    @pytest.mark.smoke
    def test_delete_existing_movie(self, superadmin_api_manager, movie_payload, movie_factory):
        """
        D-DELETE-POS-01 (Checklist)
        Удаление существующего фильма:
        DELETE /movies/{id существующего фильма}
        """
        # Arrange: создаём фильм, который будем удалять
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]

        # Act: DELETE /movies/{id} под ролью SUPER_ADMIN
        body = superadmin_api_manager.movies_api.delete_movie(movies_id).json()

        # Assert: обязательные поля схемы MovieResponse в теле ответа
        required_fields = (
            "id", "name", "price", "description", "imageUrl",
            "location", "published", "genreId", "genre",
            "createdAt", "rating",
        )
        for field in required_fields:
            assert field in body, f"В ответе отсутствует обязательное поле '{field}'"

        # Assert: тело ответа описывает именно удалённый фильм — сверяем с исходными данными
        assert body["id"] == movies_id
        assert body["name"] == movie["name"]
        assert body["price"] == movie["price"]
        assert body["description"] == movie["description"]
        assert body["imageUrl"] == movie["imageUrl"]
        assert body["location"] == movie["location"]
        assert body["published"] == movie["published"]
        assert body["genreId"] == movie["genreId"]
        assert body["createdAt"] == movie["createdAt"]
        assert isinstance(body["genre"], dict) and "name" in body["genre"]
        assert isinstance(body["rating"], (int, float)) and not isinstance(body["rating"], bool)

        # Assert: фильм действительно удалён — GET /movies/{id} возвращает 404
        fetched = superadmin_api_manager.movies_api.get_movie_by_id(movies_id, expected_status=404)


class TestsMoviesNegative:
    @pytest.mark.smoke
    def test_create_movie_without_name_field(self, superadmin_api_manager, movie_payload):
        """
        V-POST-NEG-01 (Checklist)
        Проверка отсутствия обязательного поля name.
        """
        # Arrange: убираем обязательное поле name из валидного payload
        movie_without_name = movie_payload.copy()
        movie_without_name.pop("name", None)

        # Act: создаём фильм без name
        superadmin_api_manager.movies_api.create_movie(movie_without_name, expected_status=400)

    @pytest.mark.smoke
    def test_filters_movie_with_invalid_field(self, api_manager, filters_for_movies_n_movies_for_filters):
        """
        A-GET-NEG-01
        Проверка невалидных типов значений параметров
        """
        # Arrange: подготавливаем фильм и валидные фильтры, в которых меняем одно поле на невалидное значение
        params = filters_for_movies_n_movies_for_filters.copy()
        params["pageSize"] = "abc"

        # Act: GET /movies с не валидными фильтрами
        api_manager.movies_api.get_movies(params=params, expected_status=400)

    @pytest.mark.smoke
    def test_filters_movie_with_invalid_enum_field(self, api_manager, filters_for_movies_n_movies_for_filters):
        """
        A-GET-NEG-02
        Проверка невалидных значений enum-полей
        """
        # Arrange: подготавливаем фильм и валидные фильтры, в которых меняем одно поле на невалидное значение
        params = filters_for_movies_n_movies_for_filters.copy()
        params["locations"] = "ABC"

        # Act: GET /movies с не валидными фильтрами
        api_manager.movies_api.get_movies(params=params, expected_status=400)

    @pytest.mark.smoke
    @pytest.mark.regression
    def tests_get_movie_with_non_existent_id(self, movie_factory, movie_payload, superadmin_api_manager):
        """
        B-GET-NEG-01
        Проверка несуществующего id
        Отправить GET /movies/{id} заведомо несуществующего фильма}
        """
        # Arrange: создаём фильм, сохраняем тестовый ID и удаляем фильм
        movie = movie_factory(movie_payload)
        test_movie_id = movie["id"]
        superadmin_api_manager.movies_api.delete_movie(test_movie_id)

        # Act: GET /movies/{id} под ролью SUPER_ADMIN что бы не дёргать лишнего
        superadmin_api_manager.movies_api.get_movie_by_id(test_movie_id, expected_status = 404)

    @pytest.mark.smoke
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason="Сервер возвращает 500 вместо 400/404 при невалидном типе id",
        strict=True
    )
    def test_get_movies_with_invalid_id(self, api_manager):
        """
        B-GET-NEG-02
        Проверка невалидного типа id
        Отправить GET /movies/abc
        """
        # Arrange: подготавливаем невалидные данные для ID
        invalid_movie_id = "abc"

        # Act: GET /movies/{id}
        api_manager.movies_api.get_movie_by_id(invalid_movie_id, expected_status=(400, 404))

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_create_movie_with_invalid_enum_field(self, superadmin_api_manager, movie_payload):
        """
        V-POST-NEG-02 Проверка невалидного значения enum-поля
        Шаг 1. Отправить POST /movies с location=ABC;
        """
        # Arrange: подготавливаем данные невалидного значения enum-поля
        params = movie_payload.copy()
        params["location"] = "ABC"

        # Act: POST /movies с location=ABC
        superadmin_api_manager.movies_api.create_movie(params, expected_status=400)

    @pytest.mark.smoke
    def test_create_movie_without_superadmin_role(self, api_manager, movie_payload):
        """
        V-POST-NEG-04 (Checklist)
        Проверка доступа без роли SUPER_ADMIN:
        POST /movies под ролью PUBLIC (без авторизации).
        """
        # Act: POST /movies без авторизации
        api_manager.movies_api.create_movie(movie_payload, expected_status=401)

    @pytest.mark.smoke
    def test_patch_movie_with_non_existent_id(self, superadmin_api_manager, movie_payload):
        """
        G-PATCH-NEG-01 (Checklist)
        Проверка несуществующего id:
        PATCH /movies/{id заведомо несуществующего фильма}.
        """
        # Arrange: создаём фильм и удаляем его, чтобы id гарантированно не существовал
        movie = superadmin_api_manager.movies_api.create_movie(movie_payload).json()
        non_existent_id = movie["id"]
        superadmin_api_manager.movies_api.delete_movie(non_existent_id)

        # Act: PATCH /movies/{id несуществующего фильма}
        superadmin_api_manager.movies_api.update_movie(
            non_existent_id, {"name": "Новое имя"}, expected_status=404
        )

    @pytest.mark.smoke
    def test_patch_movie_with_invalid_enum_field(self, superadmin_api_manager, movie_factory, movie_payload):
        """
        G-PATCH-NEG-02 (Checklist)
        Проверка невалидного значения enum-поля:
        PATCH /movies/{id} с location=ABC.
        """
        # Arrange: создаём фильм, который будем патчить
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]

        # Act: PATCH с невалидным location
        superadmin_api_manager.movies_api.update_movie(
            movies_id, {"location": "ABC"}, expected_status=400
        )

    @pytest.mark.smoke
    def test_patch_movie_without_superadmin_role(self, api_manager, movie_payload, movie_factory):
        """
        G-PATCH-NEG-03 (Checklist)
        Проверка доступа без роли SUPER_ADMIN:
        PATCH /movies/{id} под ролью PUBLIC.
        """
        # Arrange: создаём фильм под SUPER_ADMIN, чтобы id точно существовал
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]

        # Act: PATCH без авторизации
        api_manager.movies_api.update_movie(
            movies_id, {"name": "Хакерское имя"}, expected_status=(401, 403)
        )

    @pytest.mark.smoke
    def test_delete_movie_with_non_existent_id(self, superadmin_api_manager, movie_payload):
        """
        D-DELETE-NEG-01 (Checklist)
        Проверка несуществующего id:
        DELETE /movies/{id заведомо несуществующего фильма}.
        """
        # Arrange: создаём фильм и удаляем, чтобы id гарантированно не существовал
        movie = superadmin_api_manager.movies_api.create_movie(movie_payload).json()
        non_existent_id = movie["id"]
        superadmin_api_manager.movies_api.delete_movie(non_existent_id)

        # Act: повторный DELETE того же id
        superadmin_api_manager.movies_api.delete_movie(
            non_existent_id, expected_status=404
        )

    @pytest.mark.smoke
    def test_delete_movie_without_superadmin_role(self, api_manager, movie_payload, movie_factory):
        """
        D-DELETE-NEG-02 (Checklist)
        Проверка доступа без роли SUPER_ADMIN:
        DELETE /movies/{id} под ролью PUBLIC.
        """
        # Arrange: создаём фильм под SUPER_ADMIN, чтобы id точно существовал
        movie = movie_factory(movie_payload)
        movies_id = movie["id"]

        # Act: DELETE без авторизации
        api_manager.movies_api.delete_movie(
            movies_id, expected_status=(401, 403)
        )


class TestsGenrePositive:
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_genre_by_id(self, api_manager, create_genre):
        """
        V-POST-POS-0 (Checklist)
        Получение жанра по ID.
        Использует фикстуру created_genre для подготовки данных.
        """
        # Arrange: берём id созданного жанра из фикстуры
        genre_id = create_genre["id"]

        # Act: GET /genres/{id} (эндпоинт публичный)
        response = api_manager.genres_api.get_genre_id_by_id(genre_id).json()

        # Assert: вернулся именно тот жанр, который мы создали
        assert response["id"] == genre_id
        assert response["name"] == create_genre["name"]
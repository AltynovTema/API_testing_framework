import pytest


class TestsMoviesPositive:
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_create_movie(self, superadmin_api_manager, movie_payload):
        """
        O-GET-POS-01 (Checklist)
        Создание фильма с валидными обязательными полями.
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



class TestsGenrePositive:
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_genre_by_id(self, api_manager, created_genre):
        """
        V-POST-POS-0 (Checklist)
        Получение жанра по ID.
        Использует фикстуру created_genre для подготовки данных.
        """
        # 1. Берем id созданного жанра из фикстуры
        genre_id = created_genre["id"]

        # 2. Выполняем GET-запрос (эндпоинт публичный, поэтому используем обычный api_manager)
        response = api_manager.genres_api.get_genre_id_by_id(
            genre_id, timeout=5, verify=False
        ).json()

        # 3. Проверяем, что вернулся именно тот жанр, который мы создали
        assert response["id"] == genre_id
        assert response["name"] == created_genre["name"]


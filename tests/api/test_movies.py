import pytest


class TestsMoviesPositive:
    def test_get_genre_by_id(self, api_manager, created_genre):
        """
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
from custom_requester.custom_requester import CustomRequester
from config.base_urls import MOVIES_BASE_URL


MOVIES = "/movies"
GENRES = "/genres"

class MoviesAPI(CustomRequester):
    """API класс наследник для работы с эндпойнтами фильмов"""
    def __init__(self, session):
        super().__init__(session=session, base_url=MOVIES_BASE_URL)

    def get_movies(self, params, expected_status=200, **kwargs):
        return self.send_request(
            method="GET",
            endpoint=MOVIES,
            params=params,
            expected_status=expected_status,
            **kwargs
        )

    def get_movie_by_id(self, movies_id, expected_status=200, **kwargs):
        return self.send_request(
            method="GET",
            endpoint=f"{MOVIES}/{movies_id}",
            expected_status=expected_status,
            **kwargs
        )

    def create_movie(self, movies_data, expected_status=201, **kwargs):
        return self.send_request(
            method="POST",
            endpoint=MOVIES,
            data=movies_data,
            expected_status=expected_status,
            **kwargs
        )

    def update_movie(self, movies_id, movies_data, expected_status=200, **kwargs):
        return self.send_request(
            method="PATCH",
            endpoint=f"{MOVIES}/{movies_id}",
            data=movies_data,
            expected_status=expected_status,
            **kwargs
        )

    def delete_movie(self, movies_id, expected_status=200, **kwargs):
        return self.send_request(
            method="DELETE",
            endpoint=f"{MOVIES}/{movies_id}",
            expected_status=expected_status,
            **kwargs
        )


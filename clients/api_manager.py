from clients.user_api import UserApi
from clients.auth_api import AuthApi
from clients.movies_api import MoviesApi, GenresApi

class ApiManager():
    def __init__(self, session):
        self.session=session
        self.auth_api = AuthApi(session)
        self.user_api = UserApi(session)
        self.movies_api = MoviesApi(session)
        self.genres_api = GenresApi(session)

    def close_session(self):
        self.session.close()

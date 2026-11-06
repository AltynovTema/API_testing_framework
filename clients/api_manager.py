from clients.user_api import UserApi
from clients.auth_api import AuthApi

class ApiManager():
    def __init__(self, session):
        self.session=session
        self.auth_api = AuthApi(session)
        self.user_api = UserApi(session)

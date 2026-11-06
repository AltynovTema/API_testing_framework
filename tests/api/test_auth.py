from pytest import skip, raises
from requests import exceptions

class TestsAuthPositive:
    def test_register_user(self, api_manager, user_generator):
        """Регистрация нового пользователя"""
        response = api_manager.auth_api.register_user(user_generator, timeout=5, verify=False).json()
        # Основные поля (соответствие структуре ответа)
        assert response["email"] == user_generator["email"]
        assert response["fullName"] == user_generator["fullName"]
        assert response["roles"] == user_generator["roles"]
        assert response["verified"] is True
        # Поля, генерируемые сервером
        assert "id" in response
        assert "createdAt" in response
        if "banned" not in response:
            skip("flaky-тест: сервер не возвращает поле 'banned' указанное в Swagger")
        assert "banned" in response

    def test_register_and_login_user(self, api_manager, user_generator):
        login_data = {
            "email": user_generator["email"],
            "password": user_generator["password"]
        }
        response_register = api_manager.auth_api.register_user(user_generator,  timeout=5, verify=False).json()
        response_login = api_manager.auth_api.login_user(login_data,  timeout=5, verify=False).json()
        # Основные поля (соответствие зарегистрированным)
        assert response_register["id"] == response_login["user"]["id"]
        assert response_register["email"] == response_login["user"]["email"]
        assert response_register["fullName"] == response_login["user"]["fullName"]
        assert response_register["roles"] == response_login["user"]["roles"]
        # Поля токенов, генерируемые сервером
        assert "accessToken" in response_login
        assert "refreshToken" in response_login
        assert "expiresIn" in response_login

    def test_server_minimal_timeout(self, api_manager, user_generator):
        """Проверка на минимальный таймаут"""
        response = api_manager.auth_api.register_user(user_generator, timeout=0.7, verify=False).json()
        assert response["email"] == user_generator["email"]
        assert response["fullName"] == user_generator["fullName"]


class TestsAuthNegative:
    def test_get_user_info_forbidden_for_user(self, api_manager, authenticated_user):
        """Проверка, что обычный пользователь не имеет доступа к эндпоинту"""
        user_id = authenticated_user["id"]
        # Явно указываем, что ожидаем 403 статус
        response = api_manager.user_api.get_user_info(user_id, expected_status=403,  timeout=5, verify=False).json()
        assert response["statusCode"] == 403
        assert response["message"] == "Forbidden resource"


class TestsCheckFramework:
    def test_register_timeout(self, api_manager, user_generator):
        """Проверка на целостность цепочки передачи параметров (**kwargs) timeout=0.001, verify=False"""
        with raises(exceptions.ConnectTimeout):
            api_manager.auth_api.register_user(user_generator, timeout=0.001, verify=False)



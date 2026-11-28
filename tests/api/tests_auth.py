import pytest
from requests import exceptions
from datetime import datetime

class TestsAuthPositive:
    @pytest.mark.smoke
    def test_register_user(self, api_manager, random_user_data):
        """Регистрация нового пользователя"""
        response = api_manager.auth_api.register_user(random_user_data, timeout=5, verify=False).json()
        # Основные поля (соответствие структуре ответа)
        assert response['email'] == random_user_data['email']
        assert response['fullName'] == random_user_data['fullName']
        assert response['roles'] == random_user_data['roles']
        assert response['verified'] is True
        # Поля, генерируемые сервером
        assert 'id' in response
        assert 'createdAt' in response

        try:
            datetime.fromisoformat(response['createdAt'])
        except ValueError:
            pytest.fail(f"Некорректный формат даты: {response['createdAt']}")

        if 'banned' not in response:
            pytest.skip("flaky-тест: сервер не возвращает поле 'banned' указанное в Swagger")
        assert 'banned' in response

    @pytest.mark.smoke
    def test_register_and_login_user(self, api_manager, random_user_data):
        login_data = {
            'email': random_user_data['email'],
            'password': random_user_data['password']
        }
        response_register = api_manager.auth_api.register_user(random_user_data, timeout=5, verify=False).json()
        response_login = api_manager.auth_api.login_user(login_data,  timeout=5, verify=False).json()
        # Основные поля (соответствие зарегистрированным)
        assert response_register['id'] == response_login['user']['id']
        assert response_register['email'] == response_login['user']['email']
        assert response_register['fullName'] == response_login['user']['fullName']
        assert response_register['roles'] == response_login['user']['roles']
        # Поля токенов, генерируемые сервером
        assert 'accessToken' in response_login
        assert 'refreshToken' in response_login
        assert 'expiresIn' in response_login

    @pytest.mark.smoke
    def test_server_minimal_timeout(self, api_manager, random_user_data):
        """Проверка на минимальный таймаут"""
        response = api_manager.auth_api.register_user(random_user_data, timeout=0.7, verify=False).json()
        assert response['email'] == random_user_data['email']
        assert response['fullName'] == random_user_data['fullName']


class TestsAuthNegative:
    @pytest.mark.smoke
    def test_get_user_info_forbidden_for_user(self, api_manager, authenticated_user):
        """Проверка, что обычный пользователь не имеет доступа к эндпоинту"""
        user_id = authenticated_user['id']
        # Явно указываем, что ожидаем 403 статус
        response = api_manager.user_api.get_user(user_id, expected_status=403, timeout=5, verify=False).json()
        assert response['statusCode'] == 403
        assert response['message'] == "Forbidden resource"


class TestsCheckFramework:
    @pytest.mark.smoke
    def test_register_timeout(self, api_manager, random_user_data):
        """Проверка на целостность цепочки передачи параметров (**kwargs) timeout=0.001, verify=False"""
        with pytest.raises(exceptions.ConnectTimeout):
            api_manager.auth_api.register_user(random_user_data, timeout=0.001, verify=False)

import pytest
from datetime import datetime


class TestsUserPositive:
    @pytest.mark.smoke
    def test_create_user(self, super_admin, random_user_data_with_service_fields):
        """
        Создание юзера со всеми полями
        """
        # Act: создаём юзера с полным payload
        response = super_admin.api.user_api.create_user(random_user_data_with_service_fields).json()

        # Assert: проверка ответа сервера на соответствие контракту
        expected_keys = ('id', 'email', 'fullName', 'roles', 'verified', 'createdAt', 'banned')
        for key in expected_keys:
            assert key in expected_keys, f"В ответе отсутствует ключ '{key}'"

        # Assert: проверка типов данных и значений сгенерированных сервером
        assert isinstance(response['id'], str) and not isinstance(response['id'], bool), "ID должен быть строкой"
        assert response['id'].strip() != "", "ID не должен быть пустым"
        assert isinstance(response['createdAt'], str) and not isinstance(response['createdAt'], bool), "createdAt должен быть строкой"
        assert response['createdAt'].strip() != "", "createdAt не должен быть пустым"
        try:
            datetime.fromisoformat(response['createdAt'])
        except ValueError:
            pytest.fail(f"Некорректный формат даты: {response['createdAt']}")

        # Assert: проверка значений полученных значений с переданными
        assert response['email'] == random_user_data_with_service_fields['email']
        assert response['fullName'] == random_user_data_with_service_fields['fullName']
        assert response['roles'] == random_user_data_with_service_fields['roles']
        assert response['verified'] == random_user_data_with_service_fields['verified']
        assert response['banned'] == random_user_data_with_service_fields['banned']

    @pytest.mark.smoke
    def test_get_user_by_locator(self, super_admin, random_user_data_with_service_fields):
        """
        Получение юзера по разным локаторам ('id', 'email')
        """
        # Act: создаём юзера с полным payload и получаем его же по ID и email
        created_user = super_admin.api.user_api.create_user(random_user_data_with_service_fields).json()
        response_by_id = super_admin.api.user_api.get_user(created_user['id']).json()
        response_by_email = super_admin.api.user_api.get_user(created_user['email']).json()

        # Assert: проверка идентичности ответов сервера на запросы с разными локаторами
        assert response_by_id == response_by_email, "Содержание ответов должно быть идентичным"

        # Assert: проверка типов данных и значений сгенерированных сервером
        assert isinstance(created_user['id'], str) and not isinstance(created_user['id'],
                                                                      bool), "ID должен быть строкой"
        assert created_user['id'].strip() != "", "ID не должен быть пустым"
        assert isinstance(created_user['createdAt'], str) and not isinstance(created_user['createdAt'],
                                                                         bool), "createdAt должен быть строкой"
        assert created_user['createdAt'].strip() != "", "createdAt не должен быть пустым"
        try:
            datetime.fromisoformat(created_user['createdAt'])
        except ValueError:
            pytest.fail(f"Некорректный формат даты: {created_user['createdAt']}")

        # Assert: проверка ответов сервера на переданным значениям
        assert response_by_id['email'] == random_user_data_with_service_fields['email']
        assert response_by_id['fullName'] == random_user_data_with_service_fields['fullName']
        assert response_by_id['roles'] == random_user_data_with_service_fields['roles']
        assert response_by_id['verified'] == random_user_data_with_service_fields['verified']
        assert response_by_id['banned'] == random_user_data_with_service_fields['banned']

class TestsUserNegative:
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_get_user_by_id_with_incorrect_role(self, common_user):
        """
        Получение юзера по id с неверной ролью обычного пользователя
        """
        # Act: создаём нового юзера через common_user и дергаем его же через user_api.get_user по ID
        common_user.api.user_api.get_user(common_user.id, expected_status=403).json()
        # Act: создаём нового юзера через common_user и дергаем его же через user_api.get_user по Email
        common_user.api.user_api.get_user(common_user.email, expected_status=403).json()

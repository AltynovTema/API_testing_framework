"""Payload для логина пользователя."""


def get_login_payload(email: str, password: str) -> dict:
    """Возвращает тело запроса для POST /login."""
    return {
        "email": email,
        "password": password
    }

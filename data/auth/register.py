def get_register_payload(email: str, full_name: str, password: str) -> dict:
    """
    Payload для регистрации нового пользователя.
    :param email:
    :param full_name:
    :param password:
    :return: тело запроса для POST /register.
    """
    return {
        "email": email,
        "fullName": full_name,
        "password": password,
        "passwordRepeat": password,
        "roles": ["USER"]
    }

from faker import Faker

fake = Faker("en_US")


class DataGenerator():
    @staticmethod
    def generate_email() -> str:
        """Генерирует уникальный email."""
        return fake.unique.email()

    @staticmethod
    def generate_full_name() -> str:
        """Генерирует уникальное полное имя."""
        return fake.name()

    @staticmethod
    def generate_password() -> str:
        """Генерирует уникальный пароль."""
        unique_part_one = fake.last_name()
        unique_part_two = fake.random_int(min=1000000, max=9999999)
        return f"{unique_part_one}{unique_part_two}"

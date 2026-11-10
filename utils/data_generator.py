from faker import Faker


class DataGenerator:
    def __init__(self):
        self.fake = Faker("en_US")

    def generate_email(self) -> str:
        """Генерирует уникальный email."""
        return self.fake.unique.email()

    def generate_full_name(self) -> str:
        """Генерирует уникальное полное имя."""
        return self.fake.name()

    def generate_password(self) -> str:
        """Генерирует уникальный пароль."""
        unique_part_one = self.fake.last_name()
        unique_part_two = self.fake.random_int(min=1000000, max=9999999)
        return f"{unique_part_one}{unique_part_two}"

    def generate_movie_filter_params(self) -> dict:
        """Базовые параметры фильтрации (широкая выборка)."""
        return {
            "pageSize": 20,  # Берем максимум, чтобы нужные фильмы точно попали в выдачу
            "page": 1,
            "minPrice": 1,  # Согласно доке: minPrice default=1.
            "maxPrice": 1000,  # Согласно доке: maxPrice default=1000.
            "locations": None, # Согласно доке можно не указывать, для включения в выдачу и SPB, и MSK
            "published": None, # Согласно доке можно не указывать, для включения в выдачу и True, и False
            "genreId": None, # Согласно доке можно не указывать, для включения в выдачу всех жанров
            "createdAt": None # Сортировка None - сервер применит значение по умолчанию
        }

    def generate_movie_payload(self) -> dict:
        """Рандомный валидный payload для POST /movies."""
        return {
            "name": self.fake.unique.sentence(nb_words=2).rstrip('.'),
            "imageUrl": "https://image.spletnik.ru/resize/fit=cover,gravity=0.5x0.5,format=auto,width=508,height=758,dpr=2/https://image.spletnik.ru/image/2025/12/03/JwyM/original.webp",
            "price": self.fake.random_int(min=1, max=1000), # Согласно доке: minPrice default=1, maxPrice default=1000.
            "description": self.fake.unique.sentence(nb_words=9),
            "location": self.fake.random_element(elements=["SPB", "MSK"]),
            "published": self.fake.random_element(elements=[True, False]),
            "genreId": None # Подставляется в фикстуре
        }

    def generate_movie_genre(self) -> dict:
        """Генерируем уникальное имя для жанра"""
        return {"name": self.fake.unique.word()}


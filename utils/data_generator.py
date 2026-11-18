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
        minprice = self.fake.random_int(min=1, max=100000)
        maxprice = self.fake.random_int(min=minprice, max=100000)
        return {
            "pageSize": self.fake.random_int(min=1, max=20),
            "page": self.fake.random_element(elements=(1, 2)),
            "minPrice": minprice,  # Согласно доке: minPrice default=1.
            "maxPrice": maxprice,  # Согласно доке: maxPrice default=1000.
            "locations": self.fake.random_element(elements=["SPB", "MSK"]), # можно SPB и MSK
            "published": self.fake.random_element(elements=[True, False]),
            "genreId": None, # Подставляется в фикстуре
            "createdAt": self.fake.random_element(elements=["asc", "desc"])
        }

    def generate_movie_data(self) -> dict:
        """Рандомный валидный payload для POST /movies."""
        return {
            "name": self.fake.unique.sentence(nb_words=4).rstrip('.'),
            "imageUrl": "https://image.spletnik.ru/resize/fit=cover,gravity=0.5x0.5,format=auto,width=508,height=758,dpr=2/https://image.spletnik.ru/image/2025/12/03/JwyM/original.webp",
            "price": self.fake.random_int(min=1, max=1000), # Согласно доке: minPrice default=1, maxPrice default=1000.
            "description": self.fake.unique.sentence(nb_words=9),
            "location": self.fake.random_element(elements=["SPB", "MSK"]),
            "published": self.fake.random_element(elements=[True, False]),
            "genreId": None # Подставляется в фикстуре
        }

    def generate_review_data(self) -> dict:
        """Рандомный валидный payload для POST /movies/{movieId}/reviews."""
        return {
            "rating": self.fake.random_int(min=1, max=5),
            "text": self.fake.unique.sentence(nb_words=6),
        }

    def generate_movie_data_for_filters(self, filters) -> dict:
        """Рандомный валидный payload для POST /movies."""
        return {
            "name": self.fake.unique.sentence(nb_words=4).rstrip('.'),
            "imageUrl": "https://image.spletnik.ru/resize/fit=cover,gravity=0.5x0.5,format=auto,width=508,height=758,dpr=2/https://image.spletnik.ru/image/2025/12/03/JwyM/original.webp",
            "price": self.fake.random_int(min=filters["minPrice"], max=filters["maxPrice"]), # Согласно доке: minPrice default=1, maxPrice default=1000.
            "description": self.fake.unique.sentence(nb_words=9),
            "location": filters["locations"],
            "published": filters["published"],
            "genreId": None # Подставляется в фикстуре
        }


    def generate_genre_name(self) -> dict:
        """Генерируем уникальное имя для жанра"""
        return {"name": f"{self.fake.unique.word()}_{self.fake.random_int(min=1, max=1000)}"}


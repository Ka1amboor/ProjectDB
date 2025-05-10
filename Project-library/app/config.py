class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:1234@db:5432/postgres"
    SECRET_KEY = 'liba'

    # MongoDB конфигурация
    MONGO_URI = "mongodb://mongo:27017/library"

    # Redis конфигурация
    REDIS_URL = "redis://redis:6379/0"

    # Время жизни кэша (в секундах)
    CACHE_TIMEOUT = 300  # 5 минут
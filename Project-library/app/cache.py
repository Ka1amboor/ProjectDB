from . import redis_client
import json
from functools import wraps
from flask import current_app
from .serializers import serialize_for_cache, deserialize_from_cache


def get_cache(key):
    """Получение данных из кэша Redis"""
    data = redis_client.get(key)
    if data:
        try:
            cached_data = json.loads(data)
            return deserialize_from_cache(cached_data)
        except json.JSONDecodeError:
            # Если не удалось декодировать JSON, возвращаем None
            return None
    return None


def set_cache(key, value, timeout=None):
    """Сохранение данных в кэш Redis"""
    if timeout is None:
        timeout = current_app.config.get('CACHE_TIMEOUT', 300)

    # Преобразуем объект для кэширования
    serializable_value = serialize_for_cache(value)

    try:
        # Сериализуем в JSON и сохраняем
        redis_client.setex(key, timeout, json.dumps(serializable_value))
        return True
    except (TypeError, OverflowError) as e:
        # В случае ошибки записываем лог и не кэшируем
        current_app.logger.error(f"Cache serialization error: {e}")
        return False


def delete_cache(key):
    """Удаление данных из кэша Redis"""
    redis_client.delete(key)


def clear_book_cache():
    """Очистка кэша связанного с книгами"""
    for key in redis_client.scan_iter("book:*"):
        redis_client.delete(key)


def cached(key_format):
    """Декоратор для кэширования результатов функций"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Формирование ключа
            from flask_login import current_user

            key = key_format

            # Замена переменных в формате ключа
            if '{user_id}' in key and hasattr(current_user, 'user_id'):
                key = key.replace('{user_id}', str(current_user.user_id))
            if '{role}' in key and hasattr(current_user, 'role'):
                key = key.replace('{role}', str(current_user.role))

            for i, arg in enumerate(args):
                key = key.replace(f"{{{i}}}", str(arg))
            for k, v in kwargs.items():
                key = key.replace(f"{{{k}}}", str(v))

            # Проверка кэша
            cached_result = get_cache(key)
            if cached_result is not None:
                return cached_result

            result = f(*args, **kwargs)

            # Сохранение результата в кэш
            set_cache(key, result)

            return result

        return decorated_function

    return decorator
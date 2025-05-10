from flask import Response
import json


def is_json_serializable(obj):
    """Проверка, может ли объект быть сериализован в JSON."""
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False


def serialize_for_cache(obj):
    """Подготовка объекта для кэширования."""
    # Проверка для ответа Flask
    if isinstance(obj, Response):
        return {
            '_type': 'flask_response',
            'status_code': obj.status_code,
            'data': obj.get_data(as_text=True),
            'headers': dict(obj.headers),
            'mimetype': obj.mimetype,
            'direct_passthrough': obj.direct_passthrough
        }

    # Проверка для списков и словарей с вложенными неподдерживаемыми объектами
    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if is_json_serializable(value):
                result[key] = value
            else:
                result[key] = serialize_for_cache(value)
        return result

    elif isinstance(obj, list):
        result = []
        for item in obj:
            if is_json_serializable(item):
                result.append(item)
            else:
                result.append(serialize_for_cache(item))
        return result

    # Для других неподдерживаемых типов - преобразование в строку
    elif not is_json_serializable(obj):
        return str(obj)

    # Для поддерживаемых типов - возврат без изменения
    return obj


def deserialize_from_cache(obj):
    """Восстановление объекта из кэша."""
    from flask import Response

    if isinstance(obj, dict) and obj.get('_type') == 'flask_response':
        return Response(
            response=obj['data'],
            status=obj['status_code'],
            headers=obj['headers'],
            mimetype=obj['mimetype'],
            direct_passthrough=obj['direct_passthrough']
        )

    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = deserialize_from_cache(value)
        return result

    elif isinstance(obj, list):
        result = []
        for item in obj:
            result.append(deserialize_from_cache(item))
        return result

    return obj
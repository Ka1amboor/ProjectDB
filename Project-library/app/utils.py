import jwt
from datetime import datetime, timedelta
from .models import User

def checkUser(username, email):
    if User.query.filter_by(username=username).first():
        return True
    if User.query.filter_by(email=email).first():
        return True

def generate_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=30)  # Токен действует 30 минут
    }
    return jwt.encode(payload, 'liba', algorithm='HS256')

def generate_refresh_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)  # Токен действует 7 дней
    }
    return jwt.encode(payload, 'liba', algorithm='HS256')

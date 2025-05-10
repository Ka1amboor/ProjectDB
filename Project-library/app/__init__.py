from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flasgger import Swagger
from flask_pymongo import PyMongo
import redis
from flask_caching import Cache

db = SQLAlchemy()
login_manager = LoginManager()
swagger = Swagger()
mongo = PyMongo()
redis_client = None
cache = Cache()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Настройка кэша
    cache_config = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': app.config['REDIS_URL'],
        'CACHE_DEFAULT_TIMEOUT': app.config['CACHE_TIMEOUT']
    }

    # Инициализация компонентов
    db.init_app(app)
    login_manager.init_app(app)
    swagger.init_app(app)
    mongo.init_app(app)
    cache.init_app(app, config=cache_config)

    # Инициализация Redis
    global redis_client
    redis_client = redis.from_url(app.config['REDIS_URL'])

    with app.app_context():
        from . import routes, models
        db.create_all()

    return app
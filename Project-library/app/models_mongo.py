from datetime import datetime
from bson import ObjectId
from . import mongo


class LogEntry:
    @staticmethod
    def create(action, user_id=None, book_id=None, details=None):
        """Создание записи лога в MongoDB"""
        entry = {
            "action": action,
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "book_id": book_id,
            "details": details or {}
        }
        mongo.db.logs.insert_one(entry)
        return entry

    @staticmethod
    def get_user_activity(user_id, limit=50):
        """Получение активности пользователя"""
        cursor = mongo.db.logs.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        return list(cursor)

    @staticmethod
    def get_book_activity(book_id, limit=50):
        """Получение активности по книге"""
        cursor = mongo.db.logs.find({"book_id": book_id}).sort("timestamp", -1).limit(limit)
        return list(cursor)

    @staticmethod
    def search_logs(query, limit=50):
        """Поиск по логам"""
        cursor = mongo.db.logs.find(query).sort("timestamp", -1).limit(limit)
        return list(cursor)


class BookReview:
    @staticmethod
    def create(user_id, book_id, rating, review_text):
        """Создание отзыва о книге"""
        review = {
            "user_id": user_id,
            "book_id": book_id,
            "rating": rating,
            "review_text": review_text,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = mongo.db.book_reviews.insert_one(review)
        review["_id"] = result.inserted_id
        return review

    @staticmethod
    def get_book_reviews(book_id):
        """Получение всех отзывов о книге"""
        cursor = mongo.db.book_reviews.find({"book_id": book_id}).sort("created_at", -1)
        return list(cursor)

    @staticmethod
    def get_user_reviews(user_id):
        """Получение всех отзывов пользователя"""
        cursor = mongo.db.book_reviews.find({"user_id": user_id}).sort("created_at", -1)
        return list(cursor)
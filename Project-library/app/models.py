from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    role = db.Column(db.String, nullable=False)

    def get_id(self):
        return str(self.user_id)

class Book(db.Model):
    __tablename__ = 'books'
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    genre = db.Column(db.String, nullable=False)
    available_copies = db.Column(db.Integer, nullable=False)
    total_copies = db.Column(db.Integer, nullable=False)

class Rental(db.Model):
    __tablename__ = 'rentals'
    rental_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    rental_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    return_date = db.Column(db.Date, nullable=True)

    user = db.relationship("User", back_populates="rentals")
    book = db.relationship("Book", back_populates="rentals")

User.rentals = db.relationship("Rental", order_by=Rental.rental_id, back_populates="user")
Book.rentals = db.relationship("Rental", order_by=Rental.rental_id, back_populates="book")

from flask import jsonify, request, current_app as app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager, cache
from .models import User, Book, Rental
from .models_mongo import LogEntry, BookReview
from .utils import generate_access_token, generate_refresh_token, checkUser
from .cache import cached, delete_cache, clear_book_cache
from datetime import datetime
from flasgger import swag_from


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def hello_page():
    return jsonify(
        {
            "message": "Welcome to the library app!"
        }
    )

@app.route('/register/', methods=['POST'])
@swag_from({
    'tags': ['User'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'id': 'register',
                'required': ['username', 'password', 'email', 'role'],
                'properties': {
                    'username': {
                        'type': 'string',
                        'description': 'The user\'s username',
                        'default': 'Anna'
                    },
                    'password': {
                        'type': 'string',
                        'description': 'The user\'s password',
                        'default': 'password123'
                    },
                    'email': {
                        'type': 'string',
                        'description': 'The user\'s email',
                        'default': 'Anna@mail.ru'
                    },
                    'role': {
                        'type': 'string',
                        'description': 'The user\'s role: admin/reader',
                        'default': 'reader'
                    }
                }
            }
        }
    ],
    'responses': {
        '201': {
            'description': 'Registration successful!'
        },
        '400': {
            'description': 'User already exists'
        }
    }
})
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    email = data['email']
    role = data['role']
    if checkUser(username, email):
        return jsonify(
            {
                "message": "User already exists"
            }
        ), 400
    hashed_password = generate_password_hash(password, 'pbkdf2:sha256')
    new_user = User(username=username, password_hash=hashed_password, email=email, role=role)
    db.session.add(new_user)
    db.session.commit()
    user = User.query.filter_by(username=username).first()
    login_user(user)
    access_token = generate_access_token(user.user_id)
    refresh_token = generate_refresh_token(user.user_id)
    return jsonify(
        {
        "message": "Registration successful!",
        "access_token": access_token,
        "refresh_token": refresh_token
        }
    ), 201

@app.route('/login/', methods=['POST'])
@swag_from({
    'tags': ['User'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'id': 'login',
                'required': ['username', 'password'],
                'properties': {
                    'username': {
                        'type': 'string',
                        'description': 'The user\'s username',
                        'default': 'Anna'
                    },
                    'password': {
                        'type': 'string',
                        'description': 'The user\'s password',
                        'default': 'password123'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Login successful!'
        },
        '401': {
            'description': 'Login unsuccessful. Check username and/or password'
        }
    }
})
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        access_token = generate_access_token(user.user_id)
        refresh_token = generate_refresh_token(user.user_id)
        return jsonify(
            {
                "message": "Login successful!",
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        ), 200
    else:
        return jsonify(
            {
            "message": "Login unsuccessful. Check username and/or password"
            }
        ), 401

@app.route('/logout/', methods=['POST'])
@login_required
@swag_from({
    'tags': ['User'],
    'responses': {
        '200': {
            'description': 'Logout successful!'
        }
    }
})
def logout():
    logout_user()
    return jsonify(
        {
            "message": "Logout successful!"
        }
    ), 200

@app.route('/dashboard/', methods=['GET'])
@login_required
@swag_from({
    'tags': ['Book'],
    'responses': {
        '200': {
            'description': 'A list of books',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'book_id': {
                            'type': 'integer',
                            'description': 'The book ID'
                        },
                        'title': {
                            'type': 'string',
                            'description': 'The book title'
                        },
                        'author': {
                            'type': 'string',
                            'description': 'The book author'
                        },
                        'genre': {
                            'type': 'string',
                            'description': 'The book genre'
                        },
                        'available_copies': {
                            'type': 'integer',
                            'description': 'The number of available copies'
                        },
                        'total_copies': {
                            'type': 'integer',
                            'description': 'The total number of copies'
                        }
                    }
                }
            }
        }
    }
})
@cache.cached(timeout=300, key_prefix='dashboard_view_%s_%s',
              make_cache_key=lambda *args, **kwargs: f"dashboard_view_{current_user.user_id}_{current_user.role}")
def dashboard():
    user_id = current_user.user_id
    role = current_user.role

    # Логирование в MongoDB
    LogEntry.create(
        action="view_dashboard",
        user_id=user_id,
        details={"role": role}
    )

    if role == 'admin':
        books = Book.query.all()
        return jsonify(
            [
                {
                    "book_id": book.book_id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "available_copies": book.available_copies,
                    "total_copies": book.total_copies
                } for book in books
            ]
        ), 200
    else:
        available_books = Book.query.filter(Book.available_copies > 0).all()
        return jsonify(
            [
                {
                    "book_id": book.book_id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "available_copies": book.available_copies,
                    "total_copies": book.total_copies
                } for book in available_books
            ]
        ), 200

@app.route('/add_book/', methods=['POST'])
@login_required
@swag_from({
    'tags': ['Book'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'id': 'Book',
                'required': ['title', 'author', 'genre', 'total_copies'],
                'properties': {
                    'title': {
                        'type': 'string',
                        'description': 'The book title',
                        'default': 'Book Title'
                    },
                    'author': {
                        'type': 'string',
                        'description': 'The book author',
                        'default': 'Author Name'
                    },
                    'genre': {
                        'type': 'string',
                        'description': 'The book genre',
                        'default': 'Genre'
                    },
                    'total_copies': {
                        'type': 'integer',
                        'description': 'The total number of copies',
                        'default': 1
                    }
                }
            }
        }
    ],
    'responses': {
        '201': {
            'description': 'Book added successfully!'
        },
        '403': {
            'description': 'You do not have permission to access this page.'
        }
    }
})
def add_book():
    if current_user.role != 'admin':
        return jsonify(
            {
                "message": "You do not have permission to access this page."
            }
        ), 403
    data = request.get_json()
    title = data['title']
    author = data['author']
    genre = data['genre']
    total_copies = data['total_copies']
    new_book = Book(title=title, author=author, genre=genre, available_copies=total_copies, total_copies=total_copies)
    db.session.add(new_book)
    db.session.commit()

    # Логирование в MongoDB
    LogEntry.create(
        action="add_book",
        user_id=current_user.user_id,
        book_id=new_book.book_id,
        details={
            "title": title,
            "author": author,
            "genre": genre,
            "total_copies": total_copies
        }
    )

    # Очистка кэша книг
    clear_book_cache()

    return jsonify(
        {
            "message": "Book added successfully!"
        }
    ), 201

@app.route('/rent_book/<int:book_id>/', methods=['POST'])
@login_required
@swag_from({
    'tags': ['Rental'],
    'parameters': [
        {
            'name': 'book_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'The ID of the book to rent'
        }
    ],
    'responses': {
        '200': {
            'description': 'Book rented successfully!'
        },
        '400': {
            'description': 'No available copies of this book.'
        },
        '403': {
            'description': 'Admins cannot rent books.'
        }
    }
})
def rent_book(book_id):
    if current_user.role == 'admin':
        return jsonify(
            {
                "message": "Admins cannot rent books."
             }
        ), 403
    book = Book.query.get_or_404(book_id)
    if book.available_copies > 0:
        book.available_copies -= 1
        new_rental = Rental(user_id=current_user.user_id, book_id=book.book_id, rental_date=datetime.utcnow())
        db.session.add(new_rental)
        db.session.commit()

        # Логирование в MongoDB
        LogEntry.create(
            action="rent_book",
            user_id=current_user.user_id,
            book_id=book_id,
            details={
                "book_title": book.title,
                "rental_id": new_rental.rental_id,
                "rental_date": new_rental.rental_date.isoformat()
            }
        )

        # Очистка кэша книг
        clear_book_cache()

        return jsonify(
            {
                "message": "Book rented successfully!"
            }
        ), 200
    else:
        return jsonify(
            {
                "message": "No available copies of this book."
            }
        ), 400

@app.route('/refresh/', methods=['POST'])
@swag_from({
    'tags': ['Token'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'id': 'Token',
                'required': ['refresh_token'],
                'properties': {
                    'refresh_token': {
                        'type': 'string',
                        'description': 'The refresh token',
                        'default': 'refresh_token'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Access token refreshed successfully!'
        },
        '401': {
            'description': 'Invalid or expired refresh token'
        }
    }
})
def refresh():
    data = request.get_json()
    refresh_token = data['refresh_token']
    try:
        payload = jwt.decode(refresh_token, 'liba', algorithms=['HS256'])
        user_id = payload['user_id']
        access_token = generate_access_token(user_id)
        return jsonify(
            {
                "access_token": access_token
             }
        ), 200
    except jwt.ExpiredSignatureError:
        return jsonify(
            {
                "message": "Refresh token has expired"
            }
        ), 401
    except jwt.InvalidTokenError:
        return jsonify(
            {
                "message": "Invalid refresh token"
            }
        ), 401


@app.route('/book/<int:book_id>/reviews/', methods=['GET'])
@swag_from({
    'tags': ['Review'],
    'parameters': [
        {
            'name': 'book_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'The ID of the book'
        }
    ],
    'responses': {
        '200': {
            'description': 'List of reviews for the book'
        }
    }
})
def get_book_reviews(book_id):
    # Проверка существования книги
    book = Book.query.get_or_404(book_id)

    # Получение отзывов из MongoDB
    reviews = BookReview.get_book_reviews(book_id)

    # Преобразование ObjectId в строку для JSON
    for review in reviews:
        review['_id'] = str(review['_id'])

    return jsonify(reviews), 200


@app.route('/book/<int:book_id>/review/', methods=['POST'])
@login_required
@swag_from({
    'tags': ['Review'],
    'parameters': [
        {
            'name': 'book_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'The ID of the book'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'id': 'Review',
                'required': ['rating', 'review_text'],
                'properties': {
                    'rating': {
                        'type': 'integer',
                        'description': 'Rating from 1 to 5',
                        'default': 5
                    },
                    'review_text': {
                        'type': 'string',
                        'description': 'Review text',
                        'default': 'Great book!'
                    }
                }
            }
        }
    ],
    'responses': {
        '201': {
            'description': 'Review added successfully!'
        }
    }
})
def add_book_review(book_id):
    # Проверка существования книги
    book = Book.query.get_or_404(book_id)

    data = request.get_json()
    rating = data['rating']
    review_text = data['review_text']

    # Создание отзыва в MongoDB
    review = BookReview.create(
        user_id=current_user.user_id,
        book_id=book_id,
        rating=rating,
        review_text=review_text
    )

    # Логирование
    LogEntry.create(
        action="add_review",
        user_id=current_user.user_id,
        book_id=book_id,
        details={
            "rating": rating,
            "review_id": str(review["_id"])
        }
    )

    return jsonify({
        "message": "Review added successfully!",
        "review_id": str(review["_id"])
    }), 201


@app.route('/user/activity/', methods=['GET'])
@login_required
@swag_from({
    'tags': ['User'],
    'responses': {
        '200': {
            'description': 'User activity log'
        }
    }
})
def get_user_activity():
    user_id = current_user.user_id

    # Получение логов активности из MongoDB
    logs = LogEntry.get_user_activity(user_id)

    # Преобразование ObjectId в строку для JSON
    for log in logs:
        log['_id'] = str(log['_id'])

    return jsonify(logs), 200

@app.route('/book/<int:book_id>/return/', methods=['POST'])
@login_required
@swag_from({
    'tags': ['Rental'],
    'parameters': [
        {
            'name': 'book_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'The ID of the book to return'
        }
    ],
    'responses': {
        '200': {
            'description': 'Book returned successfully!'
        },
        '404': {
            'description': 'Rental not found.'
        }
    }
})
def return_book(book_id):
    rental = Rental.query.filter_by(
        user_id=current_user.user_id,
        book_id=book_id,
        return_date=None
    ).first_or_404()

    rental.return_date = datetime.utcnow()

    book = Book.query.get(book_id)
    book.available_copies += 1

    db.session.commit()

    # Логирование в MongoDB
    LogEntry.create(
        action="return_book",
        user_id=current_user.user_id,
        book_id=book_id,
        details={
            "rental_id": rental.rental_id,
            "rental_date": rental.rental_date.isoformat(),
            "return_date": rental.return_date.isoformat()
        }
    )

    clear_book_cache()

    return jsonify({
        "message": "Book returned successfully!"
    }), 200

# Функция для очистки кэша:
def clear_cache():
    cache.clear()

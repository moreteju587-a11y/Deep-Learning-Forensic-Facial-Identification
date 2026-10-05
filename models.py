from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # 'admin' or 'user'

    def __init__(self, username, password, role='user', email=None):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.role = role
        self.email = email

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class Case(db.Model):
    """One row per recognition search, so the dashboard can show real history."""
    __tablename__ = 'cases'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_image = db.Column(db.String(255), nullable=True)   # filename under static/uploads
    matched_name = db.Column(db.String(150), nullable=True)
    matched_image = db.Column(db.String(255), nullable=True)    # filename under synthetic_database
    similarity = db.Column(db.Float, nullable=True)             # None means "no match"
    crime = db.Column(db.String(255), nullable=True)
    last_seen = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('cases', lazy=True))

class Person(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Renamed 'metadata' to 'person_details' to avoid keyword conflict
    person_details = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(200), nullable=False)
    face_encoding = db.Column(db.Text, nullable=False)
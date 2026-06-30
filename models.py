from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    course = db.Column(db.String(120), default="Not specified yet")
    semester = db.Column(db.String(80), default="Not specified yet")
    bio = db.Column(db.Text, default="This student hasn't written a bio yet.")
    skills = db.Column(db.String(255), default="None listed yet")
    avatar_name = db.Column(db.String(80), default="bottts")

    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    projects = db.relationship('Project', backref='author', lazy=True)
    events = db.relationship('Event', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255))
    slots_open = db.Column(db.Integer, default=1)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    organizer = db.Column(db.String(150), nullable=False)
    date_time = db.Column(db.String(120), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    mmu_points = db.Column(db.Integer, default=50)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_username = db.Column(db.String(80), nullable=False)
    receiver_username = db.Column(db.String(80), nullable=False)
    text_content = db.Column(db.Text, nullable=False)
    time_sent = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)
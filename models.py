from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Portfolio Metadata Fields
    course = db.Column(db.String(100), default="Faculty of Computing & Informatics (FCI)")
    semester = db.Column(db.String(20), default="Trimester 1, Year 2")
    bio = db.Column(db.Text, default="MMU student looking to collaborate on innovative software developments and engineering assignments.")
    skills = db.Column(db.String(200), default="Python, HTML, CSS")
    avatar_seed = db.Column(db.String(50), default="adventurer") # Used to fetch random high-quality avatars

    # Relationships
    projects = db.relationship('Project', backref='author', lazy=True)
    events = db.relationship('Event', backref='creator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(100), nullable=False) 
    slots_open = db.Column(db.Integer, default=2)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    organizer = db.Column(db.String(100), nullable=False)
    date_time = db.Column(db.String(100), nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reward_points = db.Column(db.Integer, default=50) # MMU activity points standard
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
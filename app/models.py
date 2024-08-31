from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    root_folder = db.Column(db.String(100), nullable=False, default='')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    parent = db.relationship('Folder', remote_side=[id])
    path = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"Folder('{self.name}', '{self.path}')"

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"File('{self.name}', '{self.path}', '{self.date_uploaded}')"

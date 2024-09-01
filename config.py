import os

class Config:
    SECRET_KEY = os.urandom(24).hex()
    SQLALCHEMY_DATABASE_URI = 'postgresql://myappuser:securepassword@127.0.0.1:5432/myappdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

import os

class Config:
    SECRET_KEY = os.urandom(24).hex()
    SQLALCHEMY_DATABASE_URI = 'postgresql://myappuser:securepassword@postgresdb:5432/myappdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
#class Config:
#    SECRET_KEY = os.urandom(24).hex()
#    SQLALCHEMY_DATABASE_URI = 'sqlite:///Database/app.db'
#    SQLALCHEMY_TRACK_MODIFICATIONS = False
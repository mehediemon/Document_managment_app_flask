from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os
from flask_migrate import Migrate



app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myappuser:securepassword@127.0.0.1:5432/myappdb'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Define the path for the SQLite database
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(database_folder, "site.db")}'

# Existing setup...
db = SQLAlchemy(app)
migrate = Migrate(app, db)


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from app import routes

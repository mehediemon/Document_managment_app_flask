import os
from app import db, app
from app.models import User, Folder, File

# Define the path for the Database folder
database_folder = os.path.join(os.path.dirname(__file__), 'Database')

# Check if the Database folder exists; if not, create it
if not os.path.exists(database_folder):
    os.makedirs(database_folder)

# Define the path for the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(database_folder, "site.db")}'

with app.app_context():
    db.create_all()
    print("Database initialized successfully.")

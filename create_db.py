from app import db, app
from app.models import User, Folder, File

with app.app_context():
    db.create_all()
    print("Database initialized successfully.")

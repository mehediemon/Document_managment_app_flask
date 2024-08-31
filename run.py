from app import app, db
from app.models import User, File

if __name__ == "__main__":
    app.run(debug=True)

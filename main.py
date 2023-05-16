# app.py

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os


# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Configure the Flask app and database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


with app.app_context():
    ##from db_models.users import User
    from db_models.users import UserProfile
    db.create_all()

# Import your routes here
from api.api import register_route

# Register your routes with the Flask app
app.register_blueprint(register_route)

# Start the Flask app
if __name__ == '__main__':
    app.run()

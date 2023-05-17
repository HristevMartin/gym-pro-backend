# app.py

import os
from urllib.parse import quote_plus

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

uri = os.getenv('DATABASE_URL', '')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

safe_uri = quote_plus(uri)

app.config['SQLALCHEMY_DATABASE_URI'] = safe_uri

# Configure the Flask app and database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    ##from db_models.users import User
    db.create_all()

# Import your routes here
from api.api import register_route

# Register your routes with the Flask app
app.register_blueprint(register_route)

# Start the Flask app
if __name__ == '__main__':
    app.run()

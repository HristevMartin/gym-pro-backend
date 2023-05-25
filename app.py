import os
from urllib.parse import quote_plus

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# this is for local env
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:pass@localhost:3306/gym_db'


db_path = os.path.join(os.path.dirname(__file__), 'gym_db.sqlite')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

# Import your routes here
from api.api import register_route

# Register your routes with the Flask app
app.register_blueprint(register_route)

# Start the Flask app
if __name__ == '__main__':
    app.run()

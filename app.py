import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient


app = Flask(__name__)

app.config['SENDGRID_API_KEY'] = os.getenv('SENDGRID_API_KEY')
sendgrid_client = SendGridAPIClient(app.config['SENDGRID_API_KEY'])

CORS(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

import sys
import logging

if app.debug is not True:   # configure logging for when app.debug is False
    stream_handler = logging.StreamHandler(sys.stdout)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)

# Start the Flask app
if __name__ == '__main__':
    app.run()

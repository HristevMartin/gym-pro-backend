import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient

app = Flask(__name__)

app.config['SENDGRID_API_KEY'] = os.getenv('SENDGRID_API_KEY')
sendgrid_client = SendGridAPIClient(app.config['SENDGRID_API_KEY'])

CORS(app,  supports_credentials=True)

db_path = os.path.join(os.path.dirname(__file__), 'gym_db.sqlite')

user = os.environ.get('user')
password = os.environ.get('password')
host = os.environ.get('host')
port = os.environ.get('port')
database = os.environ.get('database')

if os.getenv('project') == 'local':
    db_uri = 'sqlite:///{}'.format(db_path)
else:
    db_uri = f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

with app.app_context():
    from db_models.Equipment import GymItem
    from db_models.users import User,UserProfile
    from db_models.token import Token
    from db_models.forum import Forum, View
    from db_models.forum import Reaction
    from db_models.forum import Comment
    from db_models.users import UserActivity
    from db_models.Equipment import Rating, CommentItem, Like
    db.create_all()
    # db.drop_all()

# Import your routes here
from api.api import register_route


# Register your routes with the Flask app
app.register_blueprint(register_route)

# Start the Flask app
if __name__ == '__main__':
    app.run()

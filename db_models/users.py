from db_models.enums import RoleType
from main import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleType), default=RoleType.default, nullable=False)
    # create column in the user table to be optional for user profile image
    image_url = db.Column(db.String(255), nullable=True)

    gym_items = db.relationship('GymItem', backref='user')


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    hobby = db.Column(db.String(100))
    user_id = db.Column(db.Integer)

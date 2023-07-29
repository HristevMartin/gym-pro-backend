from db_models.enums import RoleType
from app import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleType), default=RoleType.default, nullable=False)
    # create column in the user table to be optional for user profile image
    image_url = db.Column(db.String(255), nullable=True)

    gym_items = db.relationship('GymItem', backref='user')

    def __to_dict__(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
        }


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    hobby = db.Column(db.String(100))
    user_id = db.Column(db.Integer)
    image_filename = db.Column(db.String(255), nullable=True)

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, nullable=False)
    logout_time = db.Column(db.DateTime)

    def __init__(self, user_id, login_time, logout_time=None):
        self.user_id = user_id
        self.login_time = login_time
        self.logout_time = logout_time

    def __repr__(self):
        return f"<UserActivity id={self.id}, user_id={self.user_id}, login_time={self.login_time}, logout_time={self.logout_time}>"
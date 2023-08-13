from app import db


class GymItem(db.Model):
    __tablename__ = "gym_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    image_url_path = db.Column(db.String(255), nullable=True)
    # create a relationship with the user table
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    item_id = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    seller = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    mobile_number = db.Column(db.String(255), nullable=True)

    # ratings = db.relationship('Rating', backref='gym_item', lazy=True)

    # comment_items = db.relationship('CommentItem', backref='gym_item', lazy=True)

from datetime import datetime

class Rating(db.Model):
    __tablename__ = "rating"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String, nullable=False)  # set as ForeignKey
    user_id = db.Column(db.Integer, db.ForeignKey('user.id') ,nullable=False)
    star_rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'item_id', name='_user_gym_item_uc'),)


class CommentItem(db.Model):
    __tablename__ = "comment_item"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    gym_id = db.Column(db.String, nullable=False)

class Like(db.Model):
    __tablename__ = "like_item"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment_id = db.Column(db.String(255), nullable=False)
    like_count = db.Column(db.Integer, default=0)
    item_id = db.Column(db.Integer, db.ForeignKey('gym_items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

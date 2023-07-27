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

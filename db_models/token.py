from main import db


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(255), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)

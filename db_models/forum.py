from collections import defaultdict

from app import db


class Forum(db.Model):
    __tablename__ = 'forum'
    # create primary key
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2048), nullable=False)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments_num = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('forum_posts', lazy=True))
    comments = db.relationship('Comment', backref='forum', lazy=True, cascade="all, delete-orphan")

    def __init__(self, title, description, user_id):
        self.title = title
        self.description = description
        self.user_id = user_id

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'views': self.views,
            'likes': self.likes,
            'comments': self.comments_num,
            'user_id': self.user_id
        }


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(2048), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'), nullable=False)

    def __init__(self, content, user_id, forum_id):
        self.content = content
        self.user_id = user_id
        self.forum_id = forum_id

    def to_dict(self):
        # create a dictionary to store the reactions
        reactions_dict = defaultdict(list)

        # iterate over each reaction to this comment
        for reaction in self.reactions:
            # append the user's username to the list of users for this emoji
            reactions_dict[reaction.emoji].append(reaction.user.email)

        # return the comment data, including the reactions
        return {
            'id': self.id,
            'content': self.content,
            'author': self.user_id,
            'user_id': self.user_id,
            'forum_id': self.forum_id,
            'reactions': reactions_dict,  # this is the reactions data
        }


class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)

    comment = db.relationship('Comment', backref=db.backref('reactions',cascade="all,delete", lazy=True))
    user = db.relationship('User', backref=db.backref('reactions', lazy=True))


class View(db.Model):
    __tablename__ = 'views'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'), primary_key=True)

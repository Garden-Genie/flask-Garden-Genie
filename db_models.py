import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import pymysql

pymysql.install_as_MySQLdb()

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
db = SQLAlchemy(app)

class Follow(db.Model):
    __tablename__ = 'follow'

    f_id = db.Column(db.Integer, primary_key=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.user_num'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.user_num'), nullable=False)

    to_user = db.relationship('User', foreign_keys=[to_user_id], back_populates='followers')
    from_user = db.relationship('User', foreign_keys=[from_user_id], back_populates='following')

    def __init__(self, to_user, from_user):
        self.to_user = to_user
        self.from_user = from_user

class User(db.Model):
    __tablename__ = 'user'

    user_num = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(20), nullable=False)
    user_name = db.Column(db.String(20), nullable=False)
    user_pwd = db.Column(db.String(20), nullable=False)
    user_email = db.Column(db.String(50), nullable=False, unique=True)

    authorities = db.relationship('Authority', back_populates='user', cascade='all, delete-orphan', lazy='joined')
    hearts = db.relationship('Heart', back_populates='liker', cascade='all, delete-orphan', lazy='joined')
    followers = db.relationship('Follow', foreign_keys=[Follow.to_user_id], back_populates='to_user')
    following = db.relationship('Follow', foreign_keys=[Follow.from_user_id], back_populates='from_user')

    def set_authorities(self, authorities):
        self.authorities = authorities
        for authority in authorities:
            authority.user = self

    def set_hearts(self, hearts):
        self.hearts = hearts
        for heart in hearts:
            heart.liker_id = self.user_num

    def __init__(self, user_id, user_name, user_pwd, user_email):
        self.user_id = user_id
        self.user_name = user_name
        self.user_pwd = user_pwd
        self.user_email = user_email


class Authority(db.Model):
    __tablename__ = 'authority'

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(255), nullable=False)

    user_num = db.Column(db.Integer, db.ForeignKey('user.user_num'))
    user = db.relationship('User', back_populates='authorities')

    def set_user(self, user):
        self.user = user

    def __init__(self, user_name):
        self.user_name = user_name

class Plant(db.Model):
    __tablename__ = 'plant'

    plt_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False)
    plt_img = db.Column(db.String(255), nullable=False)
    plt_name = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.String(20), nullable=False)

    def __init__(self, plt_name, plt_img, user_id):
        self.plt_name = plt_name
        self.plt_img = plt_img
        self.user_id = user_id
        self.created_at = datetime.utcnow()


class Story(db.Model):
    __tablename__ = 'story'

    story_id = db.Column(db.Integer, primary_key=True)
    plt_id = db.Column(db.Integer, db.ForeignKey('plant.plt_id'), nullable=False)
    plant = db.relationship('Plant')
    story_date = db.Column(db.DateTime, nullable=False)
    story_explain = db.Column(db.Text)
    story_music = db.Column(db.String(255))
    story_poem = db.Column(db.Text)
    story_condition = db.Column(db.Text)
    upload = db.Column(db.Boolean, default=False)

    hearts = db.relationship('Heart', back_populates='story', cascade='all, delete-orphan', lazy='joined')

    def set_hearts(self, hearts):
        self.hearts = hearts
        for heart in hearts:
            heart.story = self

    def __init__(self, story_date, story_explain, story_music, story_poem, story_condition, plant, upload):
        self.story_date = story_date
        self.story_explain = story_explain
        self.story_music = story_music
        self.story_poem = story_poem
        self.story_condition = story_condition
        self.plant = plant
        self.upload = upload


class Heart(db.Model):
    __tablename__ = 'heart'

    h_id = db.Column(db.Integer, primary_key=True)
    liker_id = db.Column(db.Integer, db.ForeignKey('user.user_num'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.story_id'), nullable=False)

    liker = db.relationship('User', back_populates='hearts')
    story = db.relationship('Story', back_populates='hearts')

    def __init__(self, liker, story):
        self.liker = liker
        self.story = story



import os
from datetime import datetime
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity


load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # JWT 비밀 키 설정
jwt = JWTManager(app)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'User'

    user_id = db.Column(db.String(20), primary_key=True)
    user_name = db.Column(db.String(20), nullable=False)
    user_pwd = db.Column(db.String(20), nullable=False)
    user_email = db.Column(db.String(50), nullable=False, unique=True)

    def __init__(self, user_id, user_name, user_pwd, user_email):
        self.user_id = user_id
        self.user_name = user_name
        self.user_pwd = user_pwd
        self.user_email = user_email


class Plant(db.Model):
    __tablename__ = 'Plant'

    plt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plt_name = db.Column(db.String(20), nullable=False)
    plt_img = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(20), db.ForeignKey('User.user_id'), nullable=False)

    user = db.relationship('User', backref='plants')

    def __init__(self, plt_name, plt_img, user_id):
        self.plt_name = plt_name
        self.plt_img = plt_img
        self.user_id = user_id


class Story(db.Model):
    __tablename__ = 'Story'

    story_id = db.Column(db.Integer, primary_key=True)
    story_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    plt_name = db.Column(db.String(30), nullable=False)
    story_explain = db.Column(db.Text)
    story_music = db.Column(db.String(100))
    story_poem = db.Column(db.Text)
    story_condition = db.Column(db.String(30))
    user_id = db.Column(db.String(20), db.ForeignKey('User.user_id'), nullable=False)
    plt_id = db.Column(db.Integer, db.ForeignKey('Plant.plt_id'), nullable=False)

    user = db.relationship('User', backref='stories')
    plant = db.relationship('Plant', backref='story')

    def __init__(self, plt_name, story_explain, story_music, story_poem, story_condition, user_id, plt_id):
        self.plt_name = plt_name
        self.story_explain = story_explain
        self.story_music = story_music
        self.story_poem = story_poem
        self.story_condition = story_condition
        self.user_id = user_id
        self.plt_id = plt_id



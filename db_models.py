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


class User(db.Model):
    __tablename__ = 'user'

    user_num = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(20), nullable=False)
    user_name = db.Column(db.String(20), nullable=False)
    user_email = db.Column(db.String(50), nullable=False)
    user_pwd = db.Column(db.String(255), nullable=False)

    def __init__(self, user_name, user_id, user_email, user_pwd):
        self.user_name = user_name
        self.user_id = user_id
        self.user_email = user_email
        self.user_pwd = user_pwd


class Authority(db.Model):
    __tablename__ = 'authority'

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(255), nullable=False)
    user_num = db.Column(db.BigInteger, db.ForeignKey('user.user_num'))

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


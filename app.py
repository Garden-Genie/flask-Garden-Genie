import os
from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from img_detection import index, analyze_image
from db_models import db, Plant
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
jwt = JWTManager(app)

db.init_app(app)

# 라우트 등록
app.add_url_rule('/', 'index', index)
app.add_url_rule('/analyze', 'analyze_image', analyze_image, methods=['POST'])

if __name__ == '__main__':
    app.run(port=80)

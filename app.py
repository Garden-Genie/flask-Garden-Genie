import os
from flask import Flask, render_template
from img_detection import analyze_image
from img_detection import index
from db_models import db, Plant
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
db.init_app(app)

# 라우트 등록
# app.add_url_rule('/analyze', 'analyze_image', analyze_image, methods=['POST'])
app.add_url_rule('/', 'index', index)

if __name__ == '__main__':
    app.run(debug=True)

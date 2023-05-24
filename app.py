from flask import Flask, render_template
from views import analyze_image
from models1 import db, Plant

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:mysqlweather0101!@127.0.0.1:3306/testdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 데이터베이스 생성
with app.app_context():
    db.create_all()

# 라우트 등록
app.add_url_rule('/analyze', 'analyze_image', analyze_image, methods=['POST'])
app.add_url_rule('/', 'index', lambda: render_template('test_img.html'))

if __name__ == '__main__':
    app.run()

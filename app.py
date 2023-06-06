from flask import Flask, render_template
from img_detection import analyze_image
from img_detection import index
from db_models import db, Plant

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:mysqlweather0101!@localhost:3306/testdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# 라우트 등록
app.add_url_rule('/analyze', 'analyze_image', analyze_image, methods=['POST'])
app.add_url_rule('/', 'index', index)

if __name__ == '__main__':
    app.run(debug=True)

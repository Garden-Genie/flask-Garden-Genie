from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Plant(db.Model):
    __tablename__ = 'plant'
    plt_id = db.Column(db.Integer, primary_key=True)
    plt_name = db.Column(db.String(20), nullable=False)
    plt_img = db.Column(db.String(50))

    def save(self):
        db.session.add(self)
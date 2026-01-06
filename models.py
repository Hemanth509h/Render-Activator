from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class TargetURL(db.Model):
    id = db.Column(db.Column(db.Integer, primary_key=True))
    url = db.Column(db.String(500), unique=True, nullable=False)

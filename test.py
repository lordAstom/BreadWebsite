from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# initialize the app with the extension
db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    date = db.Column(db.String(255), nullable=False)
    time_day = db.Column(db.String(255), nullable=False)
    num_breads = db.Column(db.Integer)

def find_num_breads(date,time):
        stmt = """SELECT SUM(num_breads) FROM "order" WHERE time_day = '"""+time+"""' AND date = '"""+date+"""'"""
        b = db.session.execute(stmt)
        return b.first()[0]

for i in range(10):
     if i == 3:
          break
     print(i)


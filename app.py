import os

from datetime import datetime, timezone
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('skey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('MYPROJECT_DBURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)


# Information on each student stored as archive

class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    rank = db.Column(db.Integer)
    level = db.Column(db.String(10))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    extra = db.Column(db.String(100))


# Information on each belt ordered

class Belt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_date = db.Column(db.DateTime(), default=datetime.now(timezone.utc), index=True)
    rank = db.Column(db.Integer)
    size = db.Column(db.Integer)
    is_ordered = db.Column(db.Boolean)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    extra = db.Column(db.String(100))


# Information on each order actually ordered

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime(), default=datetime.now(timezone.utc), index=True)
    schoolorders = db.relationship('Schoolorder', backref=db.backref('order'))
    extra = db.Column(db.String(100))


# Bridge Order and Belt

class Orderbelt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    belt_id = db.Column(db.Integer, db.ForeignKey('belt.id'), nullable=False)
    extra = db.Column(db.String(100))


# Information on each school

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100))
    extra = db.Column(db.String(100))
    students = db.relationship('Student', backref=db.backref(
        'school'), order_by="Student.last_name,Student.first_name")
    schoolorders = db.relationship('Schoolorder', backref=db.backref('school'))


# Information on each school order actually ordered

class Schoolorder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    extra = db.Column(db.String(100))


# Information on each student

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), index=True)
    rank = db.Column(db.Integer)
    level = db.Column(db.String(10), index=True)
    last_size = db.Column(db.Integer)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    extra = db.Column(db.String(100))


# Users will be Instructors

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(228))
    role = db.Column(db.String(10), default='instructor')
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    extra = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



import routes

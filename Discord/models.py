from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Hilfstabelle für Server-Mitglieder
members = db.Table('members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('server_id', db.Integer, db.ForeignKey('server.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    friends = db.Column(db.Text, default="") # Vereinfacht als Liste von IDs

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    members = db.relationship('User', secondary=members, backref='servers')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'))
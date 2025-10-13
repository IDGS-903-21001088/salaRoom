from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')  # 'superadmin' o 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_superadmin(self):
        return self.role == 'superadmin'


class MeetingRoom(db.Model):
    __tablename__ = 'meeting_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    time_slot = db.Column(db.String(20), nullable=False)
    leader = db.Column(db.String(100), nullable=False)
    leader_email = db.Column(db.String(120), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    remarks = db.Column(db.String(300))
    date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='meetings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'time_slot': self.time_slot,
            'leader': self.leader,
            'leader_email': self.leader_email,
            'subject': self.subject,
            'remarks': self.remarks,
            'date': self.date.strftime('%Y-%m-%d'),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
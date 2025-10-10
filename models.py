from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MeetingRoom(db.Model):
    __tablename__ = 'meeting_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    time_slot = db.Column(db.String(20), nullable=False)
    leader = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    remarks = db.Column(db.String(300))
    date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    
    def to_dict(self):
        return {
            'id': self.id,
            'time_slot': self.time_slot,
            'leader': self.leader,
            'subject': self.subject,
            'remarks': self.remarks,
            'date': self.date.strftime('%Y-%m-%d')
        }
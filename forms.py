from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length

class MeetingRoomForm(FlaskForm):
    time_slot = SelectField('Horario', 
        choices=[
            ('8:00-8:30', '8:00-8:30'),
            ('8:30-9:00', '8:30-9:00'),
            ('9:00-9:30', '9:00-9:30'),
            ('9:30-10:00', '9:30-10:00'),
            ('10:00-10:30', '10:00-10:30'),
            ('10:30-11:00', '10:30-11:00'),
            ('11:00-11:30', '11:00-11:30'),
            ('11:30-12:00', '11:30-12:00'),
            ('12:00-12:30', '12:00-12:30'),
            ('12:30-13:00', '12:30-13:00'),
            ('13:00-13:30', '13:00-13:30'),
            ('13:30-14:00', '13:30-14:00'),
            ('14:00-14:30', '14:00-14:30'),
            ('14:30-15:00', '14:30-15:00'),
            ('15:00-15:30', '15:00-15:30'),
            ('15:30-16:00', '15:30-16:00'),
            ('16:00-16:30', '16:00-16:30'),
            ('16:30-17:00', '16:30-17:00'),
            ('17:00-17:30', '17:00-17:30'),
            ('17:30-18:00', '17:30-18:00'),
        ],
        validators=[DataRequired()])
    
    leader = StringField('Responsable/Líder', 
        validators=[DataRequired(), Length(max=100)])
    
    subject = StringField('Asunto', 
        validators=[DataRequired(), Length(max=200)])
    
    remarks = TextAreaField('Observaciones', 
        validators=[Length(max=300)])
    
    date = DateField('Fecha', 
        format='%Y-%m-%d',
        validators=[DataRequired()])
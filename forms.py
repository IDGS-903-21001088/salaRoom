from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField, PasswordField, EmailField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Correo Electrónico', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', 
        validators=[DataRequired(), Length(min=6, message='La contraseña debe tener al menos 6 caracteres')])
    confirm_password = PasswordField('Confirmar Contraseña', 
        validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')])

class UserForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Length(min=6)])
    role = SelectField('Rol', 
        choices=[('user', 'Usuario'), ('admin', 'Administrador'), ('superadmin', 'Super Administrador')],
        validators=[DataRequired()])
    
    def validate_username(self, username):
        if hasattr(self, 'user_id'):
            user = User.query.filter(User.username == username.data, User.id != self.user_id).first()
        else:
            user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso.')
    
    def validate_email(self, email):
        if hasattr(self, 'user_id'):
            user = User.query.filter(User.email == email.data, User.id != self.user_id).first()
        else:
            user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este correo electrónico ya está registrado.')

class RoomForm(FlaskForm):
    """Formulario para crear/editar salas físicas"""
    name = StringField('Nombre de la Sala', 
        validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', 
        validators=[Length(max=300)])
    capacity = IntegerField('Capacidad (personas)', 
        validators=[DataRequired(), NumberRange(min=1, max=1000, message='La capacidad debe ser entre 1 y 1000')])

class MeetingRoomForm(FlaskForm):
    """Formulario para reservar salas"""
    room_id = SelectField('Sala', coerce=int, validators=[DataRequired()])
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
    
    leader_email = EmailField('Correo del Responsable', 
        validators=[DataRequired(), Email()])
    
    subject = StringField('Asunto', 
        validators=[DataRequired(), Length(max=200)])
    
    remarks = TextAreaField('Observaciones', 
        validators=[Length(max=300)])
    
    date = DateField('Fecha', 
        format='%Y-%m-%d',
        validators=[DataRequired()])
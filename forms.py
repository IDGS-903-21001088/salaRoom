# forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, SubmitField, TextAreaField, SelectField,
    PasswordField, IntegerField
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, ValidationError
from datetime import date

# Compatibilidad con distintas versiones de WTForms
try:
    from wtforms.fields import EmailField
except Exception:
    try:
        from wtforms import EmailField
    except Exception:
        EmailField = StringField

# Horarios para agendar citas
TIME_SLOTS = [
    ('8:00-8:30','8:00-8:30'), ('8:30-9:00','8:30-9:00'), ('9:00-9:30','9:00-9:30'),
    ('9:30-10:00','9:30-10:00'), ('10:00-10:30','10:00-10:30'), ('10:30-11:00','10:30-11:00'),
    ('11:00-11:30','11:00-11:30'), ('11:30-12:00','11:30-12:00'), ('12:00-12:30','12:00-12:30'),
    ('12:30-13:00','12:30-13:00'), ('13:00-13:30','13:00-13:30'), ('13:30-14:00','13:30-14:00'),
    ('14:00-14:30','14:00-14:30'), ('14:30-15:00','14:30-15:00'), ('15:00-15:30','15:00-15:30'),
    ('15:30-16:00','15:30-16:00'), ('16:00-16:30','16:00-16:30'), ('16:30-17:00','16:30-17:00'),
    ('17:00-17:30','17:00-17:30'), ('17:30-18:00','17:30-18:00')
]


class LoginForm(FlaskForm):
    """
    Inicio de sesión por correo (email) en lugar de usuario.
    """
    email = EmailField('Correo Electrónico', validators=[
        DataRequired(message='El correo es requerido'),
        Email(message='Correo inválido'),
        Length(max=120)
    ])
    password = PasswordField('Contraseña', validators=[DataRequired(message='La contraseña es requerida')])
    submit = SubmitField('Iniciar Sesión')


class ForgotPasswordForm(FlaskForm):
    email = EmailField('Correo Electrónico', validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'Nueva Contraseña',
        validators=[DataRequired(), Length(min=6, message='La contraseña debe tener al menos 6 caracteres')]
    )
    confirm_password = PasswordField(
        'Confirmar Contraseña',
        validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')]
    )
    submit = SubmitField('Restablecer Contraseña')


class UserForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Length(min=6)])
    role = SelectField(
        'Rol',
        choices=[('user', 'Usuario'), ('admin', 'Administrador'), ('superadmin', 'Super Administrador')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Guardar')

    def validate_username(self, username):
        from models import User, db
        if hasattr(self, 'user_id'):
            user = db.session.query(User).filter(User.username == username.data, User.id != self.user_id).first()
        else:
            user = db.session.query(User).filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso.')

    def validate_email(self, email):
        from models import User, db
        if hasattr(self, 'user_id'):
            user = db.session.query(User).filter(User.email == email.data, User.id != self.user_id).first()
        else:
            user = db.session.query(User).filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este correo electrónico ya está registrado.')


class RoomForm(FlaskForm):
    name = StringField('Nombre de la Sala', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Length(max=300)])
    capacity = IntegerField(
        'Capacidad (personas)',
        validators=[DataRequired(), NumberRange(min=1, max=1000, message='La capacidad debe ser entre 1 y 1000')]
    )
    plant_id = SelectField('Planta', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')


class MeetingRoomForm(FlaskForm):
    date = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])
    plant_id = SelectField('Planta', coerce=int, validators=[DataRequired()])
    room_id = SelectField('Sala', coerce=int, validators=[DataRequired()])
    time_slot = SelectField('Horario', choices=TIME_SLOTS, validators=[DataRequired()])
    leader = StringField('Responsable/Líder', validators=[DataRequired(), Length(max=100)])
    leader_email = EmailField('Correo del Responsable', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('Asunto', validators=[DataRequired(), Length(max=200)])
    remarks = TextAreaField('Observaciones', validators=[Length(max=300)])
    submit = SubmitField('Guardar')
    
    def validate_date(self, field):
        """Validar que la fecha no sea anterior al día de hoy"""
        if field.data < date.today():
            raise ValidationError('No se pueden agendar reuniones en fechas pasadas. Por favor selecciona la fecha de hoy o una fecha futura.')

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from config import DevelopmentConfig
from models import db, MeetingRoom, User
from forms import MeetingRoomForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, UserForm
from datetime import datetime, timedelta
from functools import wraps
import secrets
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db.init_app(app)
mail = Mail(app)

# Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decorador para superadmin
def superadmin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_superadmin():
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# Función de envío de correo
def send_email(subject, recipient, body):
    try:
        mail.send(Message(subject, recipients=[recipient], body=body))
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

# Inicialización: crear tablas y usuario por defecto (si no existe)
with app.app_context():
    db.create_all()
    # Comprueba existencia por username o email antes de crear
    existing = User.query.filter(
        or_(User.username == 'superadmin', User.email == 'juangaytangg332@gmail.com')
    ).first()
    if not existing:
        admin = User(username='superadmin', email='juangaytangg332@gmail.com', role='superadmin')
        admin.set_password('admin123')
        db.session.add(admin)
        try:
            db.session.commit()
            print("Super Admin creado: usuario='superadmin', contraseña='admin123'")
        except IntegrityError:
            db.session.rollback()
            print("No se pudo crear el Super Admin: ya existe un registro con ese username o email.")

# ========== AUTENTICACIÓN ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Bienvenido {user.username}!', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('login'))

# NOTE: endpoint y nombre de ruta normalizados a ASCII
@app.route('/olvide-contrasena', methods=['GET', 'POST'], endpoint='olvide_contrasena')
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Error al generar token de restablecimiento', 'danger')
                return redirect(url_for('login'))
            
            reset_url = url_for('reset_password', token=token, _external=True)
            body = f"""Hola {user.username},

Has solicitado restablecer tu contraseña en el Sistema de Salas de Reuniones WASION.

Por favor haz clic en el siguiente enlace para restablecer tu contraseña:

{reset_url}
 
Si no solicitaste este cambio, puedes ignorar este mensaje.

Sistema WASION"""
            
            send_email('Restablecer Contraseña - WASION', user.email, body)
            flash('Si el correo existe, recibirás instrucciones para restablecer tu contraseña', 'info')
        else:
            # No revelar si el email existe; comportamiento informado arriba
            flash('Si el correo existe, recibirás instrucciones para restablecer tu contraseña', 'info')
        return redirect(url_for('login'))
    # Asegúrate de que el archivo de plantilla se llame: templates/olvide_contrasena.html
    return render_template('olvide_contraseña.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('El enlace de restablecimiento es inválido o ha expirado', 'danger')
        # actualizar para usar el endpoint nuevo
        return redirect(url_for('olvide_contraseña'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Error al actualizar la contraseña', 'danger')
            return redirect(url_for('login'))
        flash('Tu contraseña ha sido actualizada exitosamente', 'success')
        return redirect(url_for('login'))
    return render_template('restablecer.html', form=form)

## GESTIÓN DE USUARIOS

@app.route('/users')
@superadmin_required
def users():
    return render_template('usuarios.html', users=User.query.all())

@app.route('/users/add', methods=['GET', 'POST'])
@superadmin_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        # prevenir duplicados por correo o username
        if User.query.filter(or_(User.username == form.username.data, User.email == form.email.data)).first():
            flash('El username o el email ya están en uso', 'danger')
            return render_template('usuario_form.html', form=form, action='Crear')
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Error al crear usuario (posible duplicado)', 'danger')
            return render_template('usuario_form.html', form=form, action='Crear')
        flash('Usuario creado exitosamente', 'success')
        return redirect(url_for('users'))
    return render_template('usuario_form.html', form=form, action='Crear')

@app.route('/users/delete/<int:id>', methods=['POST'])
@superadmin_required
def delete_user(id):
    if id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('users'))
    
    db.session.delete(User.query.get_or_404(id))
    db.session.commit()
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('users'))

## GESTIÓN DE REUNIONES 

@app.route('/')
@login_required
def index():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    meetings = MeetingRoom.query.filter_by(date=date).order_by(MeetingRoom.time_slot).all()
    return render_template('room.html', meetings=meetings, selected_date=date_str)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_meeting():
    form = MeetingRoomForm()
    if form.validate_on_submit():
        if MeetingRoom.query.filter_by(date=form.date.data, time_slot=form.time_slot.data).first():
            flash('Ya existe una reunión reservada en ese horario', 'danger')
            return render_template('formulario.html', form=form, action='Agregar')
        
        meeting = MeetingRoom(
            time_slot=form.time_slot.data, leader=form.leader.data,
            leader_email=form.leader_email.data, subject=form.subject.data,
            remarks=form.remarks.data, date=form.date.data, created_by=current_user.id
        )
        db.session.add(meeting)
        db.session.commit()
        
        body = f"""Hola {meeting.leader},

Tu reservación de sala de reuniones ha sido confirmada exitosamente.

Detalles de la Reunión:
- Fecha: {meeting.date.strftime('%d/%m/%Y')}
- Horario: {meeting.time_slot}
- Asunto: {meeting.subject}
- Observaciones: {meeting.remarks or 'N/A'}

Reservado por: {current_user.username}

Saludos,
Sistema de Salas WASION"""
        
        send_email('Confirmación de Reservación - WASION', meeting.leader_email, body)
        flash('Reunión agregada exitosamente. Se ha enviado un correo de confirmación.', 'success')
        return redirect(url_for('index', date=form.date.data.strftime('%Y-%m-%d')))
    
    form.date.data = datetime.now().date()
    return render_template('formulario.html', form=form, action='Agregar')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit_meeting(id):
    meeting = MeetingRoom.query.get_or_404(id)
    form = MeetingRoomForm(obj=meeting)
    
    if form.validate_on_submit():
        if MeetingRoom.query.filter(
            MeetingRoom.date == form.date.data,
            MeetingRoom.time_slot == form.time_slot.data,
            MeetingRoom.id != id
        ).first():
            flash('Ya existe una reunión reservada en ese horario', 'danger')
            return render_template('formulario.html', form=form, action='Editar', meeting=meeting)
        
        meeting.time_slot = form.time_slot.data
        meeting.leader = form.leader.data
        meeting.leader_email = form.leader_email.data
        meeting.subject = form.subject.data
        meeting.remarks = form.remarks.data
        meeting.date = form.date.data
        db.session.commit()
        flash('Reunión actualizada exitosamente', 'success')
        return redirect(url_for('index', date=meeting.date.strftime('%Y-%m-%d')))
    
    return render_template('formulario.html', form=form, action='Editar', meeting=meeting)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
@superadmin_required
def delete_meeting(id):
    meeting = MeetingRoom.query.get_or_404(id)
    date = meeting.date.strftime('%Y-%m-%d')
    db.session.delete(meeting)
    db.session.commit()
    flash('Reunión eliminada exitosamente', 'success')
    return redirect(url_for('index', date=date))

if __name__ == '__main__':
    app.run(debug=True)

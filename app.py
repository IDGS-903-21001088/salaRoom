from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from config import DevelopmentConfig
from models import db, MeetingRoom, User, Room, Plant
from forms import MeetingRoomForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, UserForm, RoomForm
from datetime import datetime, timedelta, date, timezone
from functools import wraps
import secrets
from functools import wraps
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from flask import make_response

import logging
logging.basicConfig(level=logging.DEBUG)

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
    return db.session.get(User, int(user_id))


def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return no_cache_view


# Decoradores de permisos
def superadmin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_superadmin():
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Permite acceso a admin y superadmin"""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not (current_user.is_admin() or current_user.is_superadmin()):
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# Función de envío de correo
def send_email(subject, recipient, body):
    try:
        msg = Message(subject, recipients=[recipient], body=body)
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Error al enviar correo: {e}")
        return False

# Crear tablas y datos iniciales
with app.app_context():
    db.create_all()

    # Crear superadmin 
    existing = db.session.query(User).filter(
        or_(User.username == 'superadmin', User.email == 'salaswasion@gmail.com')
    ).first()
    if not existing:
        admin = User(username='superadmin', email='salaswasion@gmail.com', role='superadmin')
        admin.set_password('admin123')
        db.session.add(admin)
        try:
            db.session.commit()
            app.logger.info("Super Admin creado: usuario='superadmin', contraseña='admin123'")
            existing = admin
        except IntegrityError:
            db.session.rollback()
            existing = db.session.query(User).filter_by(username='superadmin').first()



    # Crear plantas 1 al 7 
    for i in range(1, 8):
        name = f"Planta {i}"
        if not db.session.query(Plant).filter_by(name=name).first():
            p = Plant(name=name, description=f"Planta {i}", created_by=(existing.id if existing else None))
            db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()



    # filtro de salas 
    for i in range(8, 11):
        name = f"Planta {i}"
        if not db.session.query(Plant).filter_by(name=name).first():
            p = Plant(name=name, description=f"Planta {i}", created_by=(existing.id if existing else None))
            db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()



# LOGIN Y AUTENTICACIÓN

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Bienvenido {user.email}!', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('login'))

@app.route('/olvide-contrasena', methods=['GET', 'POST'], endpoint='olvide_contrasena')
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user:
            try:
                token = secrets.token_urlsafe(32)
                user.reset_token = token
                # CORRECCIÓN: Asegurar que sea timezone-aware
                user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
                db.session.commit()
                app.logger.info(f"Token generado para {user.email}: {token}")
                
                reset_url = url_for('reset_password', token=token, _external=True)
                app.logger.info(f"URL de reset: {reset_url}")
                
                body = f"""Hola {user.username},

Has solicitado restablecer tu contraseña en el Sistema de Salas de Reuniones WASION.

Por favor haz clic en el siguiente enlace para restablecer tu contraseña:

{reset_url}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, puedes ignorar este mensaje.

Sistema WASION"""
                
                if send_email('Restablecer Contraseña - WASION', user.email, body):
                    flash('Se han enviado instrucciones para restablecer tu contraseña a tu correo electrónico.', 'info')
                else:
                    flash('Error al enviar el correo. Por favor contacta al administrador.', 'danger')
                return redirect(url_for('login'))
                
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error al generar token: {e}")
                flash('Error al procesar la solicitud', 'danger')
                return redirect(url_for('login'))
        else:
            # Seguridad en el correo
            flash('Si el correo existe, recibirás instrucciones para restablecer tu contraseña', 'info')
            return redirect(url_for('login'))
    return render_template('olvide_contraseña.html', form=form)



@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    app.logger.info(f"Intentando reset con token: {token}")
    
    # Buscar usuario con el token
    user = db.session.query(User).filter_by(reset_token=token).first()
    
    if not user:
        app.logger.error(f"Token no encontrado: {token}")
        flash('El enlace de restablecimiento es inválido o ha expirado', 'danger')
        return redirect(url_for('olvide_contrasena'))
    
    current_time = datetime.now(timezone.utc)
    
    # Si el token_expiry es naive, convertirlo a aware
    if user.reset_token_expiry:
        if user.reset_token_expiry.tzinfo is None:
            token_expiry_aware = user.reset_token_expiry.replace(tzinfo=timezone.utc)
        else:
            token_expiry_aware = user.reset_token_expiry
            
        app.logger.info(f"Token expira: {token_expiry_aware}, Hora actual: {current_time}")
        
        if token_expiry_aware < current_time:
            app.logger.error(f"Token expirado: {token}")
            flash('El enlace de restablecimiento ha expirado', 'danger')
            return redirect(url_for('olvide_contrasena'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        try:
            user.set_password(form.password.data)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            app.logger.info(f"Contraseña actualizada para usuario: {user.username}")
            
            # TEXTOS DE CORREO DE CONFIRMACIÓN
            body = f"""Hola {user.username},

Tu contraseña ha sido restablecida exitosamente.

Si no realizaste este cambio, por favor contacta al administrador inmediatamente.

Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
            
            if send_email('Contraseña Restablecida - WASION', user.email, body):
                flash('Tu contraseña ha sido actualizada exitosamente. Se ha enviado un correo de confirmación.', 'success')
            else:
                flash('Tu contraseña ha sido actualizada exitosamente, pero hubo un error al enviar el correo de confirmación.', 'warning')
            
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error al actualizar contraseña: {e}")
            flash('Error al actualizar la contraseña', 'danger')
            return redirect(url_for('login'))
    
    return render_template('restablecer.html', form=form)

# REGISTRO DE USUARIOS

@app.route('/register', methods=['GET', 'POST'])
def usuario_form():
    """Registro público - crea usuarios con rol 'user'"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        # Usar db.session.query()
        if db.session.query(User).filter(or_(User.username == form.username.data, User.email == form.email.data)).first():
            flash('El username o el email ya están en uso', 'danger')
            return render_template('usuario_form.html', form=form, action='Registrarse')      
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            role='user'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        try:
            db.session.commit()
            
            # TEXTOS DE CORREO DE BIENVENIDA
            body = f"""¡Bienvenido al Sistema de Salas de Reuniones WASION!

Hola {user.username},

Tu cuenta ha sido creada exitosamente.

Detalles de tu cuenta:
- Usuario: {user.username}
- Email: {user.email}
- Rol: Usuario
- Fecha de registro: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Ya puedes iniciar sesión en el sistema para reservar salas de reuniones.

Saludos,
Sistema WASION"""
            
            if send_email('Cuenta Creada - WASION', user.email, body):
                flash('¡Registro exitoso! Revisa tu correo. Ahora puedes iniciar sesión.', 'success')
            else:
                flash('¡Registro exitoso! Pero hubo un error al enviar el correo de confirmación. Ahora puedes iniciar sesión.', 'warning')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error al registrar usuario (posible duplicado)', 'danger')
    
    return render_template('usuario_form.html', form=form, action='Registrarse')


# CODIGO GESTIÓN DE USUARIOS (SUPERADMIN) 

@app.route('/users')
@superadmin_required
def users():
    # Usar db.session.query()
    return render_template('usuarios.html', users=db.session.query(User).all())

@app.route('/users/add', methods=['GET', 'POST'])
@superadmin_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        # Usar db.session.query()
        if db.session.query(User).filter(or_(User.username == form.username.data, User.email == form.email.data)).first():
            flash('El username o el email ya están en uso', 'danger')
            return render_template('usuario_form.html', form=form, action='Crear')
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            
            # TEXTO PARA CORREO DE NUEVO USUARIO
            body_user = f"""¡Bienvenido al Sistema de Salas de Reuniones WASION!

Hola {user.username},

Tu cuenta ha sido creada por un administrador.

Detalles de tu cuenta:
- Usuario: {user.username}
- Email: {user.email}
- Rol: {user.role}
- Fecha de creación: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Ya puedes iniciar sesión en el sistema.

Saludos,
Sistema WASION"""
            
            email_sent_user = send_email('Cuenta Creada - WASION', user.email, body_user)
            
            # TEXTO PARA CORREO AL SUPERADMIN QUE CREÓ EL USUARIO
            admin_body = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has creado exitosamente un nuevo usuario en el sistema.

Detalles del usuario creado:
- Usuario: {user.username}
- Email: {user.email}
- Rol: {user.role}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
            
            email_sent_admin = send_email('Usuario Creado - WASION', current_user.email, admin_body)
            
            if email_sent_user and email_sent_admin:
                flash('Usuario creado exitosamente. Se han enviado correos de confirmación.', 'success')
            elif email_sent_user or email_sent_admin:
                flash('Usuario creado exitosamente, pero hubo un error al enviar algunos correos.', 'warning')
            else:
                flash('Usuario creado exitosamente, pero hubo un error al enviar los correos.', 'warning')
            return redirect(url_for('users'))
        except IntegrityError:
            db.session.rollback()
            flash('Error al crear usuario', 'danger')
    return render_template('usuario_form.html', form=form, action='Crear')

@app.route('/users/delete/<int:id>', methods=['POST'])
@superadmin_required
def delete_user(id):
    if id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('users'))
    
    # Usar db.session.get()
    user = db.session.get(User, id)
    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('users'))
    
    user_email = user.email
    user_name = user.username
    user_role = user.role
    
    db.session.delete(user)
    db.session.commit()
    
    # TEXTO DE CORREO AL SUPERADMIN QUE ELIMINÓ ALGUNA ACCION DENTRO DEL SISTEMA
    body = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has eliminado un usuario del sistema.

Usuario eliminado:
- Usuario: {user_name}
- Email: {user_email}
- Rol: {user_role}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
    
    if send_email('Usuario Eliminado - WASION', current_user.email, body):
        flash('Usuario eliminado exitosamente. Se ha enviado correo de confirmación.', 'success')
    else:
        flash('Usuario eliminado exitosamente, pero hubo un error al enviar el correo de confirmación.', 'warning')
    return redirect(url_for('users'))


# SECCION DE CODIGO PARA GESTIÓN DE SALAS (ADMINISTRADOR Y SUPERADMIN)

@app.route('/rooms')
@admin_required
@no_cache
def rooms():
    plant_id = request.args.get('plant', type=int)
    if plant_id:
        # Usar db.session.query()
        all_rooms = db.session.query(Room).filter_by(plant_id=plant_id).order_by(Room.name).all()
    else:
        all_rooms = db.session.query(Room).order_by(Room.name).all()
    plants = db.session.query(Plant).order_by(Plant.name).all()
    return render_template('salas.html', rooms=all_rooms, plants=plants, selected_plant=plant_id)

@app.route('/rooms/add', methods=['GET', 'POST'])
@admin_required
def add_room():
    form = RoomForm()
    # Usar db.session.query()
    plants = db.session.query(Plant).order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]
    if form.validate_on_submit():
        if db.session.query(Room).filter_by(name=form.name.data).first():
            flash('Ya existe una sala con ese nombre', 'danger')
            return render_template('sala_form.html', form=form, action='Crear')
        
        room = Room(
            name=form.name.data,
            description=form.description.data,
            capacity=form.capacity.data,
            created_by=current_user.id,
            plant_id=form.plant_id.data
        )
        db.session.add(room)
        db.session.commit()
        
        # TEXTO DE CORREO AL ADMINISTRADOR QUE CREÓ LA SALA
        plant = db.session.get(Plant, form.plant_id.data)
        body = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has creado exitosamente una nueva sala de reuniones.

Detalles de la sala:
- Nombre: {room.name}
- Planta: {plant.name if plant else 'N/A'}
- Capacidad: {room.capacity} personas
- Descripción: {room.description or 'N/A'}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
        
        if send_email('Sala Creada - WASION', current_user.email, body):
            flash('Sala creada exitosamente. Se ha enviado correo de confirmación.', 'success')
        else:
            flash('Sala creada exitosamente, pero hubo un error al enviar el correo de confirmación.', 'warning')
        return redirect(url_for('rooms', plant=form.plant_id.data))
    return render_template('sala_form.html', form=form, action='Crear')

@app.route('/rooms/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_room(id):
    # Usar db.session.get()
    room = db.session.get(Room, id)
    if not room:
        flash('Sala no encontrada', 'danger')
        return redirect(url_for('rooms'))
    
    form = RoomForm(obj=room)
    plants = db.session.query(Plant).order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]
    if form.validate_on_submit():
        existing = db.session.query(Room).filter(Room.name == form.name.data, Room.id != id).first()
        if existing:
            flash('Ya existe una sala con ese nombre', 'danger')
            return render_template('sala_form.html', form=form, action='Editar', room=room)
        
        old_name = room.name
        room.name = form.name.data
        room.description = form.description.data
        room.capacity = form.capacity.data
        room.plant_id = form.plant_id.data
        db.session.commit()
        
        # TEXTO DE CORREO AL ADMINISTRADOR QUE EDITÓ LA SALA
        plant = db.session.get(Plant, form.plant_id.data)
        body = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has actualizado exitosamente una sala de reuniones.

Sala anterior: {old_name}

Detalles actualizados:
- Nombre: {room.name}
- Planta: {plant.name if plant else 'N/A'}
- Capacidad: {room.capacity} personas
- Descripción: {room.description or 'N/A'}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
        
        if send_email('Sala Actualizada - WASION', current_user.email, body):
            flash('Sala actualizada exitosamente. Se ha enviado correo de confirmación.', 'success')
        else:
            flash('Sala actualizada exitosamente, pero hubo un error al enviar el correo de confirmación.', 'warning')
        return redirect(url_for('rooms', plant=room.plant_id))
    return render_template('sala_form.html', form=form, action='Editar', room=room)

@app.route('/rooms/delete/<int:id>', methods=['POST'])
@admin_required
def delete_room(id):
    # Usar db.session.get()
    room = db.session.get(Room, id)
    if not room:
        flash('Sala no encontrada', 'danger')
        return redirect(url_for('rooms'))
    
    room_name = room.name
    plant_name = room.plant.name if room.plant else 'N/A'
    plant_id = room.plant_id
    
    if room.meetings:
        flash('No se puede eliminar la sala porque tiene reuniones asociadas', 'danger')
    else:
        db.session.delete(room)
        db.session.commit()
        
        # TEXTO DE CORREO AL ADMIN QUE ELIMINÓ LA SALA
        body = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has eliminado una sala de reuniones del sistema.

Sala eliminada:
- Nombre: {room_name}
- Planta: {plant_name}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
        
        if send_email('Sala Eliminada - WASION', current_user.email, body):
            flash('Sala eliminada exitosamente. Se ha enviado correo de confirmación.', 'success')
        else:
            flash('Sala eliminada exitosamente, pero hubo un error al enviar el correo de confirmación.', 'warning')
    return redirect(url_for('rooms', plant=plant_id))


# SECCION DE CODIGO PARA LA GESTIÓN DE REUNIONES
#################################################
@app.route('/')
@login_required
@no_cache

def index():
    plant_id = request.args.get('plant', type=int)
    sala_id = request.args.get('sala', type=int)        
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    mine = request.args.get('mine', default='0')

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        selected_date = datetime.now().date()
        date_str = selected_date.strftime('%Y-%m-%d')

    
    query = db.session.query(MeetingRoom).join(Room, isouter=True).filter(MeetingRoom.date == selected_date)

    # Filtrar por planta (si aplica)
    if plant_id:
        query = query.filter(Room.plant_id == plant_id)

    if sala_id:
        query = query.filter(MeetingRoom.room_id == sala_id)

    if mine == '1':
        query = query.filter(MeetingRoom.created_by == current_user.id)

    meetings = query.order_by(MeetingRoom.time_slot).all()

    try:
        plants = db.session.query(Plant).order_by(Plant.name).all()
    except Exception:
        plants = []

    try:
        if plant_id:
            salas = db.session.query(Room).filter(Room.plant_id == plant_id).order_by(Room.name).all()
        else:
            salas = db.session.query(Room).order_by(Room.name).all()
    except Exception:
        salas = []

    return render_template('room.html',
                           meetings=meetings,
                           selected_date=date_str,
                           plants=plants,
                           salas=salas,                      
                           selected_plant=plant_id,
                           selected_sala=sala_id,
                           today=date.today().strftime('%Y-%m-%d'),
                           mine=(mine == '1'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_meeting():
    form = MeetingRoomForm()
    plants = db.session.query(Plant).order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]

    selected_plant = None
    if request.method == 'POST' and form.plant_id.data:
        selected_plant = form.plant_id.data
    else:
        selected_plant = request.args.get('plant', type=int) or (plants[0].id if plants else None)

    if selected_plant:
        rooms = db.session.query(Room).filter_by(plant_id=selected_plant).order_by(Room.name).all()
    else:
        rooms = db.session.query(Room).order_by(Room.name).all()
    form.room_id.choices = [(r.id, f"{r.name} (Cap: {r.capacity})") for r in rooms]

    if not form.room_id.choices:
        flash('No hay salas disponibles para la planta seleccionada. Un administrador debe crear salas primero.', 'warning')
        return redirect(url_for('index', plant=selected_plant))

    if form.validate_on_submit():
        if form.date.data < date.today():
            flash('No se pueden agendar reuniones en fechas pasadas', 'danger')
            return render_template('formulario.html', 
                                 form=form, 
                                 action='Agregar',
                                 today=date.today().strftime('%Y-%m-%d'))
        if db.session.query(MeetingRoom).filter_by(
            date=form.date.data, 
            time_slot=form.time_slot.data,
            room_id=form.room_id.data
        ).first():
            flash('Ya existe una reunión reservada en ese horario y sala', 'danger')
            return render_template('formulario.html', 
                                 form=form, 
                                 action='Agregar',
                                 today=date.today().strftime('%Y-%m-%d'))
        
        meeting = MeetingRoom(
            room_id=form.room_id.data,
            time_slot=form.time_slot.data, 
            leader=form.leader.data,
            leader_email=form.leader_email.data, 
            subject=form.subject.data,
            remarks=form.remarks.data, 
            date=form.date.data, 
            created_by=current_user.id
        )
        db.session.add(meeting)
        db.session.commit()
        
        room = db.session.get(Room, form.room_id.data)
        
        # ENVIO DE CORREO AL LÍDER QUE ASIGNO PROXIMA REUNION
        body_leader = f"""Hola {meeting.leader},

Tu reservación de sala de reuniones ha sido confirmada exitosamente.

Detalles de la Reunión:
- Sala: {room.name if room else 'N/A'}
- Planta: {room.plant.name if room and room.plant else 'N/A'}
- Fecha: {meeting.date.strftime('%d/%m/%Y')}
- Horario: {meeting.time_slot}
- Asunto: {meeting.subject}
- Observaciones: {meeting.remarks or 'N/A'}

Reservado por: {current_user.username}

Saludos,
Sistema de Salas WASION"""
        
        email_sent_leader = send_email('Confirmación de Reservación - WASION', meeting.leader_email, body_leader)
        
        # ENVIO DE CORREO AL USUARIO QUE RESERVÓ 
        email_sent_user = True
        if current_user.email != meeting.leader_email:
            body_user = f"""Hola {current_user.username},

Has reservado exitosamente una sala de reuniones.

Detalles de la Reunión:
- Sala: {room.name if room else 'N/A'}
- Planta: {room.plant.name if room and room.plant else 'N/A'}
- Fecha: {meeting.date.strftime('%d/%m/%Y')}
- Horario: {meeting.time_slot}
- Líder: {meeting.leader}
- Email líder: {meeting.leader_email}
- Asunto: {meeting.subject}
- Observaciones: {meeting.remarks or 'N/A'}

Saludos,
Sistema de Salas WASION"""
            
            email_sent_user = send_email('Reservación Creada - WASION', current_user.email, body_user)
        
        if email_sent_leader and email_sent_user:
            flash('Reunión agregada exitosamente. Se han enviado correos de confirmación.', 'success')
        elif email_sent_leader or email_sent_user:
            flash('Reunión agregada exitosamente, pero hubo un error al enviar algunos correos.', 'warning')
        else:
            flash('Reunión agregada exitosamente, pero hubo un error al enviar los correos.', 'warning')
        return redirect(url_for('index', date=form.date.data.strftime('%Y-%m-%d'), plant=selected_plant))
    
    if not form.date.data:
        form.date.data = date.today()

    if request.args.get('plant', type=int) and not form.plant_id.data:
        form.plant_id.data = request.args.get('plant', type=int)
    
    return render_template('formulario.html', 
                         form=form, 
                         action='Agregar',
                         today=date.today().strftime('%Y-%m-%d'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_meeting(id):
    # Usar db.session.get()
    meeting = db.session.get(MeetingRoom, id)
    if not meeting:
        flash('Reunión no encontrada', 'danger')
        return redirect(url_for('index'))
    
    # Verificar permisos: superadmin o creador de la reunión
    if not (current_user.is_superadmin() or current_user.id == meeting.created_by):
        flash('No tienes permisos para editar esta reunión', 'danger')
        return redirect(url_for('index'))
    
    form = MeetingRoomForm(obj=meeting)
    plants = db.session.query(Plant).order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]

    if meeting.room and meeting.room.plant_id:
        form.plant_id.data = meeting.room.plant_id

    selected_plant = form.plant_id.data or (plants[0].id if plants else None)
    if selected_plant:
        rooms = db.session.query(Room).filter_by(plant_id=selected_plant).order_by(Room.name).all()
    else:
        rooms = db.session.query(Room).order_by(Room.name).all()
    form.room_id.choices = [(r.id, f"{r.name} (Cap: {r.capacity})") for r in rooms]

    if form.validate_on_submit():
        if form.date.data < date.today():
            flash('No se pueden agendar reuniones en fechas pasadas', 'danger')
            return render_template('formulario.html', 
                                 form=form, 
                                 action='Editar', 
                                 meeting=meeting,
                                 today=date.today().strftime('%Y-%m-%d'))
        
        if db.session.query(MeetingRoom).filter(
            MeetingRoom.date == form.date.data,
            MeetingRoom.time_slot == form.time_slot.data,
            MeetingRoom.room_id == form.room_id.data,
            MeetingRoom.id != id
        ).first():
            flash('Ya existe una reunión reservada en ese horario y sala', 'danger')
            return render_template('formulario.html', 
                                 form=form, 
                                 action='Editar', 
                                 meeting=meeting,
                                 today=date.today().strftime('%Y-%m-%d'))
        
        old_date = meeting.date.strftime('%d/%m/%Y')
        old_time = meeting.time_slot
        old_room = meeting.room.name if meeting.room else 'N/A'
        
        meeting.room_id = form.room_id.data
        meeting.time_slot = form.time_slot.data
        meeting.leader = form.leader.data
        meeting.leader_email = form.leader_email.data
        meeting.subject = form.subject.data
        meeting.remarks = form.remarks.data
        meeting.date = form.date.data
        db.session.commit()
        
        room = db.session.get(Room, form.room_id.data)
        
        # ENVIO DE CORREO AL LÍDER DE LA REUNIÓN
        body_leader = f"""Hola {meeting.leader},

Tu reservación de sala de reuniones ha sido ACTUALIZADA.

Datos anteriores:
- Sala: {old_room}
- Fecha: {old_date}
- Horario: {old_time}

Nuevos detalles de la Reunión:
- Sala: {room.name if room else 'N/A'}
- Planta: {room.plant.name if room and room.plant else 'N/A'}
- Fecha: {meeting.date.strftime('%d/%m/%Y')}
- Horario: {meeting.time_slot}
- Asunto: {meeting.subject}
- Observaciones: {meeting.remarks or 'N/A'}

Actualizado por: {current_user.username}
Fecha de actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema de Salas WASION"""
        
        email_sent_leader = send_email('Reservación Actualizada - WASION', meeting.leader_email, body_leader)
        
        # ENVIO DE CORREO AL USUARIO QUE EDITÓ (si no es el líder)
        email_sent_user = True
        if current_user.email != meeting.leader_email:
            body_user = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has actualizado exitosamente una reunión.

Datos anteriores:
- Sala: {old_room}
- Fecha: {old_date}
- Horario: {old_time}

Nuevos datos:
- Sala: {room.name if room else 'N/A'}
- Planta: {room.plant.name if room and room.plant else 'N/A'}
- Fecha: {meeting.date.strftime('%d/%m/%Y')}
- Horario: {meeting.time_slot}
- Líder: {meeting.leader}
- Email líder: {meeting.leader_email}
- Asunto: {meeting.subject}
- Observaciones: {meeting.remarks or 'N/A'}

Fecha de actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
            
            email_sent_user = send_email('Reunión Actualizada - WASION', current_user.email, body_user)
        
        if email_sent_leader and email_sent_user:
            flash('Reunión actualizada exitosamente. Se han enviado correos de confirmación.', 'success')
        elif email_sent_leader or email_sent_user:
            flash('Reunión actualizada exitosamente, pero hubo un error al enviar algunos correos.', 'warning')
        else:
            flash('Reunión actualizada exitosamente, pero hubo un error al enviar los correos.', 'warning')
        return redirect(url_for('index', date=meeting.date.strftime('%Y-%m-%d'), plant=selected_plant))
    
    return render_template('formulario.html', 
                         form=form, 
                         action='Editar', 
                         meeting=meeting,
                         today=date.today().strftime('%Y-%m-%d'))

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_meeting(id):
    # Usar db.session.get()
    meeting = db.session.get(MeetingRoom, id)
    if not meeting:
        flash('Reunión no encontrada', 'danger')
        return redirect(url_for('index'))
    
    # Verificar permisos: superadmin o creador de la reunión
    if not (current_user.is_superadmin() or current_user.id == meeting.created_by):
        flash('No tienes permisos para eliminar esta reunión', 'danger')
        return redirect(url_for('index'))
    
    date_str = meeting.date.strftime('%Y-%m-%d')
    plant_id = None
    if meeting.room:
        plant_id = meeting.room.plant_id
    
    # Guardar datos antes de eliminar
    meeting_info = {
        'room': meeting.room.name if meeting.room else 'N/A',
        'plant': meeting.room.plant.name if meeting.room and meeting.room.plant else 'N/A',
        'date': meeting.date.strftime('%d/%m/%Y'),
        'time': meeting.time_slot,
        'leader': meeting.leader,
        'leader_email': meeting.leader_email,
        'subject': meeting.subject,
        'remarks': meeting.remarks or 'N/A'
    }
    
    db.session.delete(meeting)
    db.session.commit()
    
    # ENVIO DE CORREO AL LÍDER DE LA REUNIÓN SOBRE LA ACCION
    body_leader = f"""Hola {meeting_info['leader']},

Tu reservación de sala de reuniones ha sido CANCELADA.

Detalles de la reunión cancelada:
- Sala: {meeting_info['room']}
- Planta: {meeting_info['plant']}
- Fecha: {meeting_info['date']}
- Horario: {meeting_info['time']}
- Asunto: {meeting_info['subject']}

Cancelado por: {current_user.username}
Fecha de cancelación: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Si tienes dudas, contacta al administrador.

Saludos,
Sistema de Salas WASION"""
    
    email_sent_leader = send_email('Reservación Cancelada - WASION', meeting_info['leader_email'], body_leader)

    # ENVIO DE CORREO AL USUARIO QUE ELIMINÓ (si no es el líder)
    email_sent_user = True
    if current_user.email != meeting_info['leader_email']:
        body_user = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has eliminado una reunión del sistema.

Detalles de la reunión eliminada:
- Sala: {meeting_info['room']}
- Planta: {meeting_info['plant']}
- Fecha: {meeting_info['date']}
- Horario: {meeting_info['time']}
- Líder: {meeting_info['leader']}
- Email líder: {meeting_info['leader_email']}
- Asunto: {meeting_info['subject']}
- Observaciones: {meeting_info['remarks']}

Fecha de eliminación: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
        
        email_sent_user = send_email('Reunión Eliminada - WASION', current_user.email, body_user)
    
    if email_sent_leader and email_sent_user:
        flash('Reunión eliminada exitosamente. Se han enviado correos de confirmación.', 'success')
    elif email_sent_leader or email_sent_user:
        flash('Reunión eliminada exitosamente, pero hubo un error al enviar algunos correos.', 'warning')
    else:
        flash('Reunión eliminada exitosamente, pero hubo un error al enviar los correos.', 'warning')
    return redirect(url_for('index', date=date_str, plant=plant_id))


# SECCION DE CODIGO PARA LA GESTIÓN DE PLANTAS PARA EL SUPERADMIN
@app.route('/plants')
@superadmin_required
def plants():
    all_plants = db.session.query(Plant).order_by(Plant.name).all()
    return render_template('plants.html', plants=all_plants)

@app.route('/plants/add', methods=['GET', 'POST'])
@superadmin_required
def add_plant():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if not name:
            flash('El nombre de la planta es requerido', 'danger')
            return redirect(url_for('plants'))
        if db.session.query(Plant).filter_by(name=name).first():
            flash('Ya existe una planta con ese nombre', 'danger')
            return redirect(url_for('plants'))
        p = Plant(name=name, description=description, created_by=current_user.id)
        db.session.add(p)
        db.session.commit()
        
        # ENVIO DE CORREO AL SUPERADMIN
        body = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has creado exitosamente una nueva planta en el sistema.

Detalles de la planta:
- Nombre: {p.name}
- Descripción: {p.description or 'N/A'}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
        
        if send_email('Planta Creada - WASION', current_user.email, body):
            flash('Planta creada. Se ha enviado correo de confirmación.', 'success')
        else:
            flash('Planta creada, pero hubo un error al enviar el correo de confirmación.', 'warning')
        return redirect(url_for('plants'))
    return render_template('plant_form.html')

@app.route('/plants/delete/<int:id>', methods=['POST'])
@superadmin_required
def delete_plant(id):
    # Usar db.session.get()
    plant = db.session.get(Plant, id)
    if not plant:
        flash('Planta no encontrada', 'danger')
        return redirect(url_for('plants'))
    
    plant_name = plant.name
    plant_desc = plant.description or 'N/A'
    
    if plant.rooms:
        flash('No se puede eliminar la planta porque tiene salas asociadas', 'danger')
        return redirect(url_for('plants'))
    
    db.session.delete(plant)
    db.session.commit()
    
    # ENVIO DE CORREO AL SUPERADMIN SOBRE LA ACCION
    body = f"""Confirmación de Acción - WASION

Hola {current_user.username},

Has eliminado una planta del sistema.

Planta eliminada:
- Nombre: {plant_name}
- Descripción: {plant_desc}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema WASION"""
    
    if send_email('Planta Eliminada - WASION', current_user.email, body):
        flash('Planta eliminada. Se ha enviado correo de confirmación.', 'success')
    else:
        flash('Planta eliminada, pero hubo un error al enviar el correo de confirmación.', 'warning')
    return redirect(url_for('plants'))

if __name__ == '__main__':
    app.run(debug=True)
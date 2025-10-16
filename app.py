from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from config import DevelopmentConfig
from models import db, MeetingRoom, User, Room, Plant
from forms import MeetingRoomForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, UserForm, RoomForm
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

# Inicialización y creación de tablas / datos por defecto
with app.app_context():
    db.create_all()

    # Crear superadmin si no existe
    existing = User.query.filter(
        or_(User.username == 'superadmin', User.email == 'juangaytangg332@gmail.com')
    ).first()
    if not existing:
        admin = User(username='superadmin', email='juangaytangg332@gmail.com', role='superadmin')
        admin.set_password('admin123')
        db.session.add(admin)
        try:
            db.session.commit()
            app.logger.info("Super Admin creado: usuario='superadmin', contraseña='admin123'")
            existing = admin
        except IntegrityError:
            db.session.rollback()
            existing = User.query.filter_by(username='superadmin').first()


######################################################################################################################################
    # Crear plantas 1 al 7 
    for i in range(1, 8):
        name = f"Planta {i}"
        if not Plant.query.filter_by(name=name).first():
            p = Plant(name=name, description=f"Planta {i}", created_by=(existing.id if existing else None))
            db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


#############################################################################################################33333

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
        return redirect(url_for('login'))
    return render_template('olvide_contraseña.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or (user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow()):
        flash('El enlace de restablecimiento es inválido o ha expirado', 'danger')
        return redirect(url_for('olvide_contrasena'))
    
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

@app.route('/register', methods=['GET', 'POST'])
def usuario_form():
    """Registro público - crea usuarios con rol 'user'"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        if User.query.filter(or_(User.username == form.username.data, User.email == form.email.data)).first():
            flash('El username o el email ya están en uso', 'danger')
            return render_template('usuario_form.html', form=form, action='Registrarse')
        
        # Siempre crea como 'user' al reigstrarse en login
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            role='user'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        try:
            db.session.commit()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error al registrar usuario (posible duplicado)', 'danger')
    
    return render_template('usuario_form.html', form=form, action='Registrarse')

# ############################# Gestion de usuarios por super admin 

@app.route('/users')
@superadmin_required
def users():
    return render_template('usuarios.html', users=User.query.all())

@app.route('/users/add', methods=['GET', 'POST'])
@superadmin_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter(or_(User.username == form.username.data, User.email == form.email.data)).first():
            flash('El username o el email ya están en uso', 'danger')
            return render_template('usuario_form.html', form=form, action='Crear')
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Usuario creado exitosamente', 'success')
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
    
    db.session.delete(User.query.get_or_404(id))
    db.session.commit()
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('users'))

# ############################# Gestion de salas por admin y superadmin

@app.route('/rooms')
@admin_required
def rooms():
    plant_id = request.args.get('plant', type=int)
    if plant_id:
        all_rooms = Room.query.filter_by(plant_id=plant_id).order_by(Room.name).all()
    else:
        all_rooms = Room.query.order_by(Room.name).all()
    plants = Plant.query.order_by(Plant.name).all()
    return render_template('salas.html', rooms=all_rooms, plants=plants, selected_plant=plant_id)

@app.route('/rooms/add', methods=['GET', 'POST'])
@admin_required
def add_room():
    form = RoomForm()
    plants = Plant.query.order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]
    if form.validate_on_submit():
        if Room.query.filter_by(name=form.name.data).first():
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
        flash('Sala creada exitosamente', 'success')
        return redirect(url_for('rooms', plant=form.plant_id.data))
    return render_template('sala_form.html', form=form, action='Crear')

@app.route('/rooms/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_room(id):
    room = Room.query.get_or_404(id)
    form = RoomForm(obj=room)
    plants = Plant.query.order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]
    if form.validate_on_submit():
        existing = Room.query.filter(Room.name == form.name.data, Room.id != id).first()
        if existing:
            flash('Ya existe una sala con ese nombre', 'danger')
            return render_template('sala_form.html', form=form, action='Editar', room=room)
        
        room.name = form.name.data
        room.description = form.description.data
        room.capacity = form.capacity.data
        room.plant_id = form.plant_id.data
        db.session.commit()
        flash('Sala actualizada exitosamente', 'success')
        return redirect(url_for('rooms', plant=room.plant_id))
    return render_template('sala_form.html', form=form, action='Editar', room=room)

@app.route('/rooms/delete/<int:id>', methods=['POST'])
@admin_required
def delete_room(id):
    room = Room.query.get_or_404(id)
    # Verificar si hay reuniones ya ocupadas en esa sala
    if room.meetings:
        flash('No se puede eliminar la sala porque tiene reuniones asociadas', 'danger')
    else:
        db.session.delete(room)
        db.session.commit()
        flash('Sala eliminada exitosamente', 'success')
    return redirect(url_for('rooms', plant=room.plant_id if room else None))

# ############################# Gestion de reuniones por todos los usuarios

@app.route('/')
@login_required
def index():
    ########### obtener planta en general
    plant_id = request.args.get('plant', type=int)
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        date = datetime.now().date()
        date_str = date.strftime('%Y-%m-%d')

    ################ Si hay planta seleccionada, filtrar solo por salas de esa planta
    if plant_id:
        meetings = MeetingRoom.query.join(Room).filter(
            MeetingRoom.date == date,
            Room.plant_id == plant_id
        ).order_by(MeetingRoom.time_slot).all()
    else:
        meetings = MeetingRoom.query.filter_by(date=date).order_by(MeetingRoom.time_slot).all()

    ################# Traer todas las plantas para seleccionar alguna de ellas y agendar
    try:
        plants = Plant.query.order_by(Plant.name).all()
    except Exception:
        plants = []

    return render_template('room.html', meetings=meetings, selected_date=date_str, plants=plants, selected_plant=plant_id)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_meeting():
    form = MeetingRoomForm()
    ######## cargar plantas
    plants = Plant.query.order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]

    ######### determinar planta seleccionada
    selected_plant = None
    if request.method == 'POST' and form.plant_id.data:
        selected_plant = form.plant_id.data
    else:
        selected_plant = request.args.get('plant', type=int) or (plants[0].id if plants else None)

    ########## cargar opciones de salas filtradas por planta
    if selected_plant:
        rooms = Room.query.filter_by(plant_id=selected_plant).order_by(Room.name).all()
    else:
        rooms = Room.query.order_by(Room.name).all()
    form.room_id.choices = [(r.id, f"{r.name} (Cap: {r.capacity})") for r in rooms]

    if not form.room_id.choices:
        flash('No hay salas disponibles para la planta seleccionada. Un administrador debe crear salas primero.', 'warning')
        return redirect(url_for('index', plant=selected_plant))

    if form.validate_on_submit():
        ###### saber si esta disponile el horario para agendar sala
        if MeetingRoom.query.filter_by(
            date=form.date.data, 
            time_slot=form.time_slot.data,
            room_id=form.room_id.data
        ).first():
            flash('Ya existe una reunión reservada en ese horario y sala', 'danger')
            return render_template('formulario.html', form=form, action='Agregar')
        
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
        
        room = Room.query.get(form.room_id.data)
        body = f"""Hola {meeting.leader},

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
        
        send_email('Confirmación de Reservación - WASION', meeting.leader_email, body)
        flash('Reunión agregada exitosamente. Se ha enviado un correo de confirmación.', 'success')
        return redirect(url_for('index', date=form.date.data.strftime('%Y-%m-%d'), plant=selected_plant))
    
    form.date.data = datetime.now().date()

    if request.args.get('plant', type=int) and not form.plant_id.data:
        form.plant_id.data = request.args.get('plant', type=int)
    return render_template('formulario.html', form=form, action='Agregar')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@superadmin_required
def edit_meeting(id):
    meeting = MeetingRoom.query.get_or_404(id)
    form = MeetingRoomForm(obj=meeting)
    plants = Plant.query.order_by(Plant.name).all()
    form.plant_id.choices = [(p.id, p.name) for p in plants]

    # establecer plant_id según la sala del meeting
    if meeting.room and meeting.room.plant_id:
        form.plant_id.data = meeting.room.plant_id

    # cargar salas de la planta seleccionada
    selected_plant = form.plant_id.data or (plants[0].id if plants else None)
    if selected_plant:
        rooms = Room.query.filter_by(plant_id=selected_plant).order_by(Room.name).all()
    else:
        rooms = Room.query.order_by(Room.name).all()
    form.room_id.choices = [(r.id, f"{r.name} (Cap: {r.capacity})") for r in rooms]

    if form.validate_on_submit():
        if MeetingRoom.query.filter(
            MeetingRoom.date == form.date.data,
            MeetingRoom.time_slot == form.time_slot.data,
            MeetingRoom.room_id == form.room_id.data,
            MeetingRoom.id != id
        ).first():
            flash('Ya existe una reunión reservada en ese horario y sala', 'danger')
            return render_template('formulario.html', form=form, action='Editar', meeting=meeting)
        
        meeting.room_id = form.room_id.data
        meeting.time_slot = form.time_slot.data
        meeting.leader = form.leader.data
        meeting.leader_email = form.leader_email.data
        meeting.subject = form.subject.data
        meeting.remarks = form.remarks.data
        meeting.date = form.date.data
        db.session.commit()
        flash('Reunión actualizada exitosamente', 'success')
        return redirect(url_for('index', date=meeting.date.strftime('%Y-%m-%d'), plant=selected_plant))
    
    return render_template('formulario.html', form=form, action='Editar', meeting=meeting)

@app.route('/delete/<int:id>', methods=['POST'])
@superadmin_required
def delete_meeting(id):
    meeting = MeetingRoom.query.get_or_404(id)
    date = meeting.date.strftime('%Y-%m-%d')
    plant_id = None
    if meeting.room:
        plant_id = meeting.room.plant_id
    db.session.delete(meeting)
    db.session.commit()
    flash('Reunión eliminada exitosamente', 'success')
    return redirect(url_for('index', date=date, plant=plant_id))

# ############################# Gestion de plantas por superadmin

@app.route('/plants')
@superadmin_required
def plants():
    all_plants = Plant.query.order_by(Plant.name).all()
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
        if Plant.query.filter_by(name=name).first():
            flash('Ya existe una planta con ese nombre', 'danger')
            return redirect(url_for('plants'))
        p = Plant(name=name, description=description, created_by=current_user.id)
        db.session.add(p)
        db.session.commit()
        flash('Planta creada', 'success')
        return redirect(url_for('plants'))
    return render_template('plant_form.html')

@app.route('/plants/delete/<int:id>', methods=['POST'])
@superadmin_required
def delete_plant(id):
    plant = Plant.query.get_or_404(id)
    if plant.rooms:
        flash('No se puede eliminar la planta porque tiene salas asociadas', 'danger')
        return redirect(url_for('plants'))
    db.session.delete(plant)
    db.session.commit()
    flash('Planta eliminada', 'success')
    return redirect(url_for('plants'))

if __name__ == '__main__':
    app.run(debug=True)

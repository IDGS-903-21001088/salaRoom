from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import Config
from models import db, MeetingRoom
from forms import MeetingRoomForm
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    meetings = MeetingRoom.query.filter_by(date=datetime.strptime(date, '%Y-%m-%d').date()).order_by(MeetingRoom.time_slot).all()
    return render_template('room.html', meetings=meetings, selected_date=date)

@app.route('/add', methods=['GET', 'POST'])
def add_meeting():
    form = MeetingRoomForm()
    if form.validate_on_submit():
        meeting = MeetingRoom(
            time_slot=form.time_slot.data,
            leader=form.leader.data,
            subject=form.subject.data,
            remarks=form.remarks.data,
            date=form.date.data
        )
        db.session.add(meeting)
        db.session.commit()
        flash('Reunión agregada exitosamente', 'success')
        return redirect(url_for('index', date=form.date.data.strftime('%Y-%m-%d')))
    
    form.date.data = datetime.now().date()
    return render_template('add_edit.html', form=form, action='Agregar')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_meeting(id):
    meeting = MeetingRoom.query.get_or_404(id)
    form = MeetingRoomForm(obj=meeting)
    
    if form.validate_on_submit():
        meeting.time_slot = form.time_slot.data
        meeting.leader = form.leader.data
        meeting.subject = form.subject.data
        meeting.remarks = form.remarks.data
        meeting.date = form.date.data
        db.session.commit()
        flash('Reunión actualizada exitosamente', 'success')
        return redirect(url_for('index', date=meeting.date.strftime('%Y-%m-%d')))
    
    return render_template('add_edit.html', form=form, action='Editar', meeting=meeting)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_meeting(id):
    meeting = MeetingRoom.query.get_or_404(id)
    date = meeting.date.strftime('%Y-%m-%d')
    db.session.delete(meeting)
    db.session.commit()
    flash('Reunión eliminada exitosamente', 'success')
    return redirect(url_for('index', date=date))

if __name__ == '__main__':
    app.run(debug=True)
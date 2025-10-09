import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    Usuario = request.form['Usuario']
    Contrasena = request.form['Contrasena']

#logica de autenticacion (nueva sesión)
    return redirect(url_for('room'))

@app.route('/room')
def room():
    return render_template('room.html')

if __name__ == '__main__':
    app.run(debug=True)

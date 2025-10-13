import os
from sqlalchemy import create_engine
import urllib
from datetime import timedelta


       
class Config(object):
    SECRET_KEY = 'Clave-super-secreta-cambiar-en-produccion-2024'
    SESSION_COOKIE_SECRET = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    ENV = 'production'
    PROPAGATE_EXCEPTIONS = False
    
    
    
    # Configuración de correo electrónico
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'juangaytangg332@gmail.com'  # Tu correo real
MAIL_PASSWORD = 'xxxx xxxx xxxx xxxx'  # Contraseña de aplicación de 16 dígitos
MAIL_DEFAULT_SENDER = 'juangaytangg332@gmail.com'
    # Configuración de la aplicación
APP_NAME = 'WASION Meeting Room System'
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:cclab@localhost:3306/salaWasion'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
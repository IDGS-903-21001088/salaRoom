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
    
    # Configuración de correo
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'salaswasion@gmail.com'  # ⚠️ CAMBIA ESTO
    MAIL_PASSWORD = 'jiud wwbt nnwx pgfv'  # ⚠️ CAMBIA ESTO
    MAIL_DEFAULT_SENDER = 'salaswasion@gmail.com'  # ⚠️ CAMBIA ESTO
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False

  
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:cclab@localhost:3306/salaWasion'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de correo para desarrollo (usa la misma de Config)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'salaswasion@gmail.com'  
    MAIL_PASSWORD = 'jiud wwbt nnwx pgfv'  
    MAIL_DEFAULT_SENDER = 'salaswasion@gmail.com'  # ⚠️ CAMBIA ESTO
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
    
  
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:cclab@localhost:3306/salaWasion'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
import os
from sqlalchemy import create_engine
import urllib

       
class Config(object):
    SECRET_KEY = 'Clave nueva'
    SESSION_COOKIE_SECRET = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    ENV = 'production'
    PROPAGATE_EXCEPTIONS = False

    
class DevelopmentConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:cclab@localhost:3306/salaRoom'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
        
 
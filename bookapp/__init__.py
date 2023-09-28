from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail,Message



csrf=CSRFProtect()
mail=Mail()


def create_app():
    """Keep all imports that may casue conflict within this function so that anytime we write from pkg... imports.. none of these satements will be executed"""
    from bookapp.models import db
    app = Flask(__name__,instance_relative_config=True)    
    app.config.from_pyfile("config.py",silent=True)
    db.init_app(app)
    migrate=Migrate(app,db)
    csrf.init_app(app)
    mail.init_app(app)
    return app

app=create_app()

#load the routes here


from bookapp import admin_routes,user_routes

from bookapp.forms import *


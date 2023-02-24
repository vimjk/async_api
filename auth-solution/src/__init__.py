from flask import Flask
from flask_security.utils import hash_password
from src.utils.extensions import user_datastore

from .api.v1 import auth, roles
from .core.config import settings
from .services.database import db
from .utils.extensions import jwt, security


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = settings.SECURITY_TOKEN_AUTHENTICATION_HEADER
    app.config['SECURITY_PASSWORD_SALT'] = settings.SECURITY_PASSWORD_SALT

    app.register_blueprint(auth.bp)
    app.register_blueprint(roles.bp)

    db.init_app(app)

    with app.app_context():
        app.logger.info('initialised database.')
        db.create_all()
        security.init_app(app)
        jwt.init_app(app)

        if not user_datastore.find_role(role='admin'):
            user_datastore.create_role(name='admin')
            user_datastore.commit()
        admin_user = user_datastore.find_user(email=settings.FLASK_ADMIN_MAIL)
        if not admin_user:
            user_datastore.create_user(email=settings.FLASK_ADMIN_MAIL,
                                       password=hash_password(settings.FLASK_ADMIN_PASS),
                                       roles=['admin']
                                       )
            user_datastore.commit()

    return app

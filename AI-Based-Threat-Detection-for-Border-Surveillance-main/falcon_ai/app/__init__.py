from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os
import re

# Determine important paths
package_dir = os.path.dirname(os.path.abspath(__file__))  # falcon_ai/app
falcon_root = os.path.dirname(package_dir)  # falcon_ai
project_root = os.path.dirname(falcon_root)  # repo root
templates_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

from falcon_ai.config import Config

# Initialize extensions
mongo = PyMongo()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
bcrypt = Bcrypt()


def _ensure_db_in_uri(uri, db_name='falcon_ai'):
    """Ensure the MongoDB URI contains a database name."""
    if not uri:
        return uri
    # For mongodb+srv:// or mongodb:// URIs, check if db name is in the path
    # Pattern: ...mongodb.net/  or ...mongodb.net/?  (no db name)
    if re.search(r'mongodb\.net/\?', uri) or uri.rstrip('/').endswith('.net'):
        # Insert db name before the query string
        uri = re.sub(r'(mongodb\.net)/([?])', rf'\1/{db_name}\2', uri)
        if uri.rstrip('/').endswith('.net'):
            uri = uri.rstrip('/') + f'/{db_name}'
    # For localhost URIs without db name
    elif re.search(r':\d+/?$', uri):
        uri = uri.rstrip('/') + f'/{db_name}'
    return uri


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )
    app.config.from_object(config_class)
    
    # Handle reverse proxy (HuggingFace Spaces, Render, etc.)
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Fix MONGO_URI to ensure database name is included
    raw_uri = app.config.get('MONGO_URI', '')
    fixed_uri = _ensure_db_in_uri(raw_uri, 'falcon_ai')
    app.config['MONGO_URI'] = fixed_uri
    print(f'📡 MONGO_URI (sanitized): {fixed_uri[:40]}...' if len(fixed_uri) > 40 else f'📡 MONGO_URI: {fixed_uri}')
    
    # Initialize extensions with app
    mongo.init_app(app)
    
    # Fallback: if Flask-PyMongo failed to set db, do it manually
    if mongo.db is None and mongo.cx is not None:
        mongo.db = mongo.cx['falcon_ai']
        print('⚠️ Flask-PyMongo db was None, manually set to falcon_ai')
    
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize upload folder
    config_class.init_app(app)
    
    # Register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from .analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    from .chatbot import bp as chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')

    from .upload import bp as upload_bp
    app.register_blueprint(upload_bp, url_prefix='/upload')
    
    # User loader for Flask-Login
    from .auth import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)
    
    return app


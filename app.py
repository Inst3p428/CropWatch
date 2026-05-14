from flask import Flask, render_template
from flask_login import LoginManager
from extensions import db, migrate
from models import Farmer, Officer, Admin
from routes.farmer_routes import farmer_bp
from routes.officer_routes import officer_bp
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from config import Config  # Import Config from config.py

def create_app():
    app = Flask(__name__)
    
    # Load configuration from Config class
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user = Farmer.query.get(int(user_id))
        if user:
            return user
        
        user = Officer.query.get(int(user_id))
        if user:
            return user
        
        return Admin.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return render_template('landing.html')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
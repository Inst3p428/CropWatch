from flask import Blueprint
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return "✅ CropWatch Flask app running successfully"

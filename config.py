import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'alzheimer_ai')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # SQLAlchemy - encode password to handle special characters
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))  # 50MB
    ALLOWED_EXTENSIONS = {'dcm', 'png', 'jpg', 'jpeg'}
    
    # Model
    MODEL_PATH = os.getenv('MODEL_PATH', 'models')
    DATASET_PATH = os.getenv('DATASET_PATH', 'dataset')
    DEMENTIA_MODEL_PATH = os.getenv('DEMENTIA_MODEL_PATH', 'dementia_model.h5')
    IMAGE_SIZE = (128, 128)  # Must match the training notebook (128x128)
    
    # Classes mapping
    CLASS_NAMES = ['NonDemented', 'VeryMildDemented', 'MildDemented', 'ModerateDemented']
    CLASS_TO_RISK = {
        'NonDemented': 'Low',
        'VeryMildDemented': 'Medium',
        'MildDemented': 'High',
        'ModerateDemented': 'High'
    }
    CLASS_TO_LABEL = {
        'NonDemented': 'Normal',
        'VeryMildDemented': 'MCI',
        'MildDemented': 'Alzheimer',
        'ModerateDemented': 'Alzheimer'
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        pass

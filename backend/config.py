import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance", "db.sqlite3")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Oracle Fusion Configuration
    ORACLE_FUSION_BASE_URL = os.getenv('ORACLE_FUSION_BASE_URL')
    ORACLE_FUSION_USERNAME = os.getenv('ORACLE_FUSION_USERNAME')
    ORACLE_FUSION_PASSWORD = os.getenv('ORACLE_FUSION_PASSWORD')
    
    # UCM Specific Settings
    UCM_SECURITY_GROUP = os.getenv('UCM_SECURITY_GROUP', 'FAFusionImportExport')
    UCM_CONTENT_TYPE = os.getenv('UCM_CONTENT_TYPE', 'Document')
    UCM_ACCOUNT = os.getenv('UCM_ACCOUNT', 'fin$/receivables$/import$')
    
    # File Processing Settings
    TEMPLATES_PATH = os.getenv('TEMPLATES_PATH', 'templates')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

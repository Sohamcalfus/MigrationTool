import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(instance_path, "db.sqlite3")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Oracle Cloud Configuration
    ORACLE_BASE_URL = os.getenv('ORACLE_BASE_URL', 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com')
    ORACLE_USERNAME = os.getenv('ORACLE_USERNAME')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD')
    ORACLE_UCM_ACCOUNT = os.getenv('ORACLE_UCM_ACCOUNT', 'fin$/recievables$/import$')
    
    def __init__(self):
        print(f"Database path: {self.SQLALCHEMY_DATABASE_URI}")
        print(f"Oracle Base URL: {self.ORACLE_BASE_URL}")

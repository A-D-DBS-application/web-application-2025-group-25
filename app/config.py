import os


class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Groep25&groep25'
    
    # Supabase PostgreSQL database connection
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres.hsjjntcivrvlguqfdqxl:Ot641zn1rScPUkeo@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application constants
    SPOTABLE_COST_PER_MONTH = 199

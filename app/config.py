import os


class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Groep25&groep25'
    
    # Supabase PostgreSQL database connection
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:5FJrydgxoSBBnqQV@db.hsjjntcivrvlguqfdqxl.supabase.co:5432/postgres?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application constants
    SPOTABLE_COST_PER_MONTH = 199


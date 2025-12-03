import os


class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Groep25&groep25'
    
    # Supabase PostgreSQL database connection
    # Try connection pooler first (port 6543), fallback to direct (port 5432)
    # Connection pooler is usually more reliable and faster
    SUPABASE_HOST = "db.hsjjntcivrvlguqfdqxl.supabase.co"
    SUPABASE_PASSWORD = "5FJrydgxoSBBnqQV"
    
    # Try connection pooler (port 6543) - more reliable
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://postgres:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:6543/postgres?sslmode=require&connect_timeout=10"
    
    # Alternative direct connection (if pooler doesn't work, uncomment this):
    # SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://postgres:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:5432/postgres?sslmode=require&connect_timeout=10"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application constants
    SPOTABLE_COST_PER_MONTH = 199

"""
Database models for the application.
Matches the Supabase ERD schema.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()


class TypeOfCompany(db.Model):
    """Model for company types"""
    __tablename__ = 'Type_of_company'
    
    Type_of_company_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    sector = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Relationship
    companies = db.relationship('Company', backref='type_of_company', lazy=True)
    
    def __repr__(self):
        return f'<TypeOfCompany {self.Type_of_company_id} - {self.sector}>'


class Company(db.Model):
    """Model for companies"""
    __tablename__ = 'Company'
    
    company_id = db.Column('company-id', db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    name = db.Column(db.Text, nullable=True)
    employee_count = db.Column(db.BigInteger, nullable=True)
    projects_per_year = db.Column(db.BigInteger, nullable=False)  # Removed unique=True to allow multiple companies
    type_of_company_id = db.Column(db.BigInteger, db.ForeignKey('Type_of_company.Type_of_company_id'), nullable=True)  # Removed unique=True to allow multiple companies per type
    
    # Relationships
    costs_saved = db.relationship('CostsSaved', backref='company', lazy=True)
    
    def __repr__(self):
        return f'<Company {self.company_id} - {self.name}>'


class PricingAICompany(db.Model):
    """Model for AI company pricing"""
    __tablename__ = 'Pricing_ai_company'
    
    pricing_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ai_service_cost = db.Column(db.BigInteger, nullable=False, unique=True)
    
    # Relationship
    calculators = db.relationship('Calculator', backref='pricing', lazy=True)
    
    def __repr__(self):
        return f'<PricingAICompany {self.pricing_id} - {self.ai_service_cost}>'


class CostsSaved(db.Model):
    """Model for saved costs"""
    __tablename__ = 'Costs_saved'
    
    total_cost_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    company_id = db.Column(db.BigInteger, db.ForeignKey('Company.company-id'), nullable=False)
    hours_spent_process = db.Column(db.Float, nullable=True)
    materials_used_price = db.Column(db.BigInteger, nullable=True, unique=True)
    
    # Relationship
    calculators = db.relationship('Calculator', backref='costs_saved', lazy=True)
    
    def __repr__(self):
        return f'<CostsSaved {self.total_cost_id} - Company {self.company_id}>'


class Calculator(db.Model):
    """Model for ROI calculator results"""
    __tablename__ = 'Calculator'
    
    effect_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    annual_net_profit = db.Column(db.Float, nullable=True)
    total_cost_id = db.Column(db.BigInteger, db.ForeignKey('Costs_saved.total_cost_id'), nullable=True)
    pricing_id = db.Column(db.BigInteger, db.ForeignKey('Pricing_ai_company.pricing_id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f'<Calculator {self.effect_id} - Profit: {self.annual_net_profit}>'


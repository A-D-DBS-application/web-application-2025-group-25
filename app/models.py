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
    # description column removed - not in database schema
    
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
    
    
    def __repr__(self):
        return f'<PricingAICompany {self.pricing_id} - {self.ai_service_cost}>'


class AIPartner(db.Model):
    """Model for AI partners/companies"""
    __tablename__ = 'AI_partner'
    
    partner_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    name = db.Column(db.Text, nullable=True)
    contact_email = db.Column(db.Text, nullable=False, unique=True)
    

    def __repr__(self):
        return f'<AIPartner {self.partner_id} - {self.name}>'


class AISolution(db.Model):
    """Model for AI solutions - needed for foreign key reference"""
    __tablename__ = 'AI_solution'
    
    solution_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, unique=True)
    customer_cost = db.Column(db.Float, nullable=True)
    pricing_model = db.Column(db.Text, nullable=True)
    partner_id = db.Column(db.BigInteger, nullable=True, unique=True)  # FK removed for now, will be used later
    
    def __repr__(self):
        return f'<AISolution {self.solution_id} - {self.name}>'


class InputParameterTemplate(db.Model):
    """Model for input parameter templates"""
    __tablename__ = 'Input_Parameter_Template'
    
    parameters_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    partner_id = db.Column(db.BigInteger, nullable=False, unique=True)
    
    def __repr__(self):
        return f'<InputParameterTemplate {self.parameters_id} - Partner {self.partner_id}>'


class CostsSaved(db.Model):
    """Model for saved costs"""
    __tablename__ = 'Costs_saved'
    
    cost_saved_id = db.Column('Cost_saved_id', db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    company_id = db.Column(db.BigInteger, db.ForeignKey('Company.company-id'), nullable=False)
    hours_spent_process = db.Column(db.Float, nullable=True)
    
    # Relationship
    calculators = db.relationship('Calculator', backref='costs_saved', lazy=True)
    
    def __repr__(self):
        return f'<CostsSaved {self.cost_saved_id} - Company {self.company_id}>'


class Calculator(db.Model):
    """Model for ROI calculator results"""
    __tablename__ = 'Calculator'
    
    calculator_id = db.Column('calculator_id', db.BigInteger, primary_key=True, autoincrement=True)
    annual_net_profit = db.Column('annuel_net_profit', db.Float, nullable=True)  # Note: database has typo "annuel"
    cost_saved_id = db.Column('Cost_saved_id', db.BigInteger, db.ForeignKey('Costs_saved.Cost_saved_id'), nullable=True)
    solution_id = db.Column('solution_id', db.BigInteger, nullable=True)  # FK removed for now, will be used later for AI partners
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Calculator {self.calculator_id} - Profit: {self.annual_net_profit}>'


class ClusteringResult(db.Model):
    """Model for clustering results"""
    __tablename__ = 'Clustering_Result'
    
    clustering_result_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    company_id = db.Column(db.BigInteger, db.ForeignKey('Company.company-id'), nullable=True, unique=True)
    calculator_id = db.Column(db.BigInteger, db.ForeignKey('Calculator.calculator_id'), nullable=True, unique=True)
    cluster_name = db.Column(db.Text, nullable=True)  # e.g., "Measurement Heavy Company"
    
    def __repr__(self):
        return f'<ClusteringResult {self.clustering_result_id} - {self.cluster_name}>'


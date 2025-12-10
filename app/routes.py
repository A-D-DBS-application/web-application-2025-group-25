from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
import json
from io import BytesIO
from datetime import datetime
from app.config import Config
from app.models import (
    db, Company, TypeOfCompany, Calculator, CostsSaved, PricingAICompany, ClusteringResult
)

# Create blueprint for routes
bp = Blueprint('main', __name__)

# Constants
SPOTABLE_COST_PER_MONTH = Config.SPOTABLE_COST_PER_MONTH


def classify_parameter(value, ranges):
    """Classify a value as Small, Medium, or Large based on ranges"""
    small_min, small_max = ranges['small']
    medium_min, medium_max = ranges['medium']
    large_min, large_max = ranges['large']
    
    if small_min <= value <= small_max:
        return 'Small'
    elif medium_min <= value <= medium_max:
        return 'Medium'
    elif value >= large_min:
        return 'Large'
    else:
        return 'Small'  # Default


def classify_company(data):
    """Classify company based on all parameters and generate labels"""
    
    # Define classification ranges for each parameter
    ranges = {
        'employees': {
            'small': (1, 3),
            'medium': (4, 9),
            'large': (10, float('inf'))
        },
        'hourly_wage': {
            'small': (20, 30),
            'medium': (31, 45),
            'large': (46, 60)
        },
        'projects': {
            'small': (1, 9),
            'medium': (10, 25),
            'large': (26, float('inf'))
        },
        'quotes': {
            'small': (1, 15),
            'medium': (16, 40),
            'large': (41, float('inf'))
        },
        'measurement_hours': {
            'small': (1, 20),
            'medium': (21, 60),
            'large': (61, float('inf'))
        },
        'travel_hours': {
            'small': (1, 30),
            'medium': (31, 90),
            'large': (91, float('inf'))
        }
    }
    
    # Classify each parameter
    classifications = {
        'team_size': classify_parameter(data['number_of_employees'], ranges['employees']),
        'hourly_wage': classify_parameter(data['average_hourly_wage'], ranges['hourly_wage']),
        'project_volume': classify_parameter(data['projects_per_month'], ranges['projects']),
        'quote_volume': classify_parameter(data['quotes_per_month'], ranges['quotes']),
        'measurement_hours': classify_parameter(data['measurement_hours_per_month'], ranges['measurement_hours']),
        'travel_hours': classify_parameter(data['travel_hours_per_month'], ranges['travel_hours'])
    }
    
    # Determine overall company size (use employees as primary, but consider other factors)
    team_size = classifications['team_size']
    
    # Generate cluster label based on dominant characteristics
    # Count how many parameters are in each category
    large_count = sum(1 for v in classifications.values() if v == 'Large')
    medium_count = sum(1 for v in classifications.values() if v == 'Medium')
    
    # Determine dominant characteristics
    cluster_labels = []
    
    # Quote-heavy
    if classifications['quote_volume'] == 'Large' and data['quotes_per_month'] / max(data['projects_per_month'], 1) > 2:
        cluster_labels.append('quote-intensive')
    
    # Measurement-heavy
    if classifications['measurement_hours'] == 'Large' or classifications['travel_hours'] == 'Large':
        cluster_labels.append('measurement-heavy')
    
    # High-load
    if large_count >= 3:
        cluster_labels.append('high-load operations')
    
    # Admin-heavy (high quotes relative to projects)
    if classifications['quote_volume'] in ['Large', 'Medium'] and data['quotes_per_month'] > data['projects_per_month'] * 1.5:
        cluster_labels.append('admin-heavy')
    
    # Default label if no specific characteristic dominates
    if not cluster_labels:
        if medium_count >= 3 or (team_size == 'Medium' and medium_count >= 2):
            cluster_labels.append('balanced operations')
        else:
            cluster_labels.append('standard operations')
    
    primary_label = cluster_labels[0].title().replace('-', ' ') + ' company'
    
    # Generate size description
    size_descriptions = []
    
    # Add company size
    if team_size == 'Medium':
        size_descriptions.append('Medium company')
    else:
        size_descriptions.append(f"{team_size} company")
    
    # Add dominant workload descriptions
    dominant_workloads = []
    if classifications['measurement_hours'] == 'Large':
        dominant_workloads.append('large measurement workload')
    if classifications['quote_volume'] == 'Large':
        dominant_workloads.append('heavy quote volume')
    if classifications['project_volume'] == 'Large':
        dominant_workloads.append('high project volume')
    
    if dominant_workloads:
        size_descriptions.append('with ' + ', '.join(dominant_workloads))
    elif medium_count >= 4:
        size_descriptions.append('with balanced operations')
    else:
        size_descriptions.append('with standard operations')
    
    combined_description = ' '.join(size_descriptions)
    
    return {
        'classifications': classifications,
        'cluster_label': primary_label,
        'combined_description': combined_description,
        'team_size': team_size
    }


def calculate_roi(data, monthly_cost, is_ai_partner=False):
    """
    Modular ROI calculation function - reusable for both Spotable and AI partners
    Returns a dictionary with all calculated ROI metrics
    """
    # Calculate current total hours spent
    current_hours_per_month = data['measurement_hours_per_month'] + data['travel_hours_per_month']
    
    # Time saved calculations
    time_saved_measurements = data['measurement_hours_per_month'] * 0.5
    time_saved_travel = data['travel_hours_per_month'] * 0.7
    time_saved_quotes = data['quotes_per_month'] * 0.5
    
    total_monthly_time_saved = (
        time_saved_measurements +
        time_saved_travel +
        time_saved_quotes
    )
    
    # Hours with solution (only measurement and travel hours saved, not quotes)
    hours_saved_measurement_travel = time_saved_measurements + time_saved_travel
    hours_with_solution_per_month = max(0, current_hours_per_month - hours_saved_measurement_travel)
    
    # Saved = Current - With Solution (for the chart)
    hours_saved_for_chart = current_hours_per_month - hours_with_solution_per_month
    
    # Monthly and annual calculations (based on total time saved including quotes)
    monthly_savings = total_monthly_time_saved * data['average_hourly_wage']
    yearly_savings = monthly_savings * 12
    
    # Hours saved per year
    hours_saved_per_year = total_monthly_time_saved * 12
    
    # Cost savings (annual) - savings from reduced admin time
    cost_savings_annual = yearly_savings
    
    # Extra revenue - potential billable hours from time saved
    extra_revenue = total_monthly_time_saved * data['average_hourly_wage'] * 1.5 * 12
    
    # Total annual ROI (cost savings + extra revenue - annual solution cost)
    annual_solution_cost = monthly_cost * 12
    total_annual_roi = cost_savings_annual + extra_revenue - annual_solution_cost
    
    # Detailed ROI Breakdown calculations
    hours_saved_measurement_travel_per_year = hours_saved_measurement_travel * 12
    time_savings_cost = hours_saved_measurement_travel_per_year * data['average_hourly_wage']
    
    # Workflow Analysis
    workflow_analysis = classify_company(data)
    
    return {
        'current_hours_per_month': round(current_hours_per_month, 1),
        'hours_with_spotable_per_month': round(hours_with_solution_per_month, 1),
        'hours_saved_for_chart': round(hours_saved_for_chart, 1),
        'total_monthly_time_saved': round(total_monthly_time_saved, 1),
        'hours_saved_per_year': round(hours_saved_per_year, 0),
        'monthly_savings': round(monthly_savings, 2),
        'yearly_savings': round(yearly_savings, 2),
        'cost_savings_annual': round(cost_savings_annual, 2),
        'extra_revenue': round(extra_revenue, 2),
        'total_annual_roi': round(total_annual_roi, 2),
        'spotable_cost_monthly': monthly_cost,
        'spotable_cost_annual': annual_solution_cost,
        'hours_saved_measurement_travel_per_year': round(hours_saved_measurement_travel_per_year, 0),
        'time_savings_cost': round(time_savings_cost, 2),
        'average_hourly_wage': round(data['average_hourly_wage'], 2),
        'workflow_analysis': workflow_analysis,
        'raw_data': data
    }


def require_login():
    """Helper function to check if user is logged in"""
    if 'email' not in session or 'company_name' not in session:
        return redirect(url_for('main.login'))
    return None


def require_calculator_data():
    """Helper function to check if calculator data exists"""
    if 'calculator_data' not in session:
        return redirect(url_for('main.calculator'))
    return None


def require_auth_and_data():
    """Helper function to check both login and calculator data"""
    login_check = require_login()
    if login_check:
        return login_check
    return require_calculator_data()


def check_database_connection():
    """Check if database connection is available"""
    try:
        db.engine.connect()
        return True
    except Exception as conn_error:
        print(f"❌ Database connection failed: {conn_error}")
        # Don't show flash message to user - only log to console
        return False


def find_or_create_type_of_company(company_type_name):
    """Find or create Type_of_company record"""
    print(f"🔍 Looking for company type: {company_type_name}")
    type_of_company = TypeOfCompany.query.filter_by(sector=company_type_name).first()
    if not type_of_company:
        print(f"➕ Creating new company type: {company_type_name}")
        type_of_company = TypeOfCompany(sector=company_type_name)
        db.session.add(type_of_company)
        db.session.flush()
        print(f"✓ Created Type_of_company with ID: {type_of_company.Type_of_company_id}")
    else:
        print(f"✓ Found existing Type_of_company with ID: {type_of_company.Type_of_company_id}")
    return type_of_company


def find_or_create_company(company_name, data, type_of_company):
    """Find or create Company record"""
    projects_per_year = int(data['projects_per_month'] * 12)
    company = Company.query.filter_by(projects_per_year=projects_per_year).first()
    
    if company:
        print(f"✓ Found existing company with projects_per_year={projects_per_year}: {company.company_id}")
        company.name = company_name
        company.employee_count = int(data['number_of_employees'])
        company.type_of_company_id = type_of_company.Type_of_company_id
        print(f"✓ Updated company: {company.name} (ID: {company.company_id})")
    else:
        print(f"➕ Creating new company record: {company_name}")
        company = Company(
            name=company_name,
            employee_count=int(data['number_of_employees']),
            projects_per_year=projects_per_year,
            type_of_company_id=type_of_company.Type_of_company_id
        )
        db.session.add(company)
    db.session.flush()
    print(f"✓ Company ready: {company.name} (ID: {company.company_id})")
    return company


def find_or_create_pricing(spotable_cost):
    """Find or create Pricing_ai_company record"""
    spotable_annual_cost = int(spotable_cost * 12)
    print(f"🔍 Looking for Pricing_ai_company with cost: {spotable_annual_cost}")
    pricing = PricingAICompany.query.filter_by(ai_service_cost=spotable_annual_cost).first()
    if not pricing:
        print(f"➕ Creating new Pricing_ai_company with cost: {spotable_annual_cost}")
        pricing = PricingAICompany(ai_service_cost=spotable_annual_cost)
        db.session.add(pricing)
        db.session.flush()
        print(f"✓ Created Pricing_ai_company with ID: {pricing.pricing_id}")
    else:
        print(f"✓ Found existing Pricing_ai_company with ID: {pricing.pricing_id}")
    return pricing


def create_costs_saved(company, data):
    """Create Costs_saved record"""
    total_hours_spent = data['measurement_hours_per_month'] + data['travel_hours_per_month']
    hours_spent_per_year = total_hours_spent * 12
    
    costs_saved = CostsSaved(
        company_id=company.company_id,
        hours_spent_process=hours_spent_per_year
    )
    db.session.add(costs_saved)
    db.session.flush()
    return costs_saved


def create_calculator(costs_saved, results_data):
    """Create Calculator record"""
    calculator = Calculator(
        annual_net_profit=results_data['total_annual_roi'],
        cost_saved_id=costs_saved.cost_saved_id,
        solution_id=None
    )
    db.session.add(calculator)
    db.session.flush()
    return calculator


def create_or_update_clustering_result(company, calculator, workflow_analysis):
    """Create or update Clustering_Result record"""
    cluster_name = workflow_analysis.get('cluster_label', 'Standard Operations Company')
    existing_clustering = ClusteringResult.query.filter_by(company_id=company.company_id).first()
    
    if existing_clustering:
        existing_clustering.calculator_id = calculator.calculator_id
        existing_clustering.cluster_name = cluster_name
        print(f"✓ Updated existing Clustering_Result for company {company.company_id}")
    else:
        clustering_result = ClusteringResult(
            company_id=company.company_id,
            calculator_id=calculator.calculator_id,
            cluster_name=cluster_name
        )
        db.session.add(clustering_result)
        print(f"✓ Created new Clustering_Result for company {company.company_id}")


def save_to_database(company_name, company_type_name, data, results_data, workflow_analysis):
    """Helper function to save ROI calculation to database"""
    try:
        # Test database connection first
        if not check_database_connection():
            return False
        
        # 1. Find or create Type_of_company
        type_of_company = find_or_create_type_of_company(company_type_name)
        
        # 2. Find or create Company
        company = find_or_create_company(company_name, data, type_of_company)
        
        # 3. Find or create Pricing_ai_company (Spotable cost)
        find_or_create_pricing(SPOTABLE_COST_PER_MONTH)
        
        # 4. Create Costs_saved
        costs_saved = create_costs_saved(company, data)
        
        # 5. Create Calculator (ROI calculation)
        calculator = create_calculator(costs_saved, results_data)
        
        # 6. Create or update Clustering_Result
        create_or_update_clustering_result(company, calculator, workflow_analysis)
        
        # Commit all changes
        print("💾 Committing to database...")
        db.session.commit()
        cluster_name = workflow_analysis.get('cluster_label', 'Standard Operations Company')
        print(f"✅ Successfully saved ROI calculation to database for {company_name}")
        print(f"   - Company ID: {company.company_id}")
        print(f"   - Calculator ID: {calculator.calculator_id}")
        print(f"   - Annual Net Profit: {calculator.annual_net_profit}")
        print(f"   - Cluster Name: {cluster_name}")
        # Don't show flash message to user - only log to console
        return True
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = str(e)
        print(f"❌ Error saving to database: {error_msg}")
        print("Full traceback:")
        traceback.print_exc()
        # Don't show flash message to user - only log to console
        return False


@bp.route('/')
def index():
    """Redirect to intro page"""
    return redirect(url_for('main.intro'))


@bp.route('/intro')
def intro():
    """Introduction page - explains Spotable and the ROI calculator"""
    return render_template('intro.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - stores email and company_name in session"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        company_name = request.form.get('company_name', '').strip()
        company_type = request.form.get('company_type', '').strip()
        
        # Simple validation
        if not email or not company_name or not company_type:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        # Store in session
        session['email'] = email
        session['company_name'] = company_name
        session['company_type'] = company_type
        
        return redirect(url_for('main.calculator'))
    
    return render_template('login.html')


@bp.route('/calculator', methods=['GET', 'POST'])
def calculator():
    """Calculator page - shows form and processes input"""
    # Check if user is logged in (has session data)
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        # Get all form data
        try:
            number_of_employees = float(request.form.get('number_of_employees', 0))
            average_hourly_wage = float(request.form.get('average_hourly_wage', 0))
            projects_per_month = float(request.form.get('projects_per_month', 0))
            quotes_per_month = float(request.form.get('quotes_per_month', 0))
            measurement_hours_per_month = float(request.form.get('measurement_hours_per_month', 0))
            travel_hours_per_month = float(request.form.get('travel_hours_per_month', 0))
        except ValueError:
            flash('Please enter valid numbers for all fields.', 'error')
            return render_template('calculator.html', 
                                 email=session.get('email'),
                                 company_name=session.get('company_name'))
        
        # Store form data in session for results page
        session['calculator_data'] = {
            'number_of_employees': number_of_employees,
            'average_hourly_wage': average_hourly_wage,
            'projects_per_month': projects_per_month,
            'quotes_per_month': quotes_per_month,
            'measurement_hours_per_month': measurement_hours_per_month,
            'travel_hours_per_month': travel_hours_per_month
        }
        
        return redirect(url_for('main.results'))
    
    return render_template('calculator.html',
                         email=session.get('email'),
                         company_name=session.get('company_name'),
                         company_type=session.get('company_type'))


@bp.route('/results')
def results():
    """Results page - displays ROI calculations"""
    # Check authentication and data
    redirect_response = require_auth_and_data()
    if redirect_response:
        return redirect_response
    
    data = session['calculator_data']
    
    # Use modular ROI calculation function
    results_data = calculate_roi(data, SPOTABLE_COST_PER_MONTH, is_ai_partner=False)
    
    # Save to database
    company_name = session.get('company_name')
    company_type_name = session.get('company_type', 'others')
    workflow_analysis = results_data.get('workflow_analysis', {})
    
    save_to_database(company_name, company_type_name, data, results_data, workflow_analysis)
    
    return render_template('results.html',
                         email=session.get('email'),
                         company_name=company_name,
                         results=results_data)


@bp.route('/export')
def export():
    """Export & Share page - allows downloading and emailing the report"""
    # Check authentication and data
    redirect_response = require_auth_and_data()
    if redirect_response:
        return redirect_response
    
    # Use modular ROI calculation function
    data = session['calculator_data']
    results_data = calculate_roi(data, SPOTABLE_COST_PER_MONTH, is_ai_partner=False)
    
    return render_template('export.html',
                         email=session.get('email'),
                         company_name=session.get('company_name'),
                         company_type=session.get('company_type'),
                         results=results_data)


@bp.route('/download_report')
def download_report():
    """Download report as JSON file"""
    redirect_response = require_calculator_data()
    if redirect_response:
        return redirect_response
    
    # Use modular ROI calculation function
    data = session['calculator_data']
    results_data = calculate_roi(data, SPOTABLE_COST_PER_MONTH, is_ai_partner=False)
    
    # Extract only needed fields for report
    report_results = {
        'monthly_savings': results_data['monthly_savings'],
        'yearly_savings': results_data['yearly_savings'],
        'total_annual_roi': results_data['total_annual_roi'],
        'hours_saved_per_year': results_data['hours_saved_per_year'],
        'cost_savings_annual': results_data['cost_savings_annual'],
        'extra_revenue': results_data['extra_revenue'],
        'time_savings_cost': results_data['time_savings_cost'],
        'workflow_analysis': results_data.get('workflow_analysis', {})
    }
    
    # Create report data
    report_data = {
        'company_name': session.get('company_name'),
        'email': session.get('email'),
        'company_type': session.get('company_type'),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'calculator_data': session.get('calculator_data'),
        'results': report_results
    }
    
    # Create JSON file in memory
    json_str = json.dumps(report_data, indent=2)
    json_bytes = json_str.encode('utf-8')
    json_file = BytesIO(json_bytes)
    json_file.seek(0)
    
    filename = f"ROI_Report_{session.get('company_name', 'Company')}_{datetime.now().strftime('%Y%m%d')}.json"
    
    return send_file(
        json_file,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )


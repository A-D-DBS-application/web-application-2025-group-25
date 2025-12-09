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


@bp.route('/')
def index():
    """Redirect to intro page"""
    return redirect(url_for('main.intro'))


@bp.route('/intro')
def intro():
    """Introduction page - explains Spotable and the ROI calculator"""
    return render_template('intro.html')


@bp.route('/test-db')
def test_db():
    """Test database connection and show status"""
    from flask import jsonify
    try:
        # Test connection
        conn = db.engine.connect()
        conn.close()
        
        # Try a simple query
        count = Company.query.count()
        calc_count = Calculator.query.count()
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful',
            'company_count': count,
            'calculator_count': calc_count,
            'connection_string': str(db.engine.url).replace(db.engine.url.password, '***')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'connection_string': str(db.engine.url).replace(db.engine.url.password, '***') if hasattr(db.engine, 'url') else 'Unknown'
        }), 500


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
    if 'email' not in session or 'company_name' not in session:
        return redirect(url_for('main.login'))
    
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
    # Check if user is logged in
    if 'email' not in session or 'company_name' not in session:
        return redirect(url_for('main.login'))
    
    # Check if calculator data exists
    if 'calculator_data' not in session:
        return redirect(url_for('main.calculator'))
    
    data = session['calculator_data']
    
    # Calculate current total hours spent
    current_hours_per_month = data['measurement_hours_per_month'] + data['travel_hours_per_month']
    
    # ROI Calculation Logic
    time_saved_measurements = data['measurement_hours_per_month'] * 0.5
    time_saved_travel = data['travel_hours_per_month'] * 0.7
    time_saved_quotes = data['quotes_per_month'] * 0.5
    
    total_monthly_time_saved = (
        time_saved_measurements +
        time_saved_travel +
        time_saved_quotes
    )
    
    # Hours with Spotable (only measurement and travel hours saved, not quotes)
    hours_saved_measurement_travel = time_saved_measurements + time_saved_travel
    hours_with_spotable_per_month = max(0, current_hours_per_month - hours_saved_measurement_travel)
    
    # Saved = Current - With Spotable (for the chart)
    hours_saved_for_chart = current_hours_per_month - hours_with_spotable_per_month
    
    # Monthly and annual calculations (based on total time saved including quotes)
    monthly_savings = total_monthly_time_saved * data['average_hourly_wage']
    yearly_savings = monthly_savings * 12
    
    # Hours saved per year
    hours_saved_per_year = total_monthly_time_saved * 12
    
    # Cost savings (annual) - savings from reduced admin time
    cost_savings_annual = yearly_savings
    
    # Extra revenue - potential billable hours from time saved (assuming saved time can be used for billable work)
    # This represents the revenue potential if saved time is used for billable projects
    extra_revenue = total_monthly_time_saved * data['average_hourly_wage'] * 1.5 * 12  # 1.5x multiplier for billable rate
    
    # Total annual ROI (cost savings + extra revenue - annual spotable cost)
    annual_spotable_cost = SPOTABLE_COST_PER_MONTH * 12
    total_annual_roi = cost_savings_annual + extra_revenue - annual_spotable_cost
    
    # Detailed ROI Breakdown calculations
    hours_saved_measurement_travel_per_year = hours_saved_measurement_travel * 12
    time_savings_cost = hours_saved_measurement_travel_per_year * data['average_hourly_wage']
    
    # Workflow Analysis
    workflow_analysis = classify_company(data)
    
    results_data = {
        'current_hours_per_month': round(current_hours_per_month, 1),
        'hours_with_spotable_per_month': round(hours_with_spotable_per_month, 1),
        'hours_saved_for_chart': round(hours_saved_for_chart, 1),
        'total_monthly_time_saved': round(total_monthly_time_saved, 1),
        'hours_saved_per_year': round(hours_saved_per_year, 0),
        'monthly_savings': round(monthly_savings, 2),
        'yearly_savings': round(yearly_savings, 2),
        'cost_savings_annual': round(cost_savings_annual, 2),
        'extra_revenue': round(extra_revenue, 2),
        'total_annual_roi': round(total_annual_roi, 2),
        'spotable_cost_monthly': SPOTABLE_COST_PER_MONTH,
        'spotable_cost_annual': annual_spotable_cost,
        # Detailed ROI Breakdown
        'hours_saved_measurement_travel_per_year': round(hours_saved_measurement_travel_per_year, 0),
        'time_savings_cost': round(time_savings_cost, 2),
        'average_hourly_wage': round(data['average_hourly_wage'], 2),
        # Workflow Analysis
        'workflow_analysis': workflow_analysis,
        'raw_data': data  # For displaying in workflow breakdown
    }
    
    # Save to database according to ERD schema
    try:
        # Test database connection first
        try:
            db.engine.connect()
        except Exception as conn_error:
            print(f"❌ Database connection failed: {conn_error}")
            flash(f'Database connection error: {str(conn_error)[:100]}', 'error')
            return render_template('results.html',
                                 email=session.get('email'),
                                 company_name=session.get('company_name'),
                                 results=results_data)
        
        # 1. Find or create Type_of_company
        company_type_name = session.get('company_type', 'others')
        print(f"🔍 Looking for company type: {company_type_name}")
        type_of_company = TypeOfCompany.query.filter_by(sector=company_type_name).first()
        if not type_of_company:
            print(f"➕ Creating new company type: {company_type_name}")
            type_of_company = TypeOfCompany(
                sector=company_type_name
            )
            db.session.add(type_of_company)
            db.session.flush()  # Get the ID
            print(f"✓ Created Type_of_company with ID: {type_of_company.Type_of_company_id}")
        else:
            print(f"✓ Found existing Type_of_company with ID: {type_of_company.Type_of_company_id}")
        
        # 2. Find or create Company
        # Convert projects_per_month to projects_per_year
        projects_per_year = int(data['projects_per_month'] * 12)
        company_name = session.get('company_name')
        
        # Check if company with this projects_per_year already exists (UNIQUE constraint)
        # If it exists, use that company and update it
        company = Company.query.filter_by(projects_per_year=projects_per_year).first()
        
        if company:
            # Update existing company with new data
            print(f"✓ Found existing company with projects_per_year={projects_per_year}: {company.company_id}")
            company.name = company_name
            company.employee_count = int(data['number_of_employees'])
            company.type_of_company_id = type_of_company.Type_of_company_id
            print(f"✓ Updated company: {company.name} (ID: {company.company_id})")
        else:
            # Create new company
            print(f"➕ Creating new company record: {company_name}")
            company = Company(
                name=company_name,
                employee_count=int(data['number_of_employees']),
                projects_per_year=projects_per_year,
                type_of_company_id=type_of_company.Type_of_company_id
            )
            db.session.add(company)
        db.session.flush()  # Get the ID
        print(f"✓ Company ready: {company.name} (ID: {company.company_id})")
        
        # 3. Find or create Pricing_ai_company (Spotable cost)
        spotable_annual_cost = int(SPOTABLE_COST_PER_MONTH * 12)
        print(f"🔍 Looking for Pricing_ai_company with cost: {spotable_annual_cost}")
        pricing = PricingAICompany.query.filter_by(ai_service_cost=spotable_annual_cost).first()
        if not pricing:
            print(f"➕ Creating new Pricing_ai_company with cost: {spotable_annual_cost}")
            pricing = PricingAICompany(ai_service_cost=spotable_annual_cost)
            db.session.add(pricing)
            db.session.flush()  # Get the ID
            print(f"✓ Created Pricing_ai_company with ID: {pricing.pricing_id}")
        else:
            print(f"✓ Found existing Pricing_ai_company with ID: {pricing.pricing_id}")
        
        # 4. Create Costs_saved
        # Calculate total hours spent (measurement + travel)
        total_hours_spent = data['measurement_hours_per_month'] + data['travel_hours_per_month']
        hours_spent_per_year = total_hours_spent * 12
        
        costs_saved = CostsSaved(
            company_id=company.company_id,
            hours_spent_process=hours_spent_per_year
        )
        db.session.add(costs_saved)
        db.session.flush()  # Get the ID
        
        # 5. Create Calculator (ROI calculation)
        # annual_net_profit = total_annual_roi
        calculator = Calculator(
            annual_net_profit=results_data['total_annual_roi'],
            cost_saved_id=costs_saved.cost_saved_id,
            solution_id=None  # Not used in our calculator
        )
        db.session.add(calculator)
        db.session.flush()  # Get the ID
        
        # 6. Create or update Clustering_Result (save clustering algorithm result)
        cluster_name = workflow_analysis.get('cluster_label', 'Standard Operations Company')
        
        # Check if clustering result already exists for this company
        existing_clustering = ClusteringResult.query.filter_by(company_id=company.company_id).first()
        
        if existing_clustering:
            # Update existing clustering result
            existing_clustering.calculator_id = calculator.calculator_id
            existing_clustering.cluster_name = cluster_name
            print(f"✓ Updated existing Clustering_Result for company {company.company_id}")
        else:
            # Create new clustering result
            clustering_result = ClusteringResult(
                company_id=company.company_id,
                calculator_id=calculator.calculator_id,
                cluster_name=cluster_name
            )
            db.session.add(clustering_result)
            print(f"✓ Created new Clustering_Result for company {company.company_id}")
        
        # Commit all changes
        print("💾 Committing to database...")
        db.session.commit()
        print(f"✅ Successfully saved ROI calculation to database for {session.get('company_name')}")
        print(f"   - Company ID: {company.company_id}")
        print(f"   - Calculator ID: {calculator.calculator_id}")
        print(f"   - Annual Net Profit: {calculator.annual_net_profit}")
        print(f"   - Cluster Name: {cluster_name}")
        flash('✅ Data successfully saved to database!', 'success')
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = str(e)
        print(f"❌ Error saving to database: {error_msg}")
        print("Full traceback:")
        traceback.print_exc()
        # Show detailed error to user
        flash(f'⚠️ Database save failed: {error_msg[:150]}', 'error')
    
    return render_template('results.html',
                         email=session.get('email'),
                         company_name=session.get('company_name'),
                         results=results_data)


@bp.route('/export')
def export():
    """Export & Share page - allows downloading and emailing the report"""
    # Check if user is logged in
    if 'email' not in session or 'company_name' not in session:
        return redirect(url_for('main.login'))
    
    # Check if calculator data exists
    if 'calculator_data' not in session:
        return redirect(url_for('main.calculator'))
    
    # Recalculate results for display
    data = session['calculator_data']
    current_hours_per_month = data['measurement_hours_per_month'] + data['travel_hours_per_month']
    
    time_saved_measurements = data['measurement_hours_per_month'] * 0.5
    time_saved_travel = data['travel_hours_per_month'] * 0.7
    time_saved_quotes = data['quotes_per_month'] * 0.5
    
    total_monthly_time_saved = (
        time_saved_measurements +
        time_saved_travel +
        time_saved_quotes
    )
    
    hours_saved_measurement_travel = time_saved_measurements + time_saved_travel
    hours_with_spotable_per_month = max(0, current_hours_per_month - hours_saved_measurement_travel)
    hours_saved_for_chart = current_hours_per_month - hours_with_spotable_per_month
    
    monthly_savings = total_monthly_time_saved * data['average_hourly_wage']
    yearly_savings = monthly_savings * 12
    hours_saved_per_year = total_monthly_time_saved * 12
    cost_savings_annual = yearly_savings
    extra_revenue = total_monthly_time_saved * data['average_hourly_wage'] * 1.5 * 12
    annual_spotable_cost = SPOTABLE_COST_PER_MONTH * 12
    total_annual_roi = cost_savings_annual + extra_revenue - annual_spotable_cost
    hours_saved_measurement_travel_per_year = hours_saved_measurement_travel * 12
    time_savings_cost = hours_saved_measurement_travel_per_year * data['average_hourly_wage']
    
    workflow_analysis = classify_company(data)
    
    results_data = {
        'current_hours_per_month': round(current_hours_per_month, 1),
        'hours_with_spotable_per_month': round(hours_with_spotable_per_month, 1),
        'hours_saved_for_chart': round(hours_saved_for_chart, 1),
        'total_monthly_time_saved': round(total_monthly_time_saved, 1),
        'hours_saved_per_year': round(hours_saved_per_year, 0),
        'monthly_savings': round(monthly_savings, 2),
        'yearly_savings': round(yearly_savings, 2),
        'cost_savings_annual': round(cost_savings_annual, 2),
        'extra_revenue': round(extra_revenue, 2),
        'total_annual_roi': round(total_annual_roi, 2),
        'spotable_cost_monthly': SPOTABLE_COST_PER_MONTH,
        'spotable_cost_annual': annual_spotable_cost,
        'hours_saved_measurement_travel_per_year': round(hours_saved_measurement_travel_per_year, 0),
        'time_savings_cost': round(time_savings_cost, 2),
        'average_hourly_wage': round(data['average_hourly_wage'], 2),
        'workflow_analysis': workflow_analysis,
        'raw_data': data
    }
    
    return render_template('export.html',
                         email=session.get('email'),
                         company_name=session.get('company_name'),
                         company_type=session.get('company_type'),
                         results=results_data)


@bp.route('/download_report')
def download_report():
    """Download report as JSON file"""
    if 'calculator_data' not in session:
        return redirect(url_for('main.calculator'))
    
    # Recalculate results for report
    data = session['calculator_data']
    current_hours_per_month = data['measurement_hours_per_month'] + data['travel_hours_per_month']
    
    time_saved_measurements = data['measurement_hours_per_month'] * 0.5
    time_saved_travel = data['travel_hours_per_month'] * 0.7
    time_saved_quotes = data['quotes_per_month'] * 0.5
    total_monthly_time_saved = time_saved_measurements + time_saved_travel + time_saved_quotes
    hours_saved_measurement_travel = time_saved_measurements + time_saved_travel
    monthly_savings = total_monthly_time_saved * data['average_hourly_wage']
    yearly_savings = monthly_savings * 12
    hours_saved_per_year = total_monthly_time_saved * 12
    cost_savings_annual = yearly_savings
    extra_revenue = total_monthly_time_saved * data['average_hourly_wage'] * 1.5 * 12
    annual_spotable_cost = SPOTABLE_COST_PER_MONTH * 12
    total_annual_roi = cost_savings_annual + extra_revenue - annual_spotable_cost
    hours_saved_measurement_travel_per_year = hours_saved_measurement_travel * 12
    time_savings_cost = hours_saved_measurement_travel_per_year * data['average_hourly_wage']
    
    workflow_analysis = classify_company(data)
    
    results_data = {
        'monthly_savings': round(monthly_savings, 2),
        'yearly_savings': round(yearly_savings, 2),
        'total_annual_roi': round(total_annual_roi, 2),
        'hours_saved_per_year': round(hours_saved_per_year, 0),
        'cost_savings_annual': round(cost_savings_annual, 2),
        'extra_revenue': round(extra_revenue, 2),
        'time_savings_cost': round(time_savings_cost, 2),
        'workflow_analysis': workflow_analysis
    }
    
    # Create report data
    report_data = {
        'company_name': session.get('company_name'),
        'email': session.get('email'),
        'company_type': session.get('company_type'),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'calculator_data': session.get('calculator_data'),
        'results': results_data
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


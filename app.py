from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os
import json
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions

# Constants
SPOTABLE_COST_PER_MONTH = 199


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


@app.template_filter('currency')
def currency_filter(value):
    """Jinja2 filter for currency formatting with thousand separators"""
    try:
        num = int(round(float(value)))
        # Format with thousand separators (using dot for thousands in European format)
        return f"{num:,}".replace(',', '.')
    except (ValueError, TypeError):
        return str(value)


@app.route('/')
def index():
    """Redirect to login page"""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
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
        
        return redirect(url_for('calculator'))
    
    return render_template('login.html')


@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    """Calculator page - shows form and processes input"""
    # Check if user is logged in (has session data)
    if 'email' not in session or 'company_name' not in session:
        return redirect(url_for('login'))
    
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
        
        return redirect(url_for('results'))
    
    return render_template('calculator.html',
                         email=session.get('email'),
                         company_name=session.get('company_name'),
                         company_type=session.get('company_type'))


@app.route('/results')
def results():
    """Results page - displays ROI calculations"""
    # Check if user is logged in
    if 'email' not in session or 'company_name' not in session:
        return redirect(url_for('login'))
    
    # Check if calculator data exists
    if 'calculator_data' not in session:
        return redirect(url_for('calculator'))
    
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
    
    return render_template('results.html',
                         email=session.get('email'),
                         company_name=session.get('company_name'),
                         results=results_data)


@app.route('/export')
def export():
    """Export & Share page - allows downloading and emailing the report"""
    # Check if user is logged in
    if 'email' not in session or 'company_name' not in session:
        return redirect(url_for('login'))
    
    # Check if calculator data exists
    if 'calculator_data' not in session:
        return redirect(url_for('calculator'))
    
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


@app.route('/download_report')
def download_report():
    """Download report as JSON file"""
    if 'calculator_data' not in session:
        return redirect(url_for('calculator'))
    
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


if __name__ == '__main__':
    app.run(debug=True)


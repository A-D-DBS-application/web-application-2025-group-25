"""
Test script to verify database connection and create tables
Tests the new ERD-based schema
"""
from app import create_app
from app.models import (
    db, Company, TypeOfCompany, Calculator, CostsSaved, PricingAICompany
)
from datetime import datetime

app = create_app()

with app.app_context():
    print("Testing database connection with ERD schema...")
    
    try:
        # Test connection by creating tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created successfully!")
        
        # Test counts
        company_count = Company.query.count()
        calc_count = Calculator.query.count()
        print(f"✓ Database connection successful!")
        print(f"  - Companies: {company_count}")
        print(f"  - Calculators: {calc_count}")
        
        # Test insert following ERD structure
        print("\nTesting database insert with ERD structure...")
        
        # 1. Create Type_of_company
        company_type = TypeOfCompany.query.filter_by(sector="roofing companies").first()
        if not company_type:
            company_type = TypeOfCompany(
                sector="roofing companies",
                description="Roofing companies sector"
            )
            db.session.add(company_type)
            db.session.flush()
        
        # 2. Create Company
        test_company = Company.query.filter_by(name="Test Company").first()
        if not test_company:
            test_company = Company(
                name="Test Company",
                employee_count=5,
                projects_per_year=120,  # 10 per month * 12
                type_of_company_id=company_type.Type_of_company_id
            )
            db.session.add(test_company)
            db.session.flush()
        
        # 3. Create Pricing_ai_company
        pricing = PricingAICompany.query.filter_by(ai_service_cost=2388).first()  # 199 * 12
        if not pricing:
            pricing = PricingAICompany(ai_service_cost=2388)
            db.session.add(pricing)
            db.session.flush()
        
        # 4. Create Costs_saved
        costs_saved = CostsSaved(
            company_id=test_company.company_id,
            hours_spent_process=840.0,  # (40 + 30) * 12
            materials_used_price=None
        )
        db.session.add(costs_saved)
        db.session.flush()
        
        # 5. Create Calculator
        calculator = Calculator(
            annual_net_profit=15000.0,
            total_cost_id=costs_saved.total_cost_id,
            pricing_id=pricing.pricing_id,
            created_at=datetime.utcnow()
        )
        db.session.add(calculator)
        db.session.commit()
        
        print("✓ Test records inserted successfully!")
        print(f"  - Company ID: {test_company.company_id}")
        print(f"  - Calculator ID: {calculator.effect_id}")
        
        # Verify it was saved
        saved_calc = Calculator.query.filter_by(effect_id=calculator.effect_id).first()
        if saved_calc:
            print(f"✓ Record verified! Calculator ID: {saved_calc.effect_id}, Profit: {saved_calc.annual_net_profit}")
            # Clean up test records
            db.session.delete(saved_calc)
            db.session.delete(costs_saved)
            db.session.commit()
            print("✓ Test records cleaned up.")
        else:
            print("✗ Record not found after insert!")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


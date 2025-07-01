from strands import tool
from typing import Dict, Optional, List
import datetime
import os
import boto3
from utils.customer_dynamodb import SolarCustomerDynamoDB

# Initialize the DynamoDB customer profile manager
db = SolarCustomerDynamoDB()

# Try to get table name from SSM parameter store
table_name = db.get_table_name_from_ssm()
if not table_name:
    # Default table name if not found in parameter store
    table_name = "SolarCustomerProfiles"
    print(f"Warning: Table name not found in parameter store, using default: {table_name}")

@tool
def get_customer_profile(customer_id: str = None, email: str = None) -> Dict:
    """
    Get customer profile information by customer ID or email from DynamoDB.
    
    Args:
        customer_id (str, optional): The customer ID to lookup
        email (str, optional): The customer email to lookup
        
    Returns:
        dict: Customer profile information or error message
    """
    if not customer_id and not email:
        return {"status": "error", "message": "Either customer_id or email must be provided"}
    
    profile = None
    if customer_id:
        profile = db.get_profile_by_id(customer_id, table_name)
    elif email:
        profile = db.get_profile_by_email(email, table_name)
        
    if not profile:
        return {"status": "error", "message": "Customer profile not found"}

    return profile


@tool
def update_customer_profile(customer_id: str, updates: Dict) -> Dict:
    """
    Update customer profile information in DynamoDB.
    
    Args:
        customer_id (str): The customer ID to update
        updates (dict): The updates to apply to the profile
        
    Returns:
        dict: Updated customer profile or error message
    """
    updated_profile = db.update_profile(customer_id, updates, table_name)
    if not updated_profile:
        return {"status": "error", "message": "Customer profile not found or update failed"}
        
    return updated_profile


@tool
def analyze_solar_system_performance(customer_id: str = None, email: str = None, time_period: str = "month") -> Dict:
    """
    Analyze a customer's solar system performance based on their installed products.
    
    Args:
        customer_id (str, optional): The customer ID to lookup
        email (str, optional): The customer email to lookup
        time_period (str): Period for analysis ('month', 'quarter', 'year')
        
    Returns:
        dict: Performance analysis results or error message
    """
    if not customer_id and not email:
        return {"status": "error", "message": "Either customer_id or email must be provided"}
    
    profile = None
    if customer_id:
        profile = db.get_profile_by_id(customer_id, table_name)
    elif email:
        profile = db.get_profile_by_email(email, table_name)
        
    if not profile:
        return {"status": "error", "message": "Customer profile not found"}
    
    # Simulate performance analysis based on purchased products
    purchase_history = profile.get('purchase_history', [])
    panel_purchases = [p for p in purchase_history if p.get("product_type") == "panel"]
    
    if not panel_purchases:
        return {"status": "error", "message": "No solar panels found in customer purchase history"}
    
    # Simple simulated performance analysis
    total_capacity = 0
    panel_models = []
    for purchase in panel_purchases:
        # Estimate capacity based on product name
        model_name = purchase.get("product_name", "")
        quantity = purchase.get("quantity", 1)
        
        # Map panel models to estimated wattage
        wattage = 0
        if "SunPower X" in model_name:
            wattage = 320
        elif "SunPower Y" in model_name:
            wattage = 290
        elif "SunPower Double-X" in model_name:
            wattage = 400
        else:
            wattage = 300  # default estimate
            
        total_capacity += wattage * quantity
        panel_models.append({"model": model_name, "quantity": quantity, "wattage": wattage})
    
    # Simulate performance data
    today = datetime.datetime.now()
    
    # Performance depends on time period
    if time_period == "month":
        days = 30
        efficiency = 0.92  # 92% of expected performance
    elif time_period == "quarter":
        days = 90
        efficiency = 0.89  # 89% of expected performance
    else:  # year
        days = 365
        efficiency = 0.87  # 87% of expected performance
    
    # Simulate daily production (simplified calculation)
    avg_daily_sun_hours = 5.5
    expected_daily_kwh = total_capacity * avg_daily_sun_hours / 1000
    actual_daily_kwh = expected_daily_kwh * efficiency
    
    # Calculate period totals
    expected_kwh = expected_daily_kwh * days
    actual_kwh = actual_daily_kwh * days
    
    # Return analysis results
    return {
        "status": "success",
        "customer_name": profile.get('name'),
        "system_details": {
            "total_capacity_watts": total_capacity,
            "panel_models": panel_models
        },
        "performance_analysis": {
            "time_period": time_period,
            "expected_kwh_production": round(expected_kwh, 2),
            "actual_kwh_production": round(actual_kwh, 2),
            "performance_ratio": round(efficiency * 100, 1),
            "avg_daily_production_kwh": round(actual_daily_kwh, 2),
        },
        "recommendations": generate_recommendations(efficiency)
    }


@tool
def check_warranty_status(customer_id: str = None, email: str = None, product_name: str = None) -> Dict:
    """
    Check warranty status for customer products and provide claim information.
    
    Args:
        customer_id (str, optional): The customer ID to lookup
        email (str, optional): The customer email to lookup
        product_name (str, optional): Specific product to check warranty for
        
    Returns:
        dict: Warranty information or error message
    """
    if not customer_id and not email:
        return {"status": "error", "message": "Either customer_id or email must be provided"}
    
    profile = None
    if customer_id:
        profile = db.get_profile_by_id(customer_id, table_name)
    elif email:
        profile = db.get_profile_by_email(email, table_name)
        
    if not profile:
        return {"status": "error", "message": "Customer profile not found"}
    
    # Get all products or filter by specific product
    purchase_history = profile.get('purchase_history', [])
    products = purchase_history
    if product_name:
        products = [p for p in products if product_name.lower() in p.get("product_name", "").lower()]
        
    if not products:
        return {"status": "error", "message": "No matching products found in purchase history"}
    
    # Generate warranty information for each product
    warranty_info = []
    for product in products:
        product_name = product.get("product_name", "Unknown Product")
        purchase_date_str = product.get("purchase_date", "")
        
        try:
            purchase_date = datetime.datetime.fromisoformat(purchase_date_str)
            today = datetime.datetime.now()
            
            # Determine warranty length based on product type
            warranty_years = 0
            if "SunPower X" in product_name:
                warranty_years = 25
            elif "SunPower Y" in product_name:
                warranty_years = 20
            elif "SunPower Double-X" in product_name:
                warranty_years = 30
            elif "inverter" in product.get("product_type", "").lower():
                warranty_years = 10
            else:
                warranty_years = 5  # default warranty
                
            warranty_end_date = purchase_date.replace(year=purchase_date.year + warranty_years)
            days_remaining = (warranty_end_date - today).days
            warranty_active = days_remaining > 0
            
            warranty_info.append({
                "product_name": product_name,
                "purchase_date": purchase_date_str,
                "warranty_length_years": warranty_years,
                "warranty_end_date": warranty_end_date.isoformat(),
                "warranty_active": warranty_active,
                "days_remaining": max(0, days_remaining),
                "warranty_percentage_remaining": round(max(0, days_remaining) / (warranty_years * 365) * 100, 1),
                "claim_process": get_claim_process(product_name) if warranty_active else "Warranty expired"
            })
            
        except (ValueError, TypeError):
            warranty_info.append({
                "product_name": product_name,
                "error": "Could not determine warranty status due to invalid purchase date"
            })
    
    return {
        "status": "success",
        "customer_name": profile.get('name'),
        "warranty_information": warranty_info
    }


def generate_recommendations(efficiency_ratio):
    """Helper function to generate performance recommendations based on efficiency ratio"""
    if efficiency_ratio >= 0.95:
        return [
            "Your system is performing excellently. Continue with standard maintenance."
        ]
    elif efficiency_ratio >= 0.85:
        return [
            "Your system is performing adequately but could be improved.",
            "Consider cleaning panels to remove potential debris or dust buildup.",
            "Check for any new shade sources that may have developed near panels."
        ]
    else:
        return [
            "Your system is performing below expectations.",
            "We recommend scheduling a professional inspection to identify issues.",
            "Check for inverter error codes or warning lights.",
            "Ensure all panels are clean and free from debris or shading.",
            "Monitor performance daily to identify any patterns in reduced output."
        ]


def get_claim_process(product_name):
    """Helper function to return warranty claim process for a product"""
    if "SunPower" in product_name:
        return "Submit claim through SunPower warranty portal with serial number. Customer support will arrange inspection within 5-7 business days."
    else:
        return "Contact customer support with product serial number to initiate warranty claim process."
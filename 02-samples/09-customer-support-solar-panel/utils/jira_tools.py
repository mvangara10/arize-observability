# Consider this for Atlassian MCP server: https://github.com/sooperset/mcp-atlassian

import os
from typing import Literal, Dict

from atlassian import Jira
from dotenv import load_dotenv
from strands import tool

# Load environment variables from .env file
load_dotenv()

# Initialize constants
PROJECT_NAME = os.getenv("PROJECT_NAME", "SOLAR")
JIRA_URL = os.getenv("JIRA_INSTANCE_URL", "")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_CLOUD = os.getenv("JIRA_CLOUD", "false").lower() == "true"

# Initialize Jira client if credentials are available
jira = None
PROJECT_KEY = None

if JIRA_URL and JIRA_USERNAME and JIRA_API_TOKEN:
    try:
        jira = Jira(
            url=JIRA_URL,
            username=JIRA_USERNAME,
            password=JIRA_API_TOKEN,
            cloud=JIRA_CLOUD,
        )
        
        def get_project_key(project_name: str) -> str:
            """Retrieve the Jira project key for a given project name."""
            projects = jira.projects(expand=None)
            if not projects:
                raise RuntimeError("No projects found in Jira instance.")
            
            project_dict = {project["name"]: project["key"] for project in projects}
            if project_name not in project_dict:
                raise ValueError(f"Project '{project_name}' not found in Jira.")
            
            return project_dict[project_name]
        
        # Attempt to get project key on module load
        try:
            PROJECT_KEY = get_project_key(PROJECT_NAME)
        except Exception as e:
            print(f"Warning: Failed to initialize project key: {e}")
    except Exception as e:
        print(f"Warning: Failed to initialize Jira client: {e}")
else:
    print("Warning: Jira integration disabled due to missing credentials")


@tool
def create_solar_support_ticket(
    customer_id: str, 
    title: str, 
    description: str, 
    ticket_type: Literal["Installation", "Maintenance", "Performance", "Billing", "Technical"],
    customer_email: str = None  # Add email for better customer linking
) -> Dict:
    """
    Create a solar panel support ticket in Jira.

    Args:
        customer_id (str): ID of the customer with the issue
        title (str): One-line summary of the support issue
        description (str): Detailed description of the issue
        ticket_type (Literal): Type of solar panel issue

    Returns:
        dict: Information about the created ticket or error message
    """
    if not jira or not PROJECT_KEY:
        return {
            "status": "error",
            "message": "Jira integration is not properly configured"
        }
    
    # Add customer information to description
    customer_info = f"Customer ID: {customer_id}\n"
    if customer_email:
        customer_info += f"Customer Email: {customer_email}\n"
    full_description = f"{customer_info}\n{description}"
    
    # Map our ticket types to Jira issue types
    # Assuming Jira has "Task" issue type for all solar support tickets
    issue_type = "Task"
    
    issue_payload = {
        "project": {"key": PROJECT_KEY},
        "summary": title,
        "description": full_description,
        "issuetype": {"name": issue_type},
        "labels": [ticket_type, f"customer-{customer_id}"],  # Add customer ID as label for easier searching
    }

    try:
        response = jira.issue_create_or_update(issue_payload)
        ticket_key = response.get('key', 'Unknown')
        return {
            "status": "success",
            "message": f"{ticket_type} support ticket created successfully",
            "ticket_key": ticket_key
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create Jira ticket: {e}"
        }


@tool
def get_customer_tickets(customer_id: str) -> Dict:
    """
    Get all support tickets for a specific customer.

    Args:
        customer_id (str): ID of the customer to look up

    Returns:
        dict: Information about the customer's tickets or error message
    """
    if not jira or not PROJECT_KEY:
        return {
            "status": "error",
            "message": "Jira integration is not properly configured"
        }
    
    try:
        # Search for customer ID in ticket description
        # Note: In a real system, you might have a custom field for customer ID
        jql_query = f'project = {PROJECT_KEY} AND description ~ "Customer ID: {customer_id}"'
        
        response = jira.jql(jql_query)
        issues = response.get('issues', [])
        
        tickets = []
        for issue in issues:
            ticket = {
                "key": issue.get('key'),
                "summary": issue.get('fields', {}).get('summary'),
                "status": issue.get('fields', {}).get('status', {}).get('name'),
                "type": issue.get('fields', {}).get('issuetype', {}).get('name'),
                "created": issue.get('fields', {}).get('created'),
                "updated": issue.get('fields', {}).get('updated')
            }
            tickets.append(ticket)
        
        return {
            "status": "success",
            "count": len(tickets),
            "tickets": tickets
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve customer tickets: {e}"
        }
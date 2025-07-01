import boto3
import os
from boto3.session import Session
from datetime import datetime
import sys

# Add parent directory to path so we can import from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

class SolarCustomerDynamoDB:
    """
    Support class for managing customer profiles in DynamoDB.
    Provides functions to create, delete, and populate the customer table.
    """

    def __init__(self, region_name=None):
        """
        Initialize the DynamoDB manager with optional AWS region
        
        Args:
            region_name: Optional AWS region name
        """
        self._boto_session = Session()
        self._region = region_name or self._boto_session.region_name
        self._dynamodb_client = boto3.client("dynamodb", region_name=self._region)
        self._dynamodb_resource = boto3.resource("dynamodb", region_name=self._region)
        self._ssm_client = boto3.client('ssm', region_name=self._region)
        
        # Default table name - can be overridden in function calls
        self.table_name = 'SolarCustomerProfiles'

    def create_table(self, table_name=None):
        """
        Create a DynamoDB table for customer profiles
        
        Args:
            table_name: Optional table name (defaults to SolarCustomerProfiles)
            
        Returns:
            DynamoDB Table object
        """
        table_name = table_name or self.table_name
        
        try:
            table = self._dynamodb_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "customer_id", "KeyType": "HASH"},  # Partition key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "customer_id", "AttributeType": "S"},  # customer_id
                    {"AttributeName": "email", "AttributeType": "S"},  # email
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'EmailIndex',
                        'KeySchema': [
                            {'AttributeName': "email", 'KeyType': 'HASH'},
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                ],
                BillingMode="PAY_PER_REQUEST",  # Use on-demand capacity mode
            )

            # Wait for the table to be created
            print(f'Creating table {table_name}...')
            table.wait_until_exists()
            print(f'Table {table_name} created successfully!')
            
            # Store table name in parameter store for easy retrieval
            self._ssm_client.put_parameter(
                Name=f'solar-customer-table-name',
                Description=f'Solar customer profile table name',
                Value=table_name,
                Type='String',
                Overwrite=True
            )
            return table
        except self._dynamodb_client.exceptions.ResourceInUseException:
            print(f"Table {table_name} already exists, retrieving it")
            # Update parameter store anyway to ensure it's current
            self._ssm_client.put_parameter(
                Name=f'solar-customer-table-name',
                Description=f'Solar customer profile table name',
                Value=table_name,
                Type='String',
                Overwrite=True
            )
            return self._dynamodb_resource.Table(table_name)

    def delete_table(self, table_name=None):
        """
        Delete the DynamoDB customer profiles table and clean up SSM parameter
        
        Args:
            table_name: Optional table name (defaults to SolarCustomerProfiles)
            
        Returns:
            True if successful, False otherwise
        """
        table_name = table_name or self.table_name
        cleaned_up_ssm = False
        cleaned_up_table = False
        
        # First check if the table exists before trying to delete
        if not self.table_exists(table_name):
            print(f"Table {table_name} does not exist, no need to delete.")
            cleaned_up_table = True
        else:
            try:
                self._dynamodb_client.delete_table(TableName=table_name)
                print(f"Table {table_name} is being deleted...")
                waiter = self._dynamodb_client.get_waiter('table_not_exists')
                waiter.wait(TableName=table_name)
                print(f"Table {table_name} has been deleted.")
                cleaned_up_table = True
            except Exception as e:
                print(f"Error deleting table {table_name}: {e}")
        
        # Always try to clean up SSM parameter regardless of table existence
        try:
            # Check if the SSM parameter exists and if it points to the table we're deleting
            ssm_table = self.get_table_name_from_ssm()
            if ssm_table and (ssm_table == table_name or table_name is None):
                self._ssm_client.delete_parameter(Name='solar-customer-table-name')
                print(f"SSM parameter 'solar-customer-table-name' deleted.")
            cleaned_up_ssm = True
        except self._ssm_client.exceptions.ParameterNotFound:
            print(f"SSM parameter 'solar-customer-table-name' not found.")
            cleaned_up_ssm = True
        except Exception as e:
            print(f"Error cleaning up SSM parameter: {e}")
            
        return cleaned_up_table and cleaned_up_ssm

    def generate_synthetic_profiles(self, count=10, table_name=None):
        """
        Generate synthetic customer profiles directly in DynamoDB
        
        Args:
            count: Number of profiles to generate (default: 10)
            table_name: Optional table name (defaults to SolarCustomerProfiles)
            
        Returns:
            List of customer IDs created
        """
        table_name = table_name or self.table_name
        table = self._dynamodb_resource.Table(table_name)
        
        countries = ["USA", "Canada", "Australia", "UK", "Germany"]
        states = {
            "USA": ["California", "Texas", "New York", "Florida", "Washington"],
            "Canada": ["Ontario", "Quebec", "British Columbia", "Alberta"],
            "Australia": ["New South Wales", "Victoria", "Queensland"],
            "UK": ["England", "Scotland", "Wales"],
            "Germany": ["Bavaria", "Berlin", "Hesse"]
        }
        products = [
            {"name": "SunPower X", "price": 1200, "type": "panel"},
            {"name": "SunPower Y", "price": 800, "type": "panel"},
            {"name": "SunPower Double-X", "price": 1600, "type": "panel"},
            {"name": "PowerWall Battery", "price": 5000, "type": "battery"},
            {"name": "SolarInverter X1", "price": 1500, "type": "inverter"},
            {"name": "EcoCharge Controller", "price": 300, "type": "controller"}
        ]
        # No ticket types needed - tickets are managed in JIRA only
        
        created_profiles = []
        
        for i in range(count):
            customer_id = f"CUST{100+i}"
            name = f"Customer {i+1}"
            email = f"customer{i+1}@example.com"
            country = countries[i % len(countries)]
            state = states[country][i % len(states[country])]
            
            # Generate purchase history
            purchase_count = (i % 3) + 1  # 1-3 purchases
            purchases = []
            for j in range(purchase_count):
                product = products[(i+j) % len(products)]
                purchase_date = datetime.now().replace(
                    month=((i+j) % 12) + 1,
                    day=((i*j) % 28) + 1
                ).isoformat()
                
                purchases.append({
                    "purchase_id": f"PUR{100+i}{j}",
                    "product_name": product["name"],
                    "product_type": product["type"],
                    "price": product["price"],
                    "quantity": (j % 2) + 1,
                    "purchase_date": purchase_date
                })
            
            # Support tickets removed - now managed in JIRA only
            
            # Generate preferences
            preferences = {
                "contact_preference": "email" if i % 2 == 0 else "phone",
                "newsletter": i % 3 == 0,
                "maintenance_reminder": i % 2 == 0
            }
            
            # Create profile directly in DynamoDB
            profile_data = {
                "customer_id": customer_id,
                "name": name,
                "email": email,
                "country": country,
                "state": state,
                "purchase_history": purchases,
                "preferences": preferences,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Store in DynamoDB
            table.put_item(Item=profile_data)
            created_profiles.append(customer_id)
        
        print(f"Generated and stored {len(created_profiles)} synthetic customer profiles")
        return created_profiles

    def get_profile_by_id(self, customer_id, table_name=None):
        """
        Retrieve a customer profile by customer ID
        
        Args:
            customer_id: The customer ID to look up
            table_name: Optional table name (defaults to SolarCustomerProfiles)
            
        Returns:
            Customer profile dict or None if not found
        """
        table_name = table_name or self.table_name
        table = self._dynamodb_resource.Table(table_name)
        
        try:
            response = table.get_item(Key={'customer_id': customer_id})
            return response.get('Item')
        except Exception as e:
            print(f"Error retrieving customer profile: {e}")
            return None
    
    def get_profile_by_email(self, email, table_name=None):
        """
        Retrieve a customer profile by email
        
        Args:
            email: The customer email to look up
            table_name: Optional table name (defaults to SolarCustomerProfiles)
            
        Returns:
            Customer profile dict or None if not found
        """
        table_name = table_name or self.table_name
        table = self._dynamodb_resource.Table(table_name)
        
        try:
            response = table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
            )
            if response.get('Items'):
                return response['Items'][0]
            return None
        except Exception as e:
            print(f"Error retrieving customer profile by email: {e}")
            return None
    
    def update_profile(self, customer_id, updates, table_name=None):
        """
        Update a customer profile with new information
        
        Args:
            customer_id: The customer ID to update
            updates: Dictionary containing fields to update
            table_name: Optional table name (defaults to SolarCustomerProfiles)
            
        Returns:
            Updated profile dict or None if failed
        """
        table_name = table_name or self.table_name
        table = self._dynamodb_resource.Table(table_name)
        
        try:
            # Check if customer exists
            profile = self.get_profile_by_id(customer_id, table_name)
            if not profile:
                print(f"Customer with ID {customer_id} not found")
                return None
            
            # Add updated timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            # Prepare update expression
            update_expression = "SET "
            expression_attr_values = {}
            expression_attr_names = {}
            
            for key, value in updates.items():
                update_expression += f"#{key} = :{key}, "
                expression_attr_values[f":{key}"] = value
                expression_attr_names[f"#{key}"] = key
            
            # Remove trailing comma and space
            update_expression = update_expression[:-2]
            
            # Update the profile
            response = table.update_item(
                Key={'customer_id': customer_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attr_names,
                ExpressionAttributeValues=expression_attr_values,
                ReturnValues="ALL_NEW"
            )
            
            return response.get('Attributes')
        except Exception as e:
            print(f"Error updating customer profile: {e}")
            return None
    
    def get_table_name_from_ssm(self):
        """
        Retrieves the customer profile table name from SSM Parameter Store
        
        Returns:
            Table name or None if parameter not found
        """
        try:
            response = self._ssm_client.get_parameter(Name='solar-customer-table-name')
            return response['Parameter']['Value']
        except self._ssm_client.exceptions.ParameterNotFound:
            return None
            
    def table_exists(self, table_name):
        """
        Checks if the DynamoDB table actually exists
        
        Args:
            table_name: The table name to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            self._dynamodb_client.describe_table(TableName=table_name)
            return True
        except self._dynamodb_client.exceptions.ResourceNotFoundException:
            return False


# Example usage (can be directly called from notebooks):
if __name__ == "__main__":
    # This code will only run when the module is executed directly
    # Useful for testing
    
    db = SolarCustomerDynamoDB()
    
    # Create table example
    table = db.create_table()
    
    # Generate profiles example
    db.generate_synthetic_profiles(count=5)
    
    # Get profile example
    profile = db.get_profile_by_id("CUST100")
    if profile:
        print(f"Found customer: {profile['name']}")
    
    # Update profile example
    updated = db.update_profile("CUST100", {"name": "Updated Customer Name"})
    if updated:
        print(f"Updated customer name: {updated['name']}")
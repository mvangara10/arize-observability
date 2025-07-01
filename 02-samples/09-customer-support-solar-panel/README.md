# Solar Panel Customer Support System

This example implements a comprehensive solar panel customer support agent using Amazon Bedrock, Amazon DynamoDB, Atlassian JIRA, Mem0 and Langfuse integration. The Strands Agent provides personalized customer support with conversation memory, and automated ticketing, observability for monitoring and tracking and custom tools created using [Strands Agents SDK](https://strandsagents.com/latest/) related to solar panel maintainence !

## Architecture Overview

The Solar Panel Customer Support System combines several technologies to create a support solution :

[Architecture](./images/architecture.png)

## Prerequisites

Python 3.10+
Anthropic Claude 3.7 enabled on Amazon Bedrock

| Component | Description |
|-----------|-------------|
| AWS Account | With access to Amazon Bedrock and Amazon DynamoDB |
| Mem0 API Key | For conversation memory storage (m0-*) |
| JIRA Account | For ticket creation and management  |
| Langfuse Account Keys| Public Key and Secret key for observability |
| Python 3.10+ | With required packages in requirements.txt |

## Project Structure

- `01_solar_panel_customer_support_setup.ipynb`: Sets up required AWS resources (DynamoDB, Knowledge Base, Guardrails)
- `02_Customer_support_OTEL_mem0_JIRA.ipynb`: Implements the customer support agent with integrations
- `customer_profile_tools_dynamodb.py`: Contains tools for customer profile management
- `utils/`: Directory with utility functions for JIRA, DynamoDB, and Knowledge Base operations
- `.env.example`: Example environment variables file for JIRA integration

## Setup Instructions

### Step 1: Run the Setup Notebook

Start by running the `01_solar_panel_customer_support_setup.ipynb` notebook which:

1. Creates a DynamoDB table for customer profiles
2. Populates the table with sample customer data
3. Creates an Amazon Bedrock Knowledge Base with solar panel documentation
4. Sets up Amazon Bedrock Guardrails for content safety
5. Generates a configuration file (`solar_panel_support_config.json`) containing all resource IDs

This configuration file will be used by the second notebook to connect to the created resources.

### Step 2: Configure JIRA Integration

If you want to use the JIRA ticketing system integration:

1. Rename `.env.example` to `.env` and update it with your JIRA credentials:
   ```
   JIRA_INSTANCE_URL=https://your-domain.atlassian.net/
   JIRA_USERNAME=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   JIRA_CLOUD=True
   PROJECT_NAME=SOLAR
   ```

2. Create a project named "SOLAR" in your JIRA instance

### Step 3: Run the Customer Support Agent Notebook

- **The configuration file**: The first notebook creates a `solar_panel_support_config.json` file that contains all resource IDs. This file is used by the second notebook to connect to the right resources. Make sure this file exists before running the second notebook.

Run `02_Customer_support_OTEL_mem0_JIRA.ipynb` which:

1. Loads the configuration from `solar_panel_support_config.json`
2. Sets up integrations with Mem0 for memory, JIRA for ticketing and Langfuse for Observability
3. Creates the Strands agent with all the necessary tools
4. Tests the agent with various customer support scenarios
5. The notebook outputs are verbose to showcase the underlying steps.

## Clean up

- **Resource Cleanup**: At the end of the `02_Customer_support_OTEL_mem0_JIRA.ipynb` notebook, please run the cleanup section that deletes created Amazon resources.


## Features

- Customer profile management with Amazon DynamoDB
- Custom tools created such as Solar system performance analysis, Warranty status checking
- JIRA ticket creation and management
- Conversation memory and personalisation with Mem0
- Amazon Knowledge base integration for product information
- OpenTelemetry observability for a Strands Agent with Langfuse


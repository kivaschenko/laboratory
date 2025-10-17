# API Documentation

The Laboratory Management System provides a web-based interface for all operations. This document describes the main endpoints and their functionality.

## Overview

The application is built using the Pyramid web framework and follows RESTful principles where applicable. All endpoints require proper authentication and authorization.

## Authentication

The system uses session-based authentication with secure cookie sessions.

### Login
- **URL**: `/login`
- **Method**: GET, POST
- **Description**: User authentication
- **Required Fields**: username, password

### Logout
- **URL**: `/logout`
- **Method**: GET
- **Description**: End user session

## Core Endpoints

### Dashboard
- **URL**: `/`
- **Method**: GET
- **Description**: Main dashboard with overview
- **Permissions**: Authenticated users

### Substances Management

#### List Substances
- **URL**: `/substances`
- **Method**: GET
- **Description**: Display all substances
- **Permissions**: read

#### Add Substance
- **URL**: `/add_substance`
- **Method**: GET, POST
- **Description**: Add new substance to catalog
- **Required Fields**: name, measurement
- **Permissions**: create

#### Edit Substances
- **URL**: `/substances/edit`
- **Method**: GET
- **Description**: List substances for editing
- **Permissions**: read

#### Delete Substance
- **URL**: `/substance/{subs_id}/delete`
- **Method**: GET
- **Description**: Remove substance from catalog
- **Permissions**: edit

### Normatives and Solutions

#### New Normative
- **URL**: `/new-normative`
- **Method**: GET, POST
- **Description**: Create solution recipe
- **Required Fields**: name, output, type, ingredients
- **Permissions**: create

#### Normatives List
- **URL**: `/normatives-list`
- **Method**: GET
- **Description**: Display all normative recipes
- **Permissions**: read

#### Edit Normative
- **URL**: `/normative-edit/{normative}`
- **Method**: GET, POST
- **Description**: Modify normative recipe
- **Permissions**: edit

#### Create Solution
- **URL**: `/create-solution/{normative}`
- **Method**: GET, POST
- **Description**: Prepare solution from normative
- **Required Fields**: amount, date
- **Permissions**: create

#### Solutions List
- **URL**: `/solutions`
- **Method**: GET
- **Description**: Display all prepared solutions
- **Permissions**: read

#### Solution Details
- **URL**: `/solutions/{solution_id}`
- **Method**: GET
- **Description**: View solution details
- **Permissions**: read

#### Correct Solution
- **URL**: `/correct_solution/{normative}`
- **Method**: GET, POST
- **Description**: Adjust solution quantities
- **Permissions**: edit

#### Delete Solution
- **URL**: `/delete-solution/{solution_id}`
- **Method**: GET, POST
- **Description**: Remove solution record
- **Permissions**: edit

### Recipes and Analysis

#### New Recipe
- **URL**: `/new-recipe`
- **Method**: GET, POST
- **Description**: Create analysis recipe
- **Required Fields**: name, substances, solutions
- **Permissions**: create

#### Recipe Details
- **URL**: `/new-recipe-next/{name}/{solutions}/{substances}`
- **Method**: GET, POST
- **Description**: Set recipe quantities
- **Permissions**: create

#### Recipes List
- **URL**: `/recipes`
- **Method**: GET
- **Description**: Display all analysis recipes
- **Permissions**: read

#### Recipe Details
- **URL**: `/resipe-details/{id_recipe}`
- **Method**: GET
- **Description**: View recipe details
- **Permissions**: read

#### Edit Recipes
- **URL**: `/recipes/edit`
- **Method**: GET
- **Description**: List recipes for editing
- **Permissions**: read

#### Delete Recipe
- **URL**: `/delete-recipe/{recipe_id}`
- **Method**: GET
- **Description**: Remove recipe
- **Permissions**: edit

#### Analysis Done
- **URL**: `/analysis-done`
- **Method**: GET
- **Description**: List completed analyses
- **Permissions**: read

#### Add Analysis
- **URL**: `/add-analysis/{id_recipe}`
- **Method**: GET, POST
- **Description**: Record completed analysis
- **Required Fields**: quantity, done_date
- **Permissions**: create

#### Delete Analysis
- **URL**: `/delete-analysis/{analysis_id}`
- **Method**: GET, POST
- **Description**: Remove analysis record
- **Permissions**: edit

### Stock Management

#### Stock Overview
- **URL**: `/stock`
- **Method**: GET
- **Description**: Current inventory levels
- **Permissions**: read

#### Buy Substance
- **URL**: `/buy-substance`
- **Method**: GET, POST
- **Description**: Add substance to inventory
- **Required Fields**: substance, amount, price, date
- **Permissions**: create

#### Stock History
- **URL**: `/stock-history`
- **Method**: GET
- **Description**: Inventory transaction history
- **Permissions**: read

### Reporting

#### Statistics Form
- **URL**: `/statistic-form`
- **Method**: GET, POST
- **Description**: Generate consumption reports
- **Required Fields**: start_date, end_date
- **Permissions**: read

#### Archive Filter
- **URL**: `/archive-filter/{type_item}/{name_item}/{direction}/{start_date}/{end_date}`
- **Method**: GET
- **Description**: Filtered historical data
- **Permissions**: read

#### Aggregate Solutions
- **URL**: `/aggregate-solution`
- **Method**: GET
- **Description**: Summary of solution inventory
- **Permissions**: read

## Data Models

### Substance
```json
{
  "id": 1,
  "name": "Sodium Chloride",
  "measurement": "г"
}
```

### Normative
```json
{
  "id": 1,
  "name": "HCl 0.1M",
  "output": 1000,
  "type": "solution",
  "data": "{\"HCl\": 8.2, \"H2O\": 991.8}"
}
```

### Recipe
```json
{
  "id": 1,
  "name": "Chloride Analysis",
  "substances": "{\"AgNO3\": 5.0}",
  "solutions": "{\"HCl 0.1M\": 25.0}"
}
```

### Solution
```json
{
  "id": 1,
  "normative": "HCl 0.1M",
  "measurement": "мл",
  "amount": 1000,
  "remainder": 750,
  "price": 0.05,
  "total_cost": 50.00,
  "created_at": "2024-01-15",
  "due_date": "2024-06-15",
  "notes": "Standard preparation"
}
```

### Analysis
```json
{
  "id": 1,
  "recipe_name": "Chloride Analysis",
  "quantity": 10,
  "done_date": "2024-01-15",
  "total_cost": 25.50,
  "substances_cost": "{\"AgNO3\": 15.00}",
  "solutions_cost": "{\"HCl 0.1M\": 10.50}"
}
```

### Stock
```json
{
  "id": 1,
  "substance_name": "AgNO3",
  "measurement": "г",
  "amount": 100,
  "remainder": 85,
  "price": 3.00,
  "total_cost": 300.00,
  "creation_date": "2024-01-10",
  "notes": "Purchase from Supplier X"
}
```

## Error Handling

The application returns appropriate HTTP status codes:

- **200**: Success
- **302**: Redirect (after successful form submission)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **500**: Internal Server Error

## Security Features

### CSRF Protection
All forms include CSRF tokens for protection against cross-site request forgery attacks.

### Permission System
- **read**: View data
- **create**: Add new records
- **edit**: Modify or delete existing records

### Session Security
- Secure cookie sessions
- Configurable session timeouts
- Strong session secrets

## Usage Examples

### Creating a New Substance
1. Navigate to `/add_substance`
2. Fill in substance name and measurement unit
3. Submit form
4. Substance appears in `/substances` list

### Preparing a Solution
1. Create normative recipe at `/new-normative`
2. Navigate to `/create-solution/{normative_name}`
3. Specify amount to prepare
4. System calculates ingredient requirements
5. Solution is created and inventory updated

### Recording an Analysis
1. Create analysis recipe at `/new-recipe`
2. Navigate to `/add-analysis/{recipe_id}`
3. Enter quantity analyzed and date
4. System updates stock levels and calculates costs

### Generating Reports
1. Navigate to `/statistic-form`
2. Select date range
3. View consumption summary
4. Print or save report

This API documentation provides a comprehensive overview of the Laboratory Management System's endpoints and functionality.
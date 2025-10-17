# Development Guide

This guide helps developers understand the codebase structure, set up a development environment, and contribute to the Laboratory Management System.

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Development Setup](#development-setup)
3. [Code Structure](#code-structure)
4. [Database Design](#database-design)
5. [Frontend Components](#frontend-components)
6. [Testing Strategy](#testing-strategy)
7. [Coding Standards](#coding-standards)
8. [Contributing](#contributing)
9. [Common Development Tasks](#common-development-tasks)
10. [Troubleshooting](#troubleshooting)

## Project Architecture

The Laboratory Management System is built using the Pyramid web framework with the following architectural patterns:

### MVC Architecture
- **Models**: SQLAlchemy ORM models in `laboratory/models/`
- **Views**: Request handlers in `laboratory/views/`
- **Controllers**: URL routing in `laboratory/routes.py`
- **Templates**: Jinja2 templates in `laboratory/templates/`

### Key Technologies
- **Backend**: Python 3.10+, Pyramid, SQLAlchemy
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Frontend**: Jinja2, Bootstrap CSS, jQuery
- **Forms**: Deform form library
- **Security**: BCrypt password hashing, CSRF protection
- **Data Processing**: Pandas, NumPy for calculations

### Design Patterns
- Repository pattern for data access
- Factory pattern for object creation
- Observer pattern for event handling

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Git
- PostgreSQL (for production-like development)
- Node.js (for frontend tooling)

### Quick Setup
```bash
# Clone repository
git clone https://github.com/kivaschenko/laboratory.git
cd laboratory

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[testing,development]"

# Install pre-commit hooks
pre-commit install

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings

# Initialize database
alembic upgrade head
initialize_laboratory_db development.ini

# Run development server
pserve development.ini --reload
```

### Docker Development Setup
```bash
# Start development environment
docker-compose up -d

# Initialize database
docker-compose exec web alembic upgrade head
docker-compose exec web initialize_laboratory_db development.ini

# Access application at http://localhost:6543
```

### IDE Setup

#### VS Code
Recommended extensions:
- Python
- Pylance
- Black Formatter
- isort
- SQLAlchemy
- Jinja2

#### PyCharm
1. Open project directory
2. Configure Python interpreter to use virtual environment
3. Enable Django support (for template recognition)
4. Install SQLAlchemy plugin

## Code Structure

### Directory Layout
```
laboratory/
├── laboratory/           # Main application package
│   ├── __init__.py      # Application factory
│   ├── routes.py        # URL routing configuration
│   ├── security.py      # Authentication and authorization
│   ├── models/          # Database models
│   │   ├── __init__.py  # Model imports and database setup
│   │   ├── meta.py      # Base model and metadata
│   │   ├── user.py      # User authentication model
│   │   ├── substance.py # Chemical substance model
│   │   ├── normative.py # Solution recipe model
│   │   ├── recipe.py    # Analysis recipe model
│   │   ├── solution.py  # Prepared solution model
│   │   ├── stock.py     # Inventory tracking model
│   │   └── analysis.py  # Analysis record model
│   ├── views/           # Request handlers
│   │   ├── __init__.py
│   │   ├── auth.py      # Authentication views
│   │   ├── default.py   # Dashboard and home views
│   │   ├── substances.py # Substance management
│   │   ├── normatives.py # Normative management
│   │   ├── recipes.py   # Recipe management
│   │   ├── solutions.py # Solution management
│   │   ├── analysis.py  # Analysis management
│   │   └── statistic.py # Reporting views
│   ├── templates/       # Jinja2 templates
│   │   ├── layout.jinja2 # Base template
│   │   ├── home.jinja2   # Dashboard
│   │   ├── login.jinja2  # Authentication
│   │   └── ...          # Feature-specific templates
│   ├── static/          # Static assets
│   │   ├── theme.css    # Application styles
│   │   └── images/      # Static images
│   └── scripts/         # Command-line scripts
│       ├── __init__.py
│       ├── initialize_db.py # Database initialization
│       └── db_seed.py   # Seed data
├── alembic/             # Database migrations
├── docs/                # Documentation
├── tests/               # Test files
├── .github/             # GitHub Actions CI/CD
├── pyproject.toml       # Project configuration
├── setup.py             # Legacy setup (deprecated)
├── development.ini      # Development configuration
├── production.ini       # Production configuration
├── alembic.ini         # Alembic configuration
└── README.md           # Project documentation
```

### Models Layer

#### Base Model
```python
# laboratory/models/meta.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import MetaData

class Base(DeclarativeBase):
    metadata = metadata
```

#### Example Model
```python
# laboratory/models/substance.py
from sqlalchemy import Column, Integer, String
from .meta import Base

class Substance(Base):
    __tablename__ = 'substances'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    measurement = Column(String(10), nullable=False)
```

### Views Layer

#### View Structure
```python
# laboratory/views/substances.py
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

@view_config(
    route_name="substances",
    renderer="../templates/substances.jinja2",
    permission="read"
)
def list_substances(request):
    """Display all substances."""
    substances = request.dbsession.query(Substance).all()
    return {"substances": substances}
```

#### Form Handling
```python
import colander
import deform

class SubstanceSchema(colander.Schema):
    name = colander.SchemaNode(
        colander.String(),
        title="Substance Name",
        validator=colander.Length(min=1, max=255)
    )
    measurement = colander.SchemaNode(
        colander.String(),
        title="Measurement Unit"
    )

@view_config(route_name="add_substance", permission="create")
def add_substance(request):
    schema = SubstanceSchema()
    form = deform.Form(schema)
    
    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            # Process form data
            substance = Substance(**appstruct)
            request.dbsession.add(substance)
            return HTTPFound(location=request.route_url("substances"))
        except deform.ValidationFailure as e:
            return {"form": e.render()}
    
    return {"form": form.render()}
```

## Database Design

### Entity Relationship Diagram

```
Users
├── id (PK)
├── nickname
├── email
├── password_hash
└── role

Substances
├── id (PK)
├── name (unique)
└── measurement

Normatives
├── id (PK)
├── name
├── output
├── type
└── data (JSON)

Recipes
├── id (PK)
├── name (unique)
├── substances (JSON)
└── solutions (JSON)

Stock
├── id (PK)
├── substance_name (FK)
├── amount
├── remainder
├── price
├── creation_date
└── notes

Solutions
├── id (PK)
├── normative
├── amount
├── remainder
├── price
├── created_at
├── due_date
└── notes

Analysis
├── id (PK)
├── recipe_name (FK)
├── quantity
├── done_date
├── total_cost
├── substances_cost (JSON)
└── solutions_cost (JSON)
```

### Migration Management

#### Creating Migrations
```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add new table"

# Manual migration
alembic revision -m "Custom migration"
```

#### Migration Template
```python
"""Add new column

Revision ID: abc123
Revises: def456
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('substances', sa.Column('category', sa.String(50)))

def downgrade():
    op.drop_column('substances', 'category')
```

## Frontend Components

### Template Structure
```jinja2
<!-- laboratory/templates/layout.jinja2 -->
<!DOCTYPE html>
<html>
<head>
    <title>Laboratory Management System</title>
    <link rel="stylesheet" href="{{ request.static_url('laboratory:static/theme.css') }}">
</head>
<body>
    <nav class="navbar">
        <!-- Navigation menu -->
    </nav>
    
    <main class="content">
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <!-- Footer content -->
    </footer>
</body>
</html>
```

### Form Templates
```jinja2
<!-- laboratory/templates/add_substance.jinja2 -->
{% extends 'layout.jinja2' %}

{% block content %}
<div class="container">
    <h1>Add New Substance</h1>
    
    {% if message %}
        <div class="alert alert-info">{{ message }}</div>
    {% endif %}
    
    {{ form.render()|safe }}
</div>
{% endblock %}
```

### CSS Framework
The application uses Bootstrap CSS framework with custom overrides in `theme.css`.

## Testing Strategy

### Test Structure
```python
# laboratory/tests.py
import unittest
from pyramid import testing
from pyramid.paster import get_appsettings
from sqlalchemy import create_engine

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        
    def tearDown(self):
        testing.tearDown()
        
    def test_home_view(self):
        from laboratory.views.default import home_view
        request = testing.DummyRequest()
        response = home_view(request)
        self.assertEqual(response['title'], 'Laboratory Management')
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=laboratory

# Run specific test
pytest laboratory/tests.py::ViewTests::test_home_view

# Run tests in Docker
docker-compose exec web pytest
```

### Test Data
```python
# tests/factories.py
import factory
from laboratory.models import Substance

class SubstanceFactory(factory.Factory):
    class Meta:
        model = Substance
    
    name = factory.Sequence(lambda n: f"Substance {n}")
    measurement = "г"
```

## Coding Standards

### Python Style Guide
- Follow PEP 8
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints where possible

### Code Quality Tools
```bash
# Format code
black laboratory/

# Sort imports
isort laboratory/

# Check style
flake8 laboratory/

# Type checking
mypy laboratory/

# Security check
bandit -r laboratory/
```

### Documentation Standards
- All public functions must have docstrings
- Use Google-style docstrings
- Include type hints in function signatures
- Document complex algorithms

### Example Documentation
```python
def calculate_solution_cost(
    substances: Dict[str, float],
    prices: Dict[str, float]
) -> float:
    """Calculate total cost of solution preparation.
    
    Args:
        substances: Dictionary mapping substance names to quantities
        prices: Dictionary mapping substance names to unit prices
        
    Returns:
        Total cost of all substances used
        
    Raises:
        KeyError: If substance price not found
        ValueError: If quantity is negative
        
    Example:
        >>> substances = {"NaCl": 100, "H2O": 900}
        >>> prices = {"NaCl": 0.01, "H2O": 0.001}
        >>> calculate_solution_cost(substances, prices)
        1.9
    """
    total_cost = 0.0
    for substance, quantity in substances.items():
        if quantity < 0:
            raise ValueError(f"Negative quantity for {substance}")
        if substance not in prices:
            raise KeyError(f"Price not found for {substance}")
        total_cost += quantity * prices[substance]
    return total_cost
```

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes following coding standards
4. Add tests for new functionality
5. Run test suite: `pytest`
6. Run code quality checks: `pre-commit run --all-files`
7. Commit changes: `git commit -m "Add new feature"`
8. Push to branch: `git push origin feature/new-feature`
9. Create pull request

### Commit Message Format
```
type(scope): description

body

footer
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(substances): add substance categorization

Add ability to categorize substances by type (acid, base, salt, etc.)
for better organization and filtering.

Closes #123
```

### Pull Request Guidelines
- Include clear description of changes
- Link to related issues
- Ensure all tests pass
- Include screenshots for UI changes
- Update documentation if needed

## Common Development Tasks

### Adding a New Model
1. Create model file in `laboratory/models/`
2. Add import to `laboratory/models/__init__.py`
3. Create migration: `alembic revision --autogenerate -m "Add model"`
4. Apply migration: `alembic upgrade head`
5. Add views and templates
6. Write tests

### Adding a New View
1. Create view function in appropriate views module
2. Add route configuration in `routes.py`
3. Create template file
4. Add navigation link if needed
5. Write unit tests
6. Update documentation

### Modifying Database Schema
1. Modify model definition
2. Generate migration: `alembic revision --autogenerate -m "Modify schema"`
3. Review and edit migration file if needed
4. Test migration on development database
5. Apply migration: `alembic upgrade head`

### Adding New Dependencies
1. Add to `pyproject.toml` dependencies
2. Install in development: `pip install -e ".[testing,development]"`
3. Update Docker images if needed
4. Test installation in clean environment

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database status
sudo systemctl status postgresql

# Check connection string
echo $SQLALCHEMY_URL

# Test connection
psql $SQLALCHEMY_URL
```

#### Migration Errors
```bash
# Check current migration
alembic current

# Check migration history
alembic history

# Reset to specific revision
alembic downgrade <revision>
```

#### Permission Errors
```bash
# Check file permissions
ls -la laboratory/

# Fix permissions
chmod -R 755 laboratory/
```

#### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install package in development mode
pip install -e .
```

### Debug Mode
```python
# Enable debugging in views
import pdb; pdb.set_trace()

# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Performance Profiling
```python
# Profile database queries
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    print(f"Query: {statement[:50]}... Time: {total:.4f}s")
```

This development guide provides comprehensive information for contributing to and maintaining the Laboratory Management System. Follow these guidelines to ensure consistent, high-quality code.
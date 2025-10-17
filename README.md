# Laboratory Management System

A comprehensive web application designed to streamline laboratory operations in feed plants, enabling efficient management of substances, solutions, recipes, and analytical procedures.

## 🧪 About

This project was developed as a practical solution for a small laboratory in a feed plant to help laboratory technicians manage their daily operations more efficiently. The system provides a complete workflow for:

- **Substance Management**: Track chemical substances, their quantities, and stock levels
- **Recipe Management**: Create and manage analytical procedures and solution recipes
- **Solution Preparation**: Calculate ingredient requirements and costs for solution preparation
- **Analysis Tracking**: Record performed analyses and their associated costs
- **Inventory Control**: Monitor stock levels and purchase requirements
- **Cost Analysis**: Generate reports on substance consumption and costs

## ✨ Features

### Core Functionality
- **Substance Catalog**: Maintain a database of chemical substances with measurements and properties
- **Recipe Builder**: Create detailed recipes for analytical procedures including required substances and solutions
- **Solution Maker**: Automated calculation of ingredient quantities based on desired output amounts
- **Analysis Logger**: Record completed analyses with date, quantity, and cost tracking
- **Stock Management**: Real-time inventory tracking with automatic calculations
- **Cost Reporting**: Detailed cost analysis and consumption reports

### User Management
- **Role-based Access**: Different permission levels (read, create, edit)
- **Secure Authentication**: Password-protected user accounts
- **Session Management**: Secure user sessions

### Reporting & Analytics
- **Consumption Reports**: Track substance usage over time periods
- **Cost Analysis**: Calculate total costs for analyses and solutions
- **Stock Reports**: Current inventory levels and purchase requirements
- **Print-friendly Reports**: Optimized layouts for documentation

## 🛠️ Technical Stack

- **Backend**: Python 3.10+ with Pyramid web framework
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **ORM**: SQLAlchemy with Alembic migrations
- **Frontend**: Jinja2 templates with Bootstrap CSS
- **Forms**: Deform for form handling and validation
- **Data Processing**: Pandas and NumPy for calculations
- **Visualization**: Bokeh for charts and graphs
- **Security**: BCrypt for password hashing

## 📋 Requirements

- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/kivaschenko/laboratory.git
cd laboratory
```

### 2. Create Virtual Environment
```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip setuptools
pip install -e ".[testing]"
```

### 4. Database Setup
```bash
# Generate initial migration
env/bin/alembic -c development.ini revision --autogenerate -m "init"

# Apply migrations
env/bin/alembic -c development.ini upgrade head

# Load sample data
env/bin/initialize_laboratory_db development.ini
```

### 5. Run the Application
```bash
env/bin/pserve development.ini
```

The application will be available at `http://localhost:6543`

## 📖 Usage

### Default Login
- **Username**: oksana
- **Password**: Teodor235813
- **Role**: editor (full access)

### Basic Workflow

1. **Setup Substances**: Add chemical substances to the catalog with their measurements
2. **Create Normatives**: Define standard solution recipes with ingredient ratios
3. **Build Analysis Recipes**: Create recipes that combine substances and solutions for specific analyses
4. **Perform Analyses**: Record completed analyses, automatically updating stock levels
5. **Prepare Solutions**: Create solutions following normative recipes
6. **Monitor Stock**: Track inventory levels and costs
7. **Generate Reports**: View consumption and cost reports

### Key Screens

- **Home Dashboard**: Overview of recent activities and quick navigation
- **Substances**: Manage chemical substance catalog
- **Normatives**: Define solution recipes and mixing procedures
- **Recipes**: Create analysis procedures combining multiple ingredients
- **Stock**: Monitor inventory levels and purchase history
- **Solutions**: Track prepared solutions and their usage
- **Analysis**: Record completed analytical work
- **Reports**: Generate consumption and cost analysis

## 🐳 Docker Deployment

### Development with Docker
```bash
# Build and run with Docker
docker build -t laboratory .
docker run -p 6543:6543 laboratory
```

### Production with Docker Compose
```bash
# Using PostgreSQL database
docker-compose up -d
```

## 🧪 Testing

Run the test suite:
```bash
env/bin/pytest
```

Run tests with coverage:
```bash
env/bin/pytest --cov=laboratory
```

## 📊 Database Schema

The application uses the following main entities:

- **Users**: Authentication and role management
- **Substances**: Chemical substance catalog
- **Normatives**: Standard solution recipes
- **Recipes**: Analysis procedure definitions
- **Stock**: Inventory tracking with history
- **Solutions**: Prepared solution records
- **Analysis**: Completed analysis records

## 🔧 Configuration

### Environment Variables

Key configuration options:

- `SQLALCHEMY_URL`: Database connection string
- `AUTH_SECRET`: Session encryption key
- `PYRAMID_DEBUG`: Enable debug mode
- `PYRAMID_RELOAD_TEMPLATES`: Auto-reload templates in development

### Database Configuration

Development (SQLite):
```ini
sqlalchemy.url = sqlite:///%(here)s/laboratory.sqlite
```

Production (PostgreSQL):
```ini
sqlalchemy.url = postgresql://user:password@localhost:5432/laboratory
```

## 📝 API Documentation

The application provides a web interface for all operations. Key endpoints include:

- `/` - Dashboard
- `/substances` - Substance management
- `/normatives` - Solution recipes
- `/recipes` - Analysis procedures
- `/stock` - Inventory management
- `/solutions` - Solution tracking
- `/analysis` - Analysis records

## 🤝 Contributing

This project was created as a practical solution for a specific laboratory environment. Contributions are welcome for:

- Bug fixes and improvements
- Additional features for laboratory management
- Better documentation and examples
- Test coverage improvements
- Performance optimizations

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built for laboratory technicians who needed a practical solution for daily operations
- Developed with feedback from real laboratory workflows
- Thanks to the Pyramid framework community for excellent documentation

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Review the documentation in the `docs/` directory
- Check the example configurations in the `examples/` directory

---

*This system has been successfully used in production environment for managing laboratory operations, proving its reliability and usefulness for small to medium-sized laboratory facilities.*
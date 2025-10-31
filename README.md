# 🧪 Laboratory Management System

<div align="center">

![Dashboard](screenshots/dashboard.png)

*A comprehensive web application designed to streamline laboratory operations in feed plants*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Pyramid Framework](https://img.shields.io/badge/framework-Pyramid-red.svg)](https://trypyramid.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

</div>

## 🎯 About This Project

This Laboratory Management System was developed as a **real-world solution** for a small laboratory in a feed plant to help laboratory technicians manage their daily operations more efficiently. The system provides a complete workflow for managing chemical substances, preparing solutions, recording analyses, and generating comprehensive reports.

**🏆 Portfolio Highlight**: This project demonstrates practical problem-solving skills, having been successfully deployed and used in a production environment to solve actual business challenges.

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🧪 **Laboratory Operations**
- **Substance Catalog Management**
- **Recipe Builder for Analysis Procedures** 
- **Solution Preparation with Auto-Calculations**
- **Analysis Recording with Cost Tracking**
- **Comprehensive Reporting & Analytics**

</td>
<td width="50%">

### 🔒 **Professional Standards**
- **Role-based Access Control**
- **Secure Authentication System**
- **Real-time Inventory Tracking**
- **Cost Analysis & Reporting**
- **Print-ready Documentation**

</td>
</tr>
</table>

## 📸 Application Screenshots

### 🏠 Dashboard & Navigation
<table>
<tr>
<td align="center" width="50%">
<img src="screenshots/dashboard.png" width="400" alt="Main Dashboard"/>
<br><b>Main Dashboard</b><br>
<em>Overview of laboratory operations</em>
</td>
<td align="center" width="50%">
<img src="screenshots/substances-list.png" width="400" alt="Substances Management"/>
<br><b>Substances Catalog</b><br>
<em>Chemical substances inventory</em>
</td>
</tr>
</table>

### 🧪 Laboratory Workflow
<table>
<tr>
<td align="center" width="33%">
<img src="screenshots/add-substance.png" width="300" alt="Add Substance"/>
<br><b>Add Substance</b><br>
<em>Simple substance registration</em>
</td>
<td align="center" width="33%">
<img src="screenshots/normatives-list.png" width="300" alt="Solution Recipes"/>
<br><b>Solution Recipes</b><br>
<em>Standardized preparation procedures</em>
</td>
<td align="center" width="33%">
<img src="screenshots/create-solution.png" width="300" alt="Solution Creation"/>
<br><b>Solution Preparation</b><br>
<em>Automated ingredient calculations</em>
</td>
</tr>
</table>

### 📋 Analysis & Recipes
<table>
<tr>
<td align="center" width="50%">
<img src="screenshots/recipes-list.png" width="400" alt="Analysis Recipes"/>
<br><b>Analysis Recipes</b><br>
<em>Complete procedure definitions</em>
</td>
<td align="center" width="50%">
<img src="screenshots/recipe-details.png" width="400" alt="Recipe Details"/>
<br><b>Recipe Details</b><br>
<em>Detailed ingredient specifications</em>
</td>
</tr>
</table>

### 📊 Inventory Management
<table>
<tr>
<td align="center" width="33%">
<img src="screenshots/stock-management.png" width="300" alt="Stock Management"/>
<br><b>Stock Management</b><br>
<em>Real-time inventory tracking</em>
</td>
<td align="center" width="33%">
<img src="screenshots/stock-journal.png" width="300" alt="Stock Journal"/>
<br><b>Stock Journal</b><br>
<em>Complete transaction history</em>
</td>
<td align="center" width="33%">
<img src="screenshots/solutions-inventory.png" width="300" alt="Solutions Inventory"/>
<br><b>Solutions Inventory</b><br>
<em>Prepared solutions tracking</em>
</td>
</tr>
</table>

### 📈 Analytics & Reporting
<table>
<tr>
<td align="center" width="33%">
<img src="screenshots/reports.png" width="300" alt="Reports Interface"/>
<br><b>Reports Dashboard</b><br>
<em>Comprehensive analytics</em>
</td>
<td align="center" width="33%">
<img src="screenshots/report-diagramm-cost.png" width="300" alt="Cost Distribution"/>
<br><b>Cost Analysis</b><br>
<em>Substance cost distribution</em>
</td>
<td align="center" width="33%">
<img src="screenshots/report-histagram-numer-analysis-by-recipe.png" width="300" alt="Analysis Frequency"/>
<br><b>Analysis Frequency</b><br>
<em>Usage statistics by recipe</em>
</td>
</tr>
</table>

### 📋 Operational Journals
<table>
<tr>
<td align="center" width="50%">
<img src="screenshots/analysis-journal.png" width="400" alt="Analysis Journal"/>
<br><b>Analysis Journal</b><br>
<em>Complete analysis records</em>
</td>
<td align="center" width="50%">
<img src="screenshots/solutions-journal.png" width="400" alt="Solutions Journal"/>
<br><b>Solutions Journal</b><br>
<em>Solution preparation history</em>
</td>
</tr>
</table>

### � Technology Stack

<table>
<tr>
<td width="50%">

### **Backend Technologies**
- **🐍 Python 3.10+** - Modern Python with type hints
- **🏔️ Pyramid Framework** - Lightweight, flexible web framework
- **🗃️ SQLAlchemy** - Powerful ORM for database operations
- **🐘 PostgreSQL / SQLite** - Production & development databases
- **🔄 Alembic** - Database migration management

</td>
<td width="50%">

### **Frontend & Visualization**
- **🎨 Jinja2 Templates** - Server-side rendered UI
- **🎯 Bootstrap CSS** - Responsive design framework
- **📊 Bokeh 3.4.3** - Interactive data visualization
- **📈 Pandas & NumPy** - Data analysis and processing
- **📱 Responsive Design** - Mobile-friendly interface

</td>
</tr>
</table>

### **DevOps & Quality**
- **🐳 Docker & Docker Compose** - Containerized deployment
- **🔄 GitHub Actions CI/CD** - Automated testing and deployment
- **🔍 Pre-commit Hooks** - Code quality enforcement (Black, flake8, mypy)
- **🧪 Pytest** - Comprehensive testing framework
- **📋 Type Hints** - Enhanced code reliability

## 🛠️ Quick Start

### Prerequisites
- **Python 3.10+**
- **Docker & Docker Compose** (optional, recommended)
- **Git**

### 🐳 Docker Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd laboratory

# Start with Docker Compose
docker-compose up -d

# Initialize the database
docker-compose exec web python -m laboratory.scripts.initialize_db development.ini

# Access the application
open http://localhost:6543
```

### 🐍 Local Development Setup

```bash
# Clone and enter directory
git clone <repository-url>
cd laboratory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,testing]"

# Initialize database
python -m laboratory.scripts.initialize_db development.ini

# Run the application
pserve development.ini --reload

# Visit http://localhost:6543
```

### 🎯 Demo Data Setup

```bash
# Load sample data for testing
python -m laboratory.scripts.db_seed development.ini
```

## 📚 Documentation

<table>
<tr>
<td width="50%">

### **📖 User Guides**
- **[🖼️ Visual Guide](docs/VISUAL_GUIDE.md)** - Complete UI walkthrough with screenshots
- **[✨ Features Overview](docs/FEATURES.md)** - Detailed feature explanations
- **[🚀 Quick Start Guide](#-quick-start)** - Get running in minutes

</td>
<td width="50%">

### **👨‍💻 Technical Docs**
- **[🏗️ Deployment Guide](docs/DEPLOYMENT.md)** - Production setup instructions
- **[⚙️ Development Guide](docs/DEVELOPMENT.md)** - Contributing guidelines
- **[🔌 API Documentation](docs/API.md)** - REST endpoints reference

</td>
</tr>
</table>

## 🧪 Testing

The project includes comprehensive testing coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=laboratory

# Run specific test categories
pytest laboratory/tests.py -v
```

## 🔒 Security Features

- **🛡️ Password hashing** with secure bcrypt
- **🔐 Session management** with CSRF protection
- **👥 Role-based access control** (read/create/edit permissions)
- **🔍 Input validation** and SQL injection prevention
- **📝 Audit logging** for all critical operations

## 💼 Production Deployment

The application is production-ready with:

- **🐳 Multi-stage Docker builds** for optimized containers
- **🏗️ CI/CD pipeline** with automated testing and security scanning
- **📊 Health checks** and monitoring endpoints
- **🔄 Database migrations** with Alembic
- **📈 Performance optimizations** for large datasets

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the coding standards
4. **Run tests**: `pytest`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

See [Development Guide](docs/DEVELOPMENT.md) for detailed contributing guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Real-world testing** by laboratory technicians in feed plant operations
- **Pyramid framework** for providing a solid foundation
- **SQLAlchemy** for powerful ORM capabilities
- **Bokeh community** for excellent data visualization tools

---

<div align="center">

**⭐ Star this repository if you found it helpful!**

Made with ❤️ for laboratory professionals

</div>

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
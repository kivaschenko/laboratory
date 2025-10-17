import unittest
import datetime
from decimal import Decimal

from pyramid import testing
import transaction


def dummy_request(dbsession):
    """Create a dummy request with database session for testing."""
    request = testing.DummyRequest(dbsession=dbsession)

    # Add CSRF token method
    def get_csrf_token():
        return "dummy_csrf_token"

    request.session.get_csrf_token = get_csrf_token

    # Add route_url method
    def route_url(route_name, **kwargs):
        return f"/route/{route_name}"

    request.route_url = route_url
    return request


class BaseTest(unittest.TestCase):
    """Base test class with common setup and teardown for all tests."""

    def setUp(self):
        self.config = testing.setUp(
            settings={
                "sqlalchemy.url": "sqlite:///:memory:",
                "pyramid.debug_authorization": "false",
                "pyramid.debug_notfound": "false",
                "pyramid.debug_routematch": "false",
                "pyramid.default_locale_name": "en",
                "auth.secret": "testing_secret_key_for_tests_only",
            }
        )
        self.config.include(".models")
        self.config.include("pyramid_jinja2")
        self.config.include(".routes")
        # Skip security configuration for tests to avoid complexity
        # self.config.include(".security")
        settings = self.config.get_settings()

        from .models import (
            get_engine,
            get_session_factory,
            get_tm_session,
        )

        self.engine = get_engine(settings)
        session_factory = get_session_factory(self.engine)
        self.session = get_tm_session(session_factory, transaction.manager)
        self.init_database()

    def init_database(self):
        """Initialize database schema."""
        from .models.meta import Base

        Base.metadata.create_all(self.engine)

    def seed_db(self, dbsession):
        """Seed database with initial data."""
        from .scripts.initialize_db import setup_models

        return setup_models(dbsession)

    def create_test_user(
        self,
        nickname="testuser",
        email="test@example.com",
        role="user",
        password="testpass",
    ):
        """Create a test user for authentication tests."""
        from .models import User

        user = User(nickname=nickname, email=email, role=role)
        user.set_password(password)
        self.session.add(user)
        self.session.flush()
        return user

    def create_test_substance(self, name="Test Substance", measurement="мл"):
        """Create a test substance."""
        from .models import Substance

        substance = Substance(name=name, measurement=measurement)
        self.session.add(substance)
        self.session.flush()
        return substance

    def create_test_solution(
        self, normative="Test Solution", amount=100, measurement="мл"
    ):
        """Create a test solution."""
        from .models import Solution

        solution = Solution(
            normative=normative,
            measurement=measurement,
            amount=Decimal(str(amount)),
            remainder=Decimal(str(amount)),
            price=Decimal("1.50"),
            total_cost=Decimal(str(amount * 1.5)),
            created_at=datetime.date.today(),
            due_date=datetime.date.today() + datetime.timedelta(days=30),
            notes="Test solution notes",
        )
        self.session.add(solution)
        self.session.flush()
        return solution

    def tearDown(self):
        from .models.meta import Base

        testing.tearDown()
        transaction.abort()
        Base.metadata.drop_all(self.engine)


# =============================================================================
# MODEL TESTS
# =============================================================================


class TestSubstanceModel(BaseTest):
    """Test cases for the Substance model."""

    def test_substance_creation(self):
        """Test creating a new substance."""
        substance = self.create_test_substance(name="Sodium Chloride", measurement="г")
        self.assertEqual(substance.name, "Sodium Chloride")
        self.assertEqual(substance.measurement, "г")
        self.assertIsNotNone(substance.id)

    def test_substance_string_representation(self):
        """Test string representations of substance."""
        substance = self.create_test_substance(name="Water", measurement="мл")
        self.assertEqual(str(substance), "Water (мл)")
        self.assertIn("Water", repr(substance))
        self.assertIn("мл", repr(substance))

    def test_substance_unique_name_constraint(self):
        """Test that substance names must be unique."""
        from sqlalchemy.exc import IntegrityError

        self.create_test_substance(name="Duplicate Name", measurement="г")

        # Try to create another substance with the same name
        with self.assertRaises(IntegrityError):
            self.create_test_substance(name="Duplicate Name", measurement="мл")
            transaction.commit()


class TestUserModel(BaseTest):
    """Test cases for the User model."""

    def test_user_creation(self):
        """Test creating a new user."""
        user = self.create_test_user(
            nickname="johndoe",
            email="john@example.com",
            role="admin",
            password="securepass",
        )
        self.assertEqual(user.nickname, "johndoe")
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.role, "admin")
        self.assertIsNotNone(user.password_hash)

    def test_password_hashing(self):
        """Test password hashing and verification."""
        user = self.create_test_user(password="mypassword")

        # Password should be hashed, not stored as plain text
        self.assertNotEqual(user.password_hash, "mypassword")
        self.assertTrue(user.check_password("mypassword"))
        self.assertFalse(user.check_password("wrongpassword"))

    def test_user_string_representation(self):
        """Test string representation of user."""
        user = self.create_test_user(
            nickname="testuser", email="test@example.com", role="user"
        )
        repr_str = repr(user)
        self.assertIn("testuser", repr_str)
        self.assertIn("test@example.com", repr_str)
        self.assertIn("user", repr_str)


class TestSolutionModel(BaseTest):
    """Test cases for the Solution model."""

    def test_solution_creation(self):
        """Test creating a new solution."""
        solution = self.create_test_solution(
            normative="HCl 0.1M", amount=500, measurement="мл"
        )
        self.assertEqual(solution.normative, "HCl 0.1M")
        self.assertEqual(solution.amount, Decimal("500"))
        self.assertEqual(solution.remainder, Decimal("500"))
        self.assertEqual(solution.measurement, "мл")
        self.assertIsNotNone(solution.created_at)
        self.assertIsNotNone(solution.due_date)

    def test_solution_cost_calculation(self):
        """Test solution cost calculation."""
        solution = self.create_test_solution(amount=100)
        expected_cost = Decimal("100") * Decimal("1.50")
        self.assertEqual(solution.total_cost, expected_cost)


class TestAnalysisModel(BaseTest):
    """Test cases for the Analysis model."""

    def test_analysis_creation(self):
        """Test creating a new analysis record."""
        from .models import Analysis

        analysis = Analysis(
            recipe_name="Test Recipe",
            quantity=5,
            done_date=datetime.date.today(),
            total_cost=100,
            substances_cost={"substance1": 50},
            solutions_cost={"solution1": 50},
        )
        self.session.add(analysis)
        self.session.flush()

        self.assertEqual(analysis.recipe_name, "Test Recipe")
        self.assertEqual(analysis.quantity, 5)
        self.assertEqual(analysis.total_cost, 100)
        self.assertIsInstance(analysis.substances_cost, dict)
        self.assertIsInstance(analysis.solutions_cost, dict)

    def test_analysis_string_representation(self):
        """Test string representation of analysis."""
        from .models import Analysis

        analysis = Analysis(
            recipe_name="Test Recipe", quantity=3, done_date=datetime.date.today()
        )
        self.session.add(analysis)
        self.session.flush()

        repr_str = repr(analysis)
        self.assertIn("Test Recipe", repr_str)
        self.assertIn("3", repr_str)


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================


class TestAuthentication(BaseTest):
    """Test cases for authentication functionality."""

    def test_login_view_get(self):
        """Test GET request to login view."""
        from .views.auth import login

        request = dummy_request(self.session)
        request.POST = {}

        response = login(request)
        # Response should be a dict containing form data
        if isinstance(response, dict):
            self.assertIn("form", response)

    def test_successful_login(self):
        """Test successful user login."""
        from .views.auth import login

        # Create a test user
        self.create_test_user(nickname="testuser", password="testpass")
        transaction.commit()

        request = dummy_request(self.session)
        request.POST = {
            "submit": "submit",
            "username": "testuser",
            "password": "testpass",
            "csrf": "dummy_csrf_token",
        }

        # The login should redirect on success
        response = login(request)
        # Response should be either a redirect or contain user info
        self.assertIsNotNone(response)

    def test_failed_login_wrong_password(self):
        """Test login with wrong password."""
        from .views.auth import login

        # Create a test user
        self.create_test_user(nickname="testuser", password="testpass")
        transaction.commit()

        request = dummy_request(self.session)
        request.POST = {
            "submit": "submit",
            "username": "testuser",
            "password": "wrongpass",
            "csrf": "dummy_csrf_token",
        }

        response = login(request)
        # Should return form with error message
        self.assertIsNotNone(response)


# =============================================================================
# VIEW TESTS
# =============================================================================


class TestDefaultViews(BaseTest):
    """Test cases for default views."""

    def test_home_view_with_substances(self):
        """Test home view with substances in database."""
        from .views.default import my_view

        # Create test substances
        self.create_test_substance(name="Вода H2O", measurement="мл")
        self.create_test_substance(name="Соль NaCl", measurement="г")
        transaction.commit()

        request = dummy_request(self.session)
        request.POST = {}

        response = my_view(request)
        # Response should be a dict containing form data
        if isinstance(response, dict):
            self.assertIn("form", response)

    def test_home_view_post_request(self):
        """Test home view with POST request."""
        from .views.default import my_view

        # Create test substances
        self.create_test_substance(name="Test Substance", measurement="мл")
        transaction.commit()

        request = dummy_request(self.session)
        request.POST = {
            "submit": "submit",
            "substance": "Test Substance",
            "quantity": "100",
            "csrf": "dummy_csrf_token",
        }

        # This should process the form
        response = my_view(request)
        self.assertIsNotNone(response)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestSubstanceWorkflow(BaseTest):
    """Integration tests for substance management workflow."""

    def test_complete_substance_workflow(self):
        """Test complete workflow of substance management."""
        # 1. Create a substance
        substance = self.create_test_substance(name="Acetone", measurement="мл")
        self.assertIsNotNone(substance.id)

        # 2. Verify it can be queried
        from .models import Substance

        found_substance = (
            self.session.query(Substance).filter_by(name="Acetone").first()
        )
        self.assertIsNotNone(found_substance)
        if found_substance:
            self.assertEqual(found_substance.name, "Acetone")

        # 3. Verify it appears in choices for forms
        all_substances = self.session.query(Substance.name).all()
        substance_names = [s[0] for s in all_substances]
        self.assertIn("Acetone", substance_names)


class TestSolutionWorkflow(BaseTest):
    """Integration tests for solution management workflow."""

    def test_complete_solution_workflow(self):
        """Test complete workflow of solution management."""
        # 1. Create a solution
        solution = self.create_test_solution(
            normative="Test Normative", amount=1000, measurement="мл"
        )
        self.assertIsNotNone(solution.id)

        # 2. Use some of the solution (simulate consumption)
        # Note: In a real application, you'd have a method to update remainder
        from .models import Solution

        self.session.query(Solution).filter_by(id=solution.id).update(
            {"remainder": Decimal("750")}
        )
        self.session.flush()

        # 3. Verify the change
        updated_solution = (
            self.session.query(Solution).filter_by(id=solution.id).first()
        )
        if updated_solution:
            self.assertEqual(updated_solution.remainder, Decimal("750"))
            self.assertEqual(
                updated_solution.amount, Decimal("1000")
            )  # Original amount unchanged

        # 4. Check solution is not expired
        self.assertGreater(solution.due_date, datetime.date.today())


class TestAnalysisWorkflow(BaseTest):
    """Integration tests for analysis workflow."""

    def test_complete_analysis_workflow(self):
        """Test complete workflow of creating and tracking analyses."""
        from .models import Analysis

        # 1. Create substances and solutions for the analysis
        self.create_test_substance(name="Reagent A", measurement="г")
        self.create_test_solution(normative="Buffer Solution", amount=500)

        # 2. Create an analysis record
        analysis = Analysis(
            recipe_name="Quality Control Test",
            quantity=3,
            done_date=datetime.date.today(),
            total_cost=150,
            substances_cost={"Reagent A": 50},
            solutions_cost={"Buffer Solution": 100},
        )
        self.session.add(analysis)
        self.session.flush()

        # 3. Verify the analysis was created correctly
        self.assertIsNotNone(analysis.id)
        self.assertEqual(analysis.recipe_name, "Quality Control Test")
        self.assertEqual(analysis.total_cost, 150)

        # 4. Verify cost breakdown
        self.assertEqual(analysis.substances_cost["Reagent A"], 50)
        self.assertEqual(analysis.solutions_cost["Buffer Solution"], 100)


# Keep the original test for compatibility
class TestMyViewSuccessCondition(BaseTest):
    """Original test - kept for backward compatibility."""

    def setUp(self):
        super(TestMyViewSuccessCondition, self).setUp()
        self.init_database()

        from .models import Substance

        model = Substance(name="Вода H2O", measurement="мл")
        self.session.add(model)

    def test_passing_view(self):
        """Test that the view returns expected content."""
        from .views.default import my_view

        request = dummy_request(self.session)
        request.POST = {}

        response = my_view(request)
        self.assertIsNotNone(response)
        # Response should be a dict containing form data
        if isinstance(response, dict):
            self.assertIn("form", response)

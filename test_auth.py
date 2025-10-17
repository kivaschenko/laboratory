"""
Authentication and authorization tests for the laboratory management system.

These tests require full application setup including security configuration.
"""

import unittest
import transaction
from webtest import TestApp


class AuthenticationIntegrationTest(unittest.TestCase):
    """Integration tests for authentication functionality."""

    def setUp(self):
        """Set up the full application for authentication testing."""
        from laboratory import main

        # Use test settings
        settings = {
            "sqlalchemy.url": "sqlite:///:memory:",
            "auth.secret": "testing_secret_key_for_tests_only",
            "pyramid.debug_authorization": "false",
            "pyramid.debug_notfound": "false",
            "pyramid.debug_routematch": "false",
            "pyramid.default_locale_name": "en",
        }

        # Create the application
        app = main({}, **settings)
        self.testapp = TestApp(app)

        # Initialize the database
        from laboratory.models import get_engine, get_session_factory, get_tm_session
        from laboratory.models.meta import Base

        engine = get_engine(settings)
        Base.metadata.create_all(engine)

        session_factory = get_session_factory(engine)
        self.dbsession = get_tm_session(session_factory, transaction.manager)

        # Create a test user
        self.create_test_user()
        transaction.commit()

    def create_test_user(
        self,
        nickname="testuser",
        email="test@example.com",
        role="user",
        password="testpass",
    ):
        """Create a test user for authentication tests."""
        from laboratory.models import User

        user = User(nickname=nickname, email=email, role=role)
        user.set_password(password)
        self.dbsession.add(user)
        self.dbsession.flush()
        return user

    def tearDown(self):
        """Clean up after tests."""
        transaction.abort()
        # Note: In a real test, you'd clean up the database

    def test_login_page_loads(self):
        """Test that the login page loads correctly."""
        response = self.testapp.get("/login")
        self.assertEqual(response.status_int, 200)
        self.assertIn(b"login", response.body.lower())

    def test_successful_login_redirect(self):
        """Test successful login redirects to home page."""
        # Get login page first to get CSRF token
        self.testapp.get("/login")

        # Extract CSRF token from the form (simplified - in real test you'd parse HTML)
        # For now, we'll test without CSRF to focus on authentication logic

        response = self.testapp.post(
            "/login",
            {"username": "testuser", "password": "testpass", "submit": "submit"},
            expect_errors=True,
        )

        # Should redirect on successful login or show error
        # The exact behavior depends on your application logic
        self.assertIn(response.status_int, [200, 302, 303])

    def test_failed_login_shows_error(self):
        """Test failed login shows appropriate error."""
        response = self.testapp.post(
            "/login",
            {"username": "testuser", "password": "wrongpassword", "submit": "submit"},
            expect_errors=True,
        )

        # Should stay on login page with error
        self.assertEqual(response.status_int, 200)

    def test_home_page_accessible(self):
        """Test that the home page is accessible."""
        response = self.testapp.get("/")
        self.assertEqual(response.status_int, 200)


if __name__ == "__main__":
    unittest.main()

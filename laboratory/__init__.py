import os
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory


def get_session_factory(settings):
    """Create session factory with configurable secret."""
    secret = settings.get("auth.secret") or os.environ.get("AUTH_SECRET")
    if not secret:
        raise ValueError(
            "Session secret must be provided via auth.secret setting or AUTH_SECRET environment variable"
        )
    return SignedCookieSessionFactory(secret)


def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""
    session_factory = get_session_factory(settings)

    with Configurator(settings=settings, session_factory=session_factory) as config:
        config.include(".models")
        config.include("pyramid_jinja2")
        config.include(".routes")
        config.include(".security")
        config.add_static_view(
            name="static", path="laboratory:static", cache_max_age=3600
        )
        config.add_static_view("deform_static", "deform:static/")
        config.scan()
    return config.make_wsgi_app()

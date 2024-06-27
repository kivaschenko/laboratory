from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory

my_session_factory = SignedCookieSessionFactory('Axndun57ngkd9kfol')

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings, 
    				  session_factory=my_session_factory) as config:
        config.include('.models')
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.include('.security')
        config.add_static_view(name="static", path="laboratory:static", cache_max_age=3600)
        config.add_static_view('deform_static', 'deform:static/')
        config.scan()
    return config.make_wsgi_app()

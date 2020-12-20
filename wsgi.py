# Adapted from PServeCommand.run in site-packages/pyramid/scripts/pserve.py
from pyramid.scripts.common import get_config_loader
app_name    = 'main'
config_vars = {}
config_uri  = 'production.ini'

loader = get_config_loader(config_uri)
loader.setup_logging(config_vars)
app = loader.get_wsgi_app(app_name, config_vars)
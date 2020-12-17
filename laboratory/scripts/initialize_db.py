import argparse
import sys
import json
from pyramid.paster import bootstrap, setup_logging
from sqlalchemy.exc import OperationalError

from .. import models
from .db_seed import substances, normatives

def setup_models(dbsession):
    """Add or update models / fixtures in the database.
    """
    for subst in substances:
        new_subst = models.substance.Substance(name = subst[0], measurement = subst[1])
        dbsession.add(new_subst)
    for norm in normatives:
        new_normative = models.normative.Normative(
            name=norm[0],
            output=norm[1],
            data=json.dumps(norm[2])
        )
        dbsession.add(new_normative)
    oksana = models.user.User(nickname='oksana', role='editor', email='o.v.ivaschenko@gmail.com')
    oksana.set_password('Teodor235813')
    dbsession.add(oksana)


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('config_uri', 
                        help='Configuration file, e.g., development.ini',)
    return parser.parse_args(argv[1:])


def main(argv=sys.argv):
    args = parse_args(argv)
    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)
    try:
        with env['request'].tm:
            dbsession = env['request'].dbsession
            setup_models(dbsession)
    except OperationalError:
        print('''
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for description and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.
            ''')

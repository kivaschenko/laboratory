import argparse
import sys
import json
import os
from pyramid.paster import bootstrap, setup_logging
from sqlalchemy.exc import OperationalError

from .. import models
from .db_seed import substances, normatives


def setup_models(dbsession):
    """Add or update models / fixtures in the database."""
    # Add substances
    for subst in substances:
        new_subst = models.substance.Substance(name=subst[0], measurement=subst[1])
        dbsession.add(new_subst)

    # Add normatives
    for norm in normatives:
        new_normative = models.normative.Normative(
            name=norm[0], output=norm[1], data=json.dumps(norm[2])
        )
        dbsession.add(new_normative)

    # Create default admin user
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@laboratory.local")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if not admin_password:
        print("WARNING: No ADMIN_PASSWORD environment variable set.")
        print("Using default password 'change_me_please' - CHANGE THIS IN PRODUCTION!")
        admin_password = "change_me_please"

    admin_user = models.user.User(nickname="admin", role="editor", email=admin_email)
    admin_user.set_password(admin_password)
    dbsession.add(admin_user)

    print(f"Created admin user: {admin_email}")
    print("Please change the default password after first login!")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Initialize the laboratory database with default data"
    )
    parser.add_argument("config_uri", help="Configuration file, e.g., development.ini")
    parser.add_argument(
        "--admin-email",
        help="Admin user email (can also be set via ADMIN_EMAIL env var)",
        default=os.environ.get("ADMIN_EMAIL", "admin@laboratory.local"),
    )
    return parser.parse_args(argv[1:])


def main(argv=sys.argv):
    args = parse_args(argv)

    # Set admin email from command line if provided
    if hasattr(args, "admin_email"):
        os.environ["ADMIN_EMAIL"] = args.admin_email

    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)

    try:
        with env["request"].tm:
            dbsession = env["request"].dbsession
            setup_models(dbsession)
            print("Database initialization completed successfully!")
    except OperationalError as e:
        print(f"""
Pyramid is having a problem using your SQL database: {e}

The problem might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.md for description and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your configuration file is running.

3.  Your database credentials may be incorrect.
        """)
        sys.exit(1)

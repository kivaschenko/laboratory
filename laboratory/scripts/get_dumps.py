import os
import json
import argparse
from sqlite3 import OperationalError
import sys
from pyramid.paster import bootstrap, setup_logging
from sqlalchemy import MetaData, Table
from sqlalchemy.orm import sessionmaker
from pyramid.scripts.common import parse_vars

def get_tables(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return metadata.tables

def dump_table_data(session, table, output_dir):
    rows = session.query(table).all()
    col_names = table.columns.keys()
    print(f'\n\t{table}\n{col_names}\n')
    
    output_file = os.path.join(output_dir, f"{table.name}.csv")
    with open(output_file, 'w') as f:
        # Write column names
        f.write(','.join(col_names) + '\n')
        # Write data rows
        for row in rows:
            f.write(','.join(map(str, row)) + '\n')
            print(row)

def dump_all_tables(engine, output_dir):
    Session = sessionmaker(bind=engine)
    session = Session()
    tables = get_tables(engine)
    for table in tables.values():
        dump_table_data(session, table, output_dir)
    session.close()
    print(f"Data dump completed. Files are saved in {output_dir}")

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('config_uri', help='Configuration file, e.g., development.ini',)
    return parser.parse_args(argv[1:])

def main(argv=sys.argv):
    args = parse_args(argv)
    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)
    try:
        with env['request'].tm:
            engine = env['request'].dbsession.bind
            output_dir = 'dump_all_tables'
            os.makedirs(output_dir, exist_ok=True)
            dump_all_tables(engine, output_dir)
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

if __name__ == '__main__':
    main()

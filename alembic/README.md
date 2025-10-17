# Laboratory Database Migration

This directory contains database migration files managed by Alembic.

## How to use

### Initial setup
```bash
# Create your first migration
alembic -c development.ini revision --autogenerate -m "Initial migration"

# Apply migrations
alembic -c development.ini upgrade head
```

### Adding new migrations
```bash
# After making changes to models, create a new migration
alembic -c development.ini revision --autogenerate -m "Description of changes"

# Review the generated migration file
# Edit if necessary to add custom logic

# Apply the migration
alembic -c development.ini upgrade head
```

### Other useful commands
```bash
# Check current migration status
alembic -c development.ini current

# Show migration history
alembic -c development.ini history

# Downgrade to previous migration
alembic -c development.ini downgrade -1

# Upgrade to specific revision
alembic -c development.ini upgrade <revision_id>
```

## Migration Files

Migration files are stored in the `versions/` subdirectory and should not be edited manually after they have been applied to production databases.

## Important Notes

1. Always review auto-generated migrations before applying them
2. Test migrations on a copy of production data
3. Backup your database before running migrations in production
4. Migration files should be committed to version control
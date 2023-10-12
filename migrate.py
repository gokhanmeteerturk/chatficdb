print("migrations ran")
print("migrations ran")
print("migrations ran")
print("migrations ran")
print("migrations ran")
print("migrations ran")

"""
from playhouse.migrate import DatabaseMigrator
from your_app.models import database  # Import your Peewee database instance

# Specify your migrations folder
migration_folder = 'migrations'

# Create a migrator
migrator = DatabaseMigrator(database)

# Get a list of applied migrations from the database
applied_migrations = database.get_columns('migrations', 'name')

# Get a list of available migration files in the migrations folder
import os
migration_files = os.listdir(migration_folder)
migration_files.sort()  # Ensure they are in the right order

# Find new migrations that haven't been applied
new_migrations = [m for m in migration_files if m not in applied_migrations]

if new_migrations:
    # Apply new migrations
    with database.atomic():
        for migration in new_migrations:
            migration_module = __import__(f'{migration_folder}.{migration}', fromlist=['migrate'])
            migration_module.migrate(migrator)
            database.execute_sql("INSERT INTO migrations (name) VALUES (?)", (migration,))

# Add this at the end to be able to run the script from the command line
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        # If you run "python migrate.py migrate" in the command line, it will trigger migration.
        pass
"""
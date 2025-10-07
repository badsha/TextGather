#!/usr/bin/env python3
"""
Database Migration Runner
Run this script to apply database migrations safely in production
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration(migration_file):
    """Run a single migration file"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"Running migration: {migration_file}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Read migration file
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute migration
        cursor.execute(sql)
        conn.commit()
        
        print(f"✓ Migration {migration_file} completed successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        sys.exit(1)

def main():
    """Run all pending migrations"""
    migrations_dir = 'migrations'
    
    if not os.path.exists(migrations_dir):
        print(f"No migrations directory found at {migrations_dir}")
        return
    
    # Get all .sql files in migrations directory
    migration_files = sorted([
        os.path.join(migrations_dir, f) 
        for f in os.listdir(migrations_dir) 
        if f.endswith('.sql')
    ])
    
    if not migration_files:
        print("No migration files found")
        return
    
    print(f"Found {len(migration_files)} migration(s)")
    print("-" * 50)
    
    for migration_file in migration_files:
        run_migration(migration_file)
    
    print("-" * 50)
    print("All migrations completed successfully!")

if __name__ == '__main__':
    main()

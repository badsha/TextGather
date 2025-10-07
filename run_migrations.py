#!/usr/bin/env python3
"""
Database Migration Runner for Development
Wrapper script to run database migrations using db_migrator.py

Usage: python run_migrations.py
"""

if __name__ == '__main__':
    from db_migrator import run_migrations
    print("\n🔧 Running database migrations...\n")
    success = run_migrations()
    
    if success:
        print("\n✅ Migrations complete! You can now start the app with: python run.py\n")
        exit(0)
    else:
        print("\n❌ Migration failed!\n")
        exit(1)

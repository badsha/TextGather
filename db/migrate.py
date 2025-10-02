#!/usr/bin/env python3
"""
Database migration script for VoiceScript Collector
Handles migration from SQLite to PostgreSQL and schema updates
"""

import os
import sys
import psycopg2
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

def get_db_connection():
    """Get PostgreSQL database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

def run_sql_file(conn, filename):
    """Execute SQL commands from a file"""
    try:
        with open(filename, 'r') as file:
            sql_content = file.read()
        
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        print(f"✅ Successfully executed {filename}")
        
    except Exception as e:
        print(f"❌ Error executing {filename}: {e}")
        conn.rollback()
        return False
    return True

def create_schema(conn):
    """Create database schema"""
    print("🏗️  Creating database schema...")
    return run_sql_file(conn, 'schema.sql')

def init_demo_data(conn):
    """Initialize demo data"""
    print("📊 Initializing demo data...")
    return run_sql_file(conn, 'init_data.sql')

def migrate_from_sqlite():
    """Migrate existing data from SQLite to PostgreSQL"""
    sqlite_path = 'instance/voicescript.db'
    
    if not os.path.exists(sqlite_path):
        print("ℹ️  No existing SQLite database found, skipping migration")
        return True
    
    print("📦 Migrating data from SQLite...")
    
    pg_conn = get_db_connection()
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    try:
        # Migrate users (with new fields defaulted)
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM user")
        users = sqlite_cursor.fetchall()
        
        pg_cursor = pg_conn.cursor()
        for user in users:
            # Insert user with default gender and age_group
            pg_cursor.execute("""
                INSERT INTO users (id, email, password_hash, first_name, last_name, role, 
                                 google_id, profile_picture, auth_provider, gender, age_group, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, (
                user['id'], user['email'], user['password_hash'], 
                user['first_name'], user['last_name'], user['role'],
                user.get('google_id'), user.get('profile_picture'), 
                user.get('auth_provider', 'local'),
                'prefer-not-to-say',  # Default gender
                'Adult (20–59)',      # Default age group
                user.get('created_at', datetime.utcnow())
            ))
        
        # Migrate scripts
        sqlite_cursor.execute("SELECT * FROM script")
        scripts = sqlite_cursor.fetchall()
        
        for script in scripts:
            pg_cursor.execute("""
                INSERT INTO scripts (id, title, content, language, category, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                script['id'], script['title'], script['content'],
                script.get('language', 'en'), script.get('category'),
                script.get('is_active', True), script.get('created_at', datetime.utcnow())
            ))
        
        # Migrate submissions
        sqlite_cursor.execute("SELECT * FROM submission")
        submissions = sqlite_cursor.fetchall()
        
        for submission in submissions:
            pg_cursor.execute("""
                INSERT INTO submissions (id, user_id, script_id, text_content, audio_filename,
                                       status, created_at, reviewed_at, reviewed_by, review_notes,
                                       quality_score, word_count, duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                submission['id'], submission['user_id'], submission.get('script_id'),
                submission.get('text_content'), submission['audio_filename'],
                submission.get('status', 'pending'), submission.get('created_at'),
                submission.get('reviewed_at'), submission.get('reviewed_by'),
                submission.get('review_notes'), submission.get('quality_score'),
                submission.get('word_count', 0), submission.get('duration', 0.0)
            ))
        
        pg_conn.commit()
        pg_cursor.close()
        
        print("✅ Data migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        pg_conn.rollback()
        return False
    finally:
        sqlite_conn.close()
        pg_conn.close()

def main():
    """Main migration function"""
    print("🚀 Starting database migration to PostgreSQL...")
    
    # Get PostgreSQL connection
    conn = get_db_connection()
    
    try:
        # Create schema
        if not create_schema(conn):
            print("❌ Schema creation failed")
            return False
        
        # Initialize demo data
        if not init_demo_data(conn):
            print("❌ Demo data initialization failed")
            return False
        
        # Migrate existing SQLite data if present
        if not migrate_from_sqlite():
            print("❌ Data migration failed")
            return False
        
        print("✅ Database migration completed successfully!")
        print("🎉 PostgreSQL database is ready for production use")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
"""
Database-First Migration System (Flyway-style)
Executes SQL scripts in sequential order before model updates
"""
import os
import re
import hashlib
import sqlparse
from sqlalchemy import text
from app import app, db


class MigrationRunner:
    """Handles database-first SQL migrations similar to Flyway"""
    
    MIGRATIONS_DIR = "db/migrations"
    VERSION_TABLE = "schema_version"
    
    def __init__(self):
        self.migrations_path = os.path.join(os.path.dirname(__file__), self.MIGRATIONS_DIR)
        
    def ensure_version_table(self):
        """Create schema_version table if it doesn't exist"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.VERSION_TABLE} (
            version VARCHAR(50) PRIMARY KEY,
            description VARCHAR(200) NOT NULL,
            script_name VARCHAR(100) NOT NULL,
            checksum VARCHAR(64) NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms INTEGER,
            success BOOLEAN DEFAULT TRUE
        );
        """
        with db.engine.begin() as conn:
            conn.execute(text(create_table_sql))
            print(f"✓ Migration tracking table '{self.VERSION_TABLE}' ready")
    
    def get_applied_migrations(self):
        """Get list of already applied migrations"""
        query = f"SELECT version, checksum FROM {self.VERSION_TABLE} ORDER BY version"
        with db.engine.connect() as conn:
            result = conn.execute(text(query))
            return {row[0]: row[1] for row in result}
    
    def parse_migration_filename(self, filename):
        """Parse migration filename: V001__description.sql"""
        pattern = r'^V(\d+)__(.+)\.sql$'
        match = re.match(pattern, filename)
        if match:
            version = match.group(1)
            description = match.group(2).replace('_', ' ')
            return version, description
        return None, None
    
    def calculate_checksum(self, content):
        """Calculate SHA256 checksum of migration script"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_pending_migrations(self):
        """Find all SQL migration files that haven't been applied"""
        if not os.path.exists(self.migrations_path):
            print(f"No migrations directory found at {self.migrations_path}")
            return []
        
        applied = self.get_applied_migrations()
        pending = []
        
        # Get all SQL files
        files = sorted([f for f in os.listdir(self.migrations_path) if f.endswith('.sql')])
        
        for filename in files:
            version, description = self.parse_migration_filename(filename)
            if not version:
                print(f"⚠ Skipping invalid migration filename: {filename}")
                continue
            
            filepath = os.path.join(self.migrations_path, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            checksum = self.calculate_checksum(content)
            
            # Check if migration was already applied
            if version in applied:
                if applied[version] != checksum:
                    raise Exception(
                        f"Migration {filename} has been modified!\n"
                        f"Expected checksum: {applied[version]}\n"
                        f"Current checksum:  {checksum}\n"
                        f"Never modify applied migrations!"
                    )
                continue
            
            pending.append({
                'version': version,
                'description': description,
                'filename': filename,
                'filepath': filepath,
                'content': content,
                'checksum': checksum
            })
        
        return pending
    
    def split_sql_statements(self, sql_content):
        """
        Split SQL content into individual statements using sqlparse.
        Handles quotes, comments, and complex SQL syntax correctly.
        """
        # Use sqlparse to split statements properly
        statements = sqlparse.split(sql_content)
        
        # Filter out empty and comment-only statements
        filtered_statements = []
        for stmt in statements:
            cleaned = stmt.strip()
            
            # Skip empty statements
            if not cleaned:
                continue
            
            # Skip pure line comments
            if cleaned.startswith('--'):
                continue
            
            # Skip pure block comments
            if cleaned.startswith('/*') and cleaned.endswith('*/'):
                # Check if it's ONLY a comment (no SQL after the comment)
                continue
            
            # This is a real SQL statement
            filtered_statements.append(cleaned)
        
        return filtered_statements
    
    def execute_migration(self, migration):
        """Execute a single migration within a transaction"""
        import time
        start_time = time.time()
        
        print(f"\n→ Executing migration V{migration['version']}: {migration['description']}")
        
        try:
            # Split SQL into individual statements
            statements = self.split_sql_statements(migration['content'])
            
            with db.engine.begin() as conn:
                # Execute each statement individually within the transaction
                for stmt in statements:
                    if stmt.strip():
                        conn.execute(text(stmt))
                
                # Record in version table
                execution_time = int((time.time() - start_time) * 1000)
                record_sql = f"""
                INSERT INTO {self.VERSION_TABLE} 
                (version, description, script_name, checksum, execution_time_ms, success)
                VALUES (:version, :description, :filename, :checksum, :exec_time, TRUE)
                """
                conn.execute(text(record_sql), {
                    'version': migration['version'],
                    'description': migration['description'],
                    'filename': migration['filename'],
                    'checksum': migration['checksum'],
                    'exec_time': execution_time
                })
            
            print(f"✓ Migration V{migration['version']} completed in {execution_time}ms")
            return True
            
        except Exception as e:
            print(f"✗ Migration V{migration['version']} failed: {str(e)}")
            raise
    
    def run_migrations(self):
        """Main method to run all pending migrations"""
        with app.app_context():
            print("\n" + "="*60)
            print("Database-First Migration System (Flyway-style)")
            print("="*60)
            
            # Ensure tracking table exists
            self.ensure_version_table()
            
            # Find pending migrations
            pending = self.get_pending_migrations()
            
            if not pending:
                print("\n✓ Database is up to date - no pending migrations")
                return True
            
            print(f"\nFound {len(pending)} pending migration(s):")
            for m in pending:
                print(f"  - V{m['version']}: {m['description']}")
            
            # Execute each migration
            print("\nExecuting migrations...")
            for migration in pending:
                self.execute_migration(migration)
            
            print(f"\n✓ Successfully applied {len(pending)} migration(s)")
            print("="*60 + "\n")
            return True


def run_migrations():
    """Entry point for running migrations"""
    runner = MigrationRunner()
    return runner.run_migrations()


if __name__ == "__main__":
    # Allow running directly: python db_migrator.py
    run_migrations()

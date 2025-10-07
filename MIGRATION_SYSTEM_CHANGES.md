# Database Migration System - Changes Summary

## What Changed?

### Before (Custom SQL Migrations)
- Manual SQL files in `migrations/` directory
- Custom Python script (`run_migrations.py`) to execute SQL
- Manual tracking of which migrations ran
- Required writing raw SQL for schema changes

### After (Flask-Migrate / Alembic)
- Industry-standard migration framework
- Automatic migration generation from model changes
- Built-in version tracking with `alembic_version` table
- Easy rollback support
- Better collaboration and deployment workflow

---

## Key Improvements

### 1. Automatic Migration Generation
No more writing SQL manually:
```bash
# Old way: Write SQL file manually
cat > migrations/add_column.sql << 'EOF'
ALTER TABLE submissions ADD COLUMN new_field TEXT;
EOF

# New way: Modify model in app.py, then:
flask db migrate -m "add new_field to submissions"
flask db upgrade
```

### 2. Environment Variable Management
**Before**: Pass DATABASE_URL via command line
```bash
docker run -e DATABASE_URL="postgresql://..." voicescript-collector
```

**Now**: Use `.env` file (recommended)
```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
# DATABASE_URL=postgresql://...

# Run with env file
docker run --env-file .env voicescript-collector

# Or use docker-compose (even easier)
docker-compose up -d
```

### 3. Docker Compose Integration
Single command deployment with database included:
```bash
# Before: Manually set up PostgreSQL, then run app
docker-compose up -d
```

Automatically:
- Starts PostgreSQL database
- Creates database schema
- Runs migrations
- Starts web application
- Configures networking and volumes

---

## Migration Commands

### Common Tasks

```bash
# Check current database version
flask db current

# View migration history
flask db history

# Create new migration after model changes
flask db migrate -m "description"

# Apply pending migrations
flask db upgrade

# Rollback last migration
flask db downgrade -1

# Stamp database without migrating (for existing databases)
flask db stamp head
```

---

## Deployment Workflows

### Development
```bash
# 1. Make changes to models in app.py
# 2. Generate migration
flask db migrate -m "add email verification"

# 3. Review the migration file in migrations/versions/
# 4. Apply migration
flask db upgrade
```

### Production (Docker)
Migrations run automatically on container startup:
```bash
docker-compose up -d  # Migrations apply automatically
```

Or manually:
```bash
docker exec voicescript_app flask db upgrade
```

---

## File Structure

### Before
```
migrations/
  ├── add_transcript_column.sql     # Custom SQL
  └── README.md
run_migrations.py                    # Custom Python script
```

### After
```
migrations/
  ├── alembic.ini                   # Alembic config
  ├── env.py                        # Migration environment
  ├── script.py.mako                # Migration template
  ├── README                        # Auto-generated
  └── versions/                     # Migration files
      └── e4bb56decded_initial_schema.py
```

---

## Baseline Setup (Already Done)

For existing databases, we created a baseline:

```bash
# 1. Initialized Flask-Migrate
flask db init

# 2. Generated initial migration capturing current schema
flask db migrate -m "Initial schema with all existing tables"

# 3. Stamped existing database (didn't run migration)
flask db stamp head
```

This tells Flask-Migrate: "The database already has these tables, don't try to create them again."

---

## Benefits

1. **Version Control**: All schema changes tracked in git
2. **Collaboration**: Team members can apply same migrations
3. **Rollback**: Easily revert problematic changes
4. **Documentation**: Migrations serve as schema change history
5. **Testing**: Can migrate test databases to any version
6. **Automation**: Migrations run automatically in CI/CD pipelines

---

## See Also

- **DEPLOYMENT.md**: Full deployment guide with examples
- **Flask-Migrate Docs**: https://flask-migrate.readthedocs.io/
- **Alembic Docs**: https://alembic.sqlalchemy.org/

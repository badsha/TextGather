# Database Migration Guide - Transcript Column

## Overview
This guide explains how to safely add the `transcript` column to your production database.

## What Changed
- Added `transcript` TEXT column to `submissions` table
- This column stores real-time speech-to-text transcriptions
- The migration is **idempotent** (safe to run multiple times)

## Migration Files Created
```
migrations/
  ├── add_transcript_column.sql    # SQL migration script
  └── README.md                     # Migration documentation
run_migrations.py                   # Python migration runner
docker-entrypoint.sh                # Docker entrypoint (runs migrations automatically)
```

## Deployment Options

### Option 1: Docker Deployment (RECOMMENDED)
The Dockerfile has been updated to automatically run migrations on startup.

**Steps:**
```bash
# 1. Build your Docker image
docker build -t voicescript-collector .

# 2. Deploy/Run the container
docker run -e DATABASE_URL="your_postgres_url" voicescript-collector

# The migration will run automatically before the app starts
```

**What happens:**
1. Docker container starts
2. `docker-entrypoint.sh` runs automatically
3. Migration script executes (adds transcript column if needed)
4. Gunicorn starts the application

### Option 2: Manual Migration (Before Deployment)
Run the migration manually before deploying your application.

**Steps:**
```bash
# 1. Set your DATABASE_URL
export DATABASE_URL="your_production_postgres_url"

# 2. Run the migration
python run_migrations.py

# 3. Deploy your application normally
```

### Option 3: Direct SQL Execution
If you prefer to run the SQL directly:

```bash
# Using psql
psql $DATABASE_URL -f migrations/add_transcript_column.sql

# Or connect to your database and run:
# DO $$ 
# BEGIN
#     IF NOT EXISTS (
#         SELECT 1 FROM information_schema.columns 
#         WHERE table_name = 'submissions' 
#         AND column_name = 'transcript'
#     ) THEN
#         ALTER TABLE submissions ADD COLUMN transcript TEXT;
#     END IF;
# END $$;
```

## Safety Features

### ✅ Idempotent
The migration checks if the column exists before adding it:
- If column exists: Does nothing (safe)
- If column doesn't exist: Adds the column

### ✅ No Data Loss
- Adds a nullable TEXT column
- Existing rows will have `NULL` for transcript
- No existing data is modified or deleted

### ✅ Non-Blocking
- The ALTER TABLE operation is fast
- No table locks for extended periods
- Safe for production databases with data

## Verification

After deployment, verify the migration succeeded:

```sql
-- Check if column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'submissions' 
AND column_name = 'transcript';

-- Expected result:
-- column_name | data_type | is_nullable
-- transcript  | text      | YES
```

## Rollback (If Needed)

If you need to remove the column:

```sql
ALTER TABLE submissions DROP COLUMN IF EXISTS transcript;
```

**Note:** This will delete all transcript data. Only do this if absolutely necessary.

## Docker Compose

If using docker-compose, the migration will run automatically when you do:

```bash
docker-compose up --build
```

No additional steps needed!

## Troubleshooting

### Migration fails with "permission denied"
Ensure your DATABASE_URL user has ALTER TABLE permissions:
```sql
GRANT ALTER ON TABLE submissions TO your_user;
```

### "psycopg2 not found" error
Install the Python dependencies:
```bash
pip install -r requirements.txt
```

### Column already exists warning
This is normal! The migration is idempotent and will skip if the column exists.

## Summary

✅ **Safest method**: Use Docker deployment (Option 1) - migrations run automatically
✅ **Manual control**: Run `python run_migrations.py` before deployment (Option 2)  
✅ **Direct SQL**: Run the SQL file manually if preferred (Option 3)

All methods are safe and production-ready!

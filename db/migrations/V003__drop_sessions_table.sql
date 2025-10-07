-- Remove unnecessary sessions table (Flask uses cookie-based sessions, not database)
DROP TABLE IF EXISTS sessions CASCADE;

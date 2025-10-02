-- PostgreSQL Schema for VoiceScript Collector
-- Production-ready database schema with proper constraints and indexes

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Languages table (referenced by other tables)
CREATE TABLE IF NOT EXISTS languages (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    native_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table with gender and age group fields
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(20) DEFAULT 'provider' CHECK (role IN ('provider', 'reviewer', 'admin')),
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'non-binary', 'prefer-not-to-say')),
    age_group VARCHAR(20) CHECK (age_group IN ('Child (0–12)', 'Teen (13–19)', 'Adult (20–59)', 'Elderly (60+)')),
    google_id VARCHAR(100) UNIQUE,
    profile_picture VARCHAR(255),
    auth_provider VARCHAR(20) DEFAULT 'local' CHECK (auth_provider IN ('local', 'google')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scripts table
CREATE TABLE IF NOT EXISTS scripts (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Submissions table
CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    script_id INTEGER NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    text_content TEXT,
    audio_filename VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'correction_requested')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id),
    review_notes TEXT,
    quality_score INTEGER CHECK (quality_score >= 1 AND quality_score <= 5),
    word_count INTEGER DEFAULT 0,
    duration FLOAT DEFAULT 0.0
);

-- Billing records table
CREATE TABLE IF NOT EXISTS billing_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submission_id INTEGER REFERENCES submissions(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    rate_per_word DECIMAL(10,4),
    rate_per_submission DECIMAL(10,2),
    billing_type VARCHAR(20) NOT NULL CHECK (billing_type IN ('provider', 'reviewer')),
    language_code VARCHAR(10) NOT NULL,
    word_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pricing rates table
CREATE TABLE IF NOT EXISTS pricing_rates (
    id SERIAL PRIMARY KEY,
    language_code VARCHAR(10) NOT NULL REFERENCES languages(code) ON DELETE CASCADE,
    provider_rate_per_word DECIMAL(10,4) DEFAULT 0.01,
    reviewer_rate_per_submission DECIMAL(10,2) DEFAULT 2.00,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_script_id ON submissions(script_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_reviewed_by ON submissions(reviewed_by);
CREATE INDEX IF NOT EXISTS idx_billing_records_user_id ON billing_records(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_records_submission_id ON billing_records(submission_id);
CREATE INDEX IF NOT EXISTS idx_pricing_rates_language_code ON pricing_rates(language_code);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for pricing_rates updated_at
DROP TRIGGER IF EXISTS update_pricing_rates_updated_at ON pricing_rates;
CREATE TRIGGER update_pricing_rates_updated_at
    BEFORE UPDATE ON pricing_rates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
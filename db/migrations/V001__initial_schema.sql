-- Initial database schema for VoiceScript Collector
-- Creates all base tables for the application

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(20) DEFAULT 'provider',
    gender VARCHAR(20),
    age_group VARCHAR(20),
    google_id VARCHAR(100) UNIQUE,
    profile_picture VARCHAR(255),
    auth_provider VARCHAR(20) DEFAULT 'local',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scripts table
CREATE TABLE IF NOT EXISTS scripts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    content TEXT NOT NULL,
    category VARCHAR(100),
    difficulty VARCHAR(50),
    target_duration INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Script variant requirements table
CREATE TABLE IF NOT EXISTS script_variant_requirements (
    id SERIAL PRIMARY KEY,
    script_id INTEGER NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    gender VARCHAR(20) NOT NULL,
    age_group VARCHAR(20) NOT NULL,
    target_total INTEGER DEFAULT 1 NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_script_variant UNIQUE (script_id, gender, age_group)
);

-- Submissions table
CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    script_id INTEGER NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    text_content TEXT,
    audio_filename VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    review_notes TEXT,
    quality_score INTEGER,
    word_count INTEGER DEFAULT 0,
    duration FLOAT DEFAULT 0.0,
    provider_gender VARCHAR(20),
    provider_age_group VARCHAR(20),
    collected_by_admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    speaker_name VARCHAR(100),
    speaker_location VARCHAR(255),
    is_field_collection BOOLEAN DEFAULT FALSE
);

-- Billing records table
CREATE TABLE IF NOT EXISTS billing_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submission_id INTEGER REFERENCES submissions(id) ON DELETE SET NULL,
    amount FLOAT NOT NULL,
    rate_per_word FLOAT,
    rate_per_submission FLOAT,
    billing_type VARCHAR(20) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    word_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Languages table
CREATE TABLE IF NOT EXISTS languages (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    native_name VARCHAR(100),
    rate_per_word FLOAT DEFAULT 0.0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_script_id ON submissions(script_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_field_collection ON submissions(is_field_collection);
CREATE INDEX IF NOT EXISTS idx_billing_user_id ON billing_records(user_id);

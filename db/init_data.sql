-- Initialize demo data for VoiceScript Collector
-- This script populates the database with initial data for testing and development

-- Insert demo languages
INSERT INTO languages (code, name, native_name, is_active) VALUES
('en', 'English', 'English', TRUE),
('es', 'Spanish', 'Español', TRUE),
('fr', 'French', 'Français', TRUE),
('de', 'German', 'Deutsch', TRUE),
('bn', 'Bengali', 'বাংলা', TRUE),
('hi', 'Hindi', 'हिन्दी', TRUE),
('ar', 'Arabic', 'العربية', TRUE),
('zh', 'Chinese', '中文', TRUE),
('ja', 'Japanese', '日本語', TRUE),
('ko', 'Korean', '한국어', TRUE)
ON CONFLICT (code) DO NOTHING;

-- Insert demo pricing rates
INSERT INTO pricing_rates (language_code, provider_rate_per_word, reviewer_rate_per_submission, currency) VALUES
('en', 0.01, 2.00, 'USD'),
('es', 0.012, 2.20, 'USD'),
('fr', 0.013, 2.30, 'USD'),
('de', 0.014, 2.40, 'USD'),
('bn', 0.015, 2.50, 'USD'),
('hi', 0.015, 2.50, 'USD'),
('ar', 0.016, 2.60, 'USD'),
('zh', 0.018, 2.80, 'USD'),
('ja', 0.020, 3.00, 'USD'),
('ko', 0.020, 3.00, 'USD')
ON CONFLICT DO NOTHING;

-- Insert demo users with the new gender and age_group fields
INSERT INTO users (email, password_hash, first_name, last_name, role, gender, age_group, auth_provider) VALUES
('admin@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Demo', 'Admin', 'admin', 'prefer-not-to-say', 'Adult (20–59)', 'local'),
('provider@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Demo', 'Provider', 'provider', 'female', 'Adult (20–59)', 'local'),
('reviewer@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Demo', 'Reviewer', 'reviewer', 'male', 'Adult (20–59)', 'local'),
('john.provider@example.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'John', 'Smith', 'provider', 'male', 'Teen (13–19)', 'local'),
('maria.provider@example.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Maria', 'Rodriguez', 'provider', 'female', 'Elderly (60+)', 'local'),
('male.child@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Alex', 'Johnson', 'provider', 'male', 'Child (0–12)', 'local'),
('male.teen@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Ryan', 'Davis', 'provider', 'male', 'Teen (13–19)', 'local'),
('male.adult@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Michael', 'Brown', 'provider', 'male', 'Adult (20–59)', 'local'),
('male.elderly@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Robert', 'Wilson', 'provider', 'male', 'Elderly (60+)', 'local'),
('female.child@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Emma', 'Taylor', 'provider', 'female', 'Child (0–12)', 'local'),
('female.teen@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Sophie', 'Anderson', 'provider', 'female', 'Teen (13–19)', 'local'),
('female.adult@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Jessica', 'Martinez', 'provider', 'female', 'Adult (20–59)', 'local'),
('female.elderly@demo.com', 'scrypt:32768:8:1$xo68r8gJwcsizOmS$c05c09475551b4875b8cc7f948bf505d7f489ce85355c95c37002eec9135f58223f4ad077a2d3dfa27f90d430af79968c7f3b7a31b7d491c4a62ec873289bc4a', 'Margaret', 'Garcia', 'provider', 'female', 'Elderly (60+)', 'local')
ON CONFLICT (email) DO NOTHING;

-- Insert demo scripts
INSERT INTO scripts (content, language, is_active) VALUES
('Hello, my name is [Your Name] and I am from [Your Location]. I am excited to contribute to this voice data collection project.', 'en', TRUE),
('Today is a beautiful sunny day with clear blue skies. The temperature is perfect for outdoor activities.', 'en', TRUE),
('Once upon a time, in a land far away, there lived a wise old owl who helped all the forest animals solve their problems.', 'en', TRUE),
('Please read the following numbers clearly: 123, 456, 789, 1000, 2023, 15.5, 99.99, 0.01', 'en', TRUE),
('Artificial intelligence, machine learning, natural language processing, neural networks, deep learning, algorithm', 'en', TRUE)
ON CONFLICT DO NOTHING;
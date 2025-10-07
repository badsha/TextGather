-- Add transcript column to submissions table
-- Stores real-time speech-to-text transcription from Web Speech API

ALTER TABLE submissions 
ADD COLUMN IF NOT EXISTS transcript TEXT;

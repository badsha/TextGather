-- Migration V005: Add transcript_language_id to submissions table
-- This allows transcripts to be in a different language than the audio recording
-- Example: Audio in Bengali, transcript in English (translation)

-- Add transcript_language_id column (nullable - transcripts are optional)
ALTER TABLE submissions 
ADD COLUMN transcript_language_id INTEGER REFERENCES languages(id) ON DELETE RESTRICT;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_submissions_transcript_language_id ON submissions(transcript_language_id);

-- Add comment to clarify usage
COMMENT ON COLUMN submissions.transcript_language_id IS 'Language of the transcript text (may differ from audio language)';

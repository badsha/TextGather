-- Add language selection to submissions
-- A script can have multiple recordings in different languages
-- Users select language before/during submission

-- Step 1: Add language_id column (nullable initially for backfill)
ALTER TABLE submissions 
ADD COLUMN language_id INTEGER REFERENCES languages(id) ON DELETE RESTRICT;

-- Step 2: Backfill existing submissions with language from their associated script
-- Map: submissions.script_id → scripts.language (code) → languages.code → languages.id
UPDATE submissions
SET language_id = (
    SELECT l.id 
    FROM scripts s
    JOIN languages l ON s.language = l.code
    WHERE s.id = submissions.script_id
    LIMIT 1
)
WHERE language_id IS NULL;

-- Step 3: Set default language for any remaining NULL values (fallback to English)
UPDATE submissions
SET language_id = (SELECT id FROM languages WHERE code = 'en' LIMIT 1)
WHERE language_id IS NULL;

-- Step 4: Make language_id NOT NULL now that all rows have values
ALTER TABLE submissions 
ALTER COLUMN language_id SET NOT NULL;

-- Step 5: Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_submissions_language_id ON submissions(language_id);

-- Step 6: Add comment for documentation
COMMENT ON COLUMN submissions.language_id IS 'Language of the recording/transcript - selected by user during submission';

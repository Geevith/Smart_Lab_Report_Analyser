-- Migration: Add demographic fields to users table
-- Purpose: Enable personalized insights based on age, gender, and ethnicity
-- Date: 2026-02-07

-- Add age column (nullable for existing users)
ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER;

-- Add ethnicity column (nullable for existing users)
ALTER TABLE users ADD COLUMN IF NOT EXISTS ethnicity VARCHAR(100);

-- Add comment to age column
COMMENT ON COLUMN users.age IS 'User age for personalized medical insights';

-- Add comment to ethnicity column  
COMMENT ON COLUMN users.ethnicity IS 'User ethnicity for demographic-specific reference ranges';

-- Note: gender column already exists in the schema
-- Note: All fields are nullable to support existing users and optional data collection

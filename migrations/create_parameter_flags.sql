-- Migration to create parameter_flags table
-- This table tracks user-reported issues with extracted parameters

CREATE TABLE IF NOT EXISTS parameter_flags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    parameter_name VARCHAR(255) NOT NULL,
    original_value TEXT,
    corrected_value TEXT,
    issue_type VARCHAR(50) NOT NULL CHECK (issue_type IN ('misread', 'incorrect_unit', 'missing', 'other')),
    notes TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_parameter_flags_user_id ON parameter_flags(user_id);
CREATE INDEX IF NOT EXISTS idx_parameter_flags_report_id ON parameter_flags(report_id);
CREATE INDEX IF NOT EXISTS idx_parameter_flags_parameter_name ON parameter_flags(parameter_name);
CREATE INDEX IF NOT EXISTS idx_parameter_flags_created_at ON parameter_flags(created_at DESC);

-- Add comment for documentation
COMMENT ON TABLE parameter_flags IS 'Stores user feedback about incorrectly extracted or missing parameters to improve OCR accuracy';

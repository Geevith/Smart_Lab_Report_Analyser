-- Create shareable_links table for report sharing
CREATE TABLE IF NOT EXISTS shareable_links (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    share_token VARCHAR(128) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_shareable_links_token ON shareable_links(share_token);
CREATE INDEX idx_shareable_links_user ON shareable_links(user_id);
CREATE INDEX idx_shareable_links_report ON shareable_links(report_id);

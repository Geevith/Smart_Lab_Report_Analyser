"""
migrate_db.py — Add soft-delete + kb_version columns to SQLite databases.
Run once: python migrate_db.py
"""
import sqlite3
from pathlib import Path

DB_FILES = ["lab_analyzer.db", "reports.db"]

for db_file in DB_FILES:
    p = Path(db_file)
    if not p.exists():
        print(f"SKIP {db_file}: not found")
        continue

    print(f"\n=== {db_file} ===")
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables:", tables)

    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        cols = [r[1] for r in cur.fetchall()]
        print(f"  {t}: {cols}")

    # 1. Soft-delete on reports
    if "reports" in tables:
        for col, col_type in [("deleted_at", "DATETIME"), ("kb_version", "TEXT")]:
            try:
                cur.execute(f"ALTER TABLE reports ADD COLUMN {col} {col_type} DEFAULT NULL")
                print(f"  + Added '{col}' to reports")
            except Exception as e:
                print(f"  ~ '{col}' already exists or error: {e}")

        # Indexes
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_created ON reports(user_id, created_at DESC)")
            print("  + Added idx_reports_user_created")
        except Exception as e:
            print(f"  ~ Index error: {e}")

        # Partial index for non-deleted rows (SQLite supports this)
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_active ON reports(user_id) WHERE deleted_at IS NULL")
            print("  + Added idx_reports_active partial index")
        except Exception as e:
            print(f"  ~ Partial index error: {e}")

    # 2. Session cleanup index  
    if "sessions" in tables:
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)")
            print("  + Added idx_sessions_token")
        except Exception as e:
            print(f"  ~ Session index error: {e}")

    con.commit()
    con.close()
    print(f"  Done: {db_file}")

print("\n=== Migration complete ===")

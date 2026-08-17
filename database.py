"""
Database layer for the Traceability Console.
Stores every evidence record permanently in a local SQLite file,
so run history survives restarts instead of living only in memory.
Supports many-to-many linking: a requirement can have several
linked tests, so evidence lookups are filtered by both req_id
and test_ref.
"""

import sqlite3


def get_connection(db_path="traceability.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path="traceability.db"):
    """Create the evidence table if it doesn't already exist."""
    conn = get_connection(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            req_id TEXT NOT NULL,
            test_ref TEXT,
            status TEXT NOT NULL,
            error TEXT,
            timestamp TEXT NOT NULL
        )
        """)
    conn.commit()
    conn.close()


def insert_evidence(db_path, req_id, test_ref, status, error, timestamp):
    """Insert one evidence record and return its assigned evidence_id."""
    conn = get_connection(db_path)
    cursor = conn.execute(
        """
        INSERT INTO evidence (req_id, test_ref, status, error, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (req_id, test_ref, status, error, timestamp),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_evidence(db_path):
    """Return every evidence record ever recorded, oldest first."""
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM evidence ORDER BY evidence_id ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_latest_evidence_for(db_path, req_id, test_ref):
    """Return the most recent evidence record for a given requirement + test pair, or None."""
    conn = get_connection(db_path)
    if test_ref is None:
        query = """
            SELECT * FROM evidence
            WHERE req_id = ? AND test_ref IS NULL
            ORDER BY evidence_id DESC
            LIMIT 1
        """
        params = (req_id,)
    else:
        query = """
            SELECT * FROM evidence
            WHERE req_id = ? AND test_ref = ?
            ORDER BY evidence_id DESC
            LIMIT 1
        """
        params = (req_id, test_ref)

    row = conn.execute(query, params).fetchone()
    conn.close()
    return dict(row) if row else None

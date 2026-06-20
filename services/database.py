"""SQLite persistence for listings, price history, and feedback."""

import sqlite3
from pathlib import Path


def connect(database_path):
    """Open a SQLite connection and initialize the schema."""
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    initialize(connection)
    return connection


def reset_database(database_path):
    """Remove the local SQLite database file if it exists."""
    path = Path(database_path)
    if not path.exists():
        return False

    path.unlink()
    return True


def initialize(connection):
    """Create database tables when they do not exist."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_listing_id TEXT NOT NULL,
            gmail_message_id TEXT,
            title TEXT NOT NULL,
            area TEXT,
            price_eur INTEGER,
            size_sqm INTEGER,
            rooms INTEGER,
            url TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            score_reasons TEXT DEFAULT '',
            first_seen_at TEXT,
            last_seen_at TEXT,
            UNIQUE(source, source_listing_id)
        );

        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            price_eur INTEGER NOT NULL,
            observed_at TEXT,
            FOREIGN KEY(listing_id) REFERENCES listings(id)
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER,
            feedback_text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(listing_id) REFERENCES listings(id)
        );

        CREATE TABLE IF NOT EXISTS recent_digest_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            item_number INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(listing_id) REFERENCES listings(id)
        );
        """
    )
    connection.commit()


def find_listing(connection, source, source_listing_id):
    """Return one listing by source identity, or None."""
    row = connection.execute(
        """
        SELECT * FROM listings
        WHERE source = ? AND source_listing_id = ?
        """,
        (source, source_listing_id),
    ).fetchone()
    return dict(row) if row else None


def upsert_listing(connection, listing):
    """Insert or update a listing and append price history when needed."""
    existing = find_listing(
        connection,
        listing["source"],
        listing["source_listing_id"],
    )

    if existing is None:
        cursor = connection.execute(
            """
            INSERT INTO listings (
                source, source_listing_id, gmail_message_id, title, area,
                price_eur, size_sqm, rooms, url, score, score_reasons,
                first_seen_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _listing_values(listing),
        )
        listing_id = cursor.lastrowid
        _insert_price_history(connection, listing_id, listing)
    else:
        listing_id = existing["id"]
        connection.execute(
            """
            UPDATE listings
            SET gmail_message_id = ?, title = ?, area = ?, price_eur = ?,
                size_sqm = ?, rooms = ?, url = ?, score = ?,
                score_reasons = ?, last_seen_at = ?
            WHERE id = ?
            """,
            (
                listing.get("gmail_message_id"),
                listing["title"],
                listing.get("area"),
                listing.get("price_eur"),
                listing.get("size_sqm"),
                listing.get("rooms"),
                listing["url"],
                listing.get("score", 0),
                ", ".join(listing.get("score_reasons", [])),
                listing.get("last_seen_at"),
                listing_id,
            ),
        )
        if listing.get("price_eur") and listing.get("price_eur") != existing.get("price_eur"):
            _insert_price_history(connection, listing_id, listing)

    connection.commit()
    return listing_id


def _listing_values(listing):
    return (
        listing["source"],
        listing["source_listing_id"],
        listing.get("gmail_message_id"),
        listing["title"],
        listing.get("area"),
        listing.get("price_eur"),
        listing.get("size_sqm"),
        listing.get("rooms"),
        listing["url"],
        listing.get("score", 0),
        ", ".join(listing.get("score_reasons", [])),
        listing.get("first_seen_at"),
        listing.get("last_seen_at"),
    )


def _insert_price_history(connection, listing_id, listing):
    connection.execute(
        """
        INSERT INTO price_history (listing_id, price_eur, observed_at)
        VALUES (?, ?, ?)
        """,
        (listing_id, listing["price_eur"], listing.get("last_seen_at")),
    )


def add_feedback(connection, listing_id, feedback_text, raw_text):
    """Store one user feedback event."""
    connection.execute(
        """
        INSERT INTO feedback (listing_id, feedback_text)
        VALUES (?, ?)
        """,
        (listing_id, f"{feedback_text}: {raw_text}"),
    )
    connection.commit()


def list_recent_listings(connection, limit=8):
    """Return recent listings in the same order used by the digest."""
    rows = connection.execute(
        """
        SELECT * FROM listings
        ORDER BY score DESC, last_seen_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def record_recent_digest(connection, listing_ids):
    """Remember the exact listing order shown in the latest WhatsApp digest."""
    connection.execute("DELETE FROM recent_digest_items")
    for item_number, listing_id in enumerate(listing_ids, start=1):
        connection.execute(
            """
            INSERT INTO recent_digest_items (listing_id, item_number)
            VALUES (?, ?)
            """,
            (listing_id, item_number),
        )
    connection.commit()


def list_recent_digest_listings(connection, limit=8):
    """Return listings in the exact order used by the latest WhatsApp digest."""
    rows = connection.execute(
        """
        SELECT listings.*
        FROM recent_digest_items
        JOIN listings ON listings.id = recent_digest_items.listing_id
        ORDER BY recent_digest_items.item_number ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_favorite_listings(connection, limit=50):
    """Return listings saved as favorites in the agent's local database."""
    rows = connection.execute(
        """
        SELECT listings.*, MAX(feedback.created_at) AS saved_at
        FROM feedback
        JOIN listings ON listings.id = feedback.listing_id
        WHERE feedback.feedback_text LIKE 'favorite:%'
        GROUP BY listings.id
        ORDER BY saved_at DESC, listings.score DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]

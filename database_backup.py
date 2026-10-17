import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chatbot.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def add_audio_path_column():
    with get_connection() as connection:
        columns = [
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(messages)"
            ).fetchall()
        ]

        if "audio_path" not in columns:
            connection.execute(
                "ALTER TABLE messages ADD COLUMN audio_path TEXT"
            )

def initialize_database():
    """Create all required tables."""

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL
                    CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_messages_conversation_id
            ON messages(conversation_id, id)
        """)

        # Store uploaded document metadata.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                file_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                character_count INTEGER NOT NULL
            )
        """)

        # Store extracted document text in manageable chunks.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(document_id)
                    REFERENCES documents(id)
                    ON DELETE CASCADE,
                UNIQUE(document_id, chunk_index)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_document_chunks_document_id
            ON document_chunks(document_id, chunk_index)
        """)


# ---------------------------------------
# Conversation operations
# ---------------------------------------

def create_conversation(title="New Chat"):
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO conversations
                (title, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (title, now, now)
        )

        return cursor.lastrowid


def get_conversations():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC, id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_conversation(conversation_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        ).fetchone()

        return dict(row) if row else None


def get_messages(conversation_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

        return [dict(row) for row in rows]


def add_message(conversation_id, role, content):
    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role")

    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO messages
                (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, role, content, now)
        )

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
            """,
            (now, conversation_id)
        )

        return cursor.lastrowid


def update_conversation_title(conversation_id, title):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE conversations
            SET title = ?
            WHERE id = ?
            """,
            (title, conversation_id)
        )


def delete_conversation(conversation_id):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )


# ---------------------------------------
# Document operations
# ---------------------------------------




def save_document(
    filename,
    file_hash,
    file_type,
    text,
    chunks
):
    """
    Save document metadata and extracted text.

    Returns:
        (document_id, created)
    """

    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:

        existing = connection.execute(
            """
            SELECT id
            FROM documents
            WHERE file_hash = ?
            """,
            (file_hash,)
        ).fetchone()

        if existing:
            return existing["id"], False

        cursor = connection.execute(
            """
            INSERT INTO documents
                (filename, file_hash, file_type,
                 created_at, character_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                filename,
                file_hash,
                file_type,
                now,
                len(text)
            )
        )

        document_id = cursor.lastrowid

        connection.executemany(
            """
            INSERT INTO document_chunks
                (document_id, chunk_index, content)
            VALUES (?, ?, ?)
            """,
            [
                (document_id, index, chunk)
                for index, chunk in enumerate(chunks)
            ]
        )

        return document_id, True



def get_document_chunks(limit=5):
    """Retrieve initial chunks from stored documents."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                dc.document_id,
                dc.chunk_index,
                dc.content,
                d.filename
            FROM document_chunks dc
            JOIN documents d
                ON d.id = dc.document_id
            ORDER BY d.id DESC, dc.chunk_index ASC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        return [dict(row) for row in rows]

def get_documents():
    """List all stored documents."""

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                id,
                filename,
                file_type,
                created_at,
                character_count
            FROM documents
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def delete_document(document_id):
    """Delete a document and all its chunks."""

    with get_connection() as connection:
        connection.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,)
        )


def search_document_chunks(query, limit=5):
    """
    Find relevant chunks using simple keyword matching.

    This is a lightweight baseline, not semantic search.
    """

    import re
    from collections import Counter

    stopwords = {
        "the", "a", "an", "and", "or", "but", "is", "are",
        "was", "were", "be", "been", "being", "to", "of",
        "in", "on", "at", "for", "from", "by", "with",
        "as", "it", "its", "this", "that", "these", "those",
        "what", "which", "who", "when", "where", "why",
        "how", "can", "could", "would", "should", "do",
        "does", "did", "about", "tell", "me", "please"
    }

    def tokenize(text):
        words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

        return [
            word for word in words
            if len(word) > 1 and word not in stopwords
        ]

    query_words = Counter(tokenize(query))

    if not query_words:
        return []

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                dc.document_id,
                dc.chunk_index,
                dc.content,
                d.filename
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
        """).fetchall()

    scored = []

    for row in rows:
        chunk_words = Counter(tokenize(row["content"]))

        score = sum(
            min(count, chunk_words[word])
            for word, count in query_words.items()
        )

        if score > 0:
            scored.append({
                "document_id": row["document_id"],
                "chunk_index": row["chunk_index"],
                "content": row["content"],
                "filename": row["filename"],
                "score": score
            })

    scored.sort(
        key=lambda item: (
            -item["score"],
            item["document_id"],
            item["chunk_index"]
        )
    )

    return scored[:limit]


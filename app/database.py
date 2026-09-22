from contextlib import contextmanager
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "assistant.db"

@contextmanager
def connect_db():
    connection = sqlite3.connect(DB_PATH)
    try:
        with connection:
            yield connection
    finally:
        connection.close()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                name TEXT,
                contact TEXT,
                request TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                name TEXT,
                contact TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS handoffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL UNIQUE,
                lead_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    init_lead_conversations()
    init_handoff_conversations()
    init_message_conversations()    


def save_message(
    message: str,
    conversation_id: str | None = None,
    role: str = "user",
) -> int:
    with connect_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO messages (
                conversation_id,
                role,
                message
            )
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, message),
        )
        return cursor.lastrowid
    
def get_conversation_messages(conversation_id: str):
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT id, conversation_id, role, message, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()

        return [dict(row) for row in rows]

def save_lead(
    message_id: int,
    name: str | None,
    contact: str | None,
    lead_score: str | None = None,
) -> int:
    with connect_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (
                message_id,
                name,
                contact,
                lead_score
            )
            VALUES (?, ?, ?, ?)
            """,
            (message_id, name, contact, lead_score),
        )
        return cursor.lastrowid


def get_lead(lead_id: int):
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT leads.id, leads.name, leads.contact,
            leads.lead_score,
            messages.message, leads.created_at
            FROM leads
            JOIN messages ON messages.id = leads.message_id
            WHERE leads.id = ?
            """,
            (lead_id,),
        ).fetchone()

    return dict(row) if row else None


def save_handoff(
    message_id: int,
    lead_id: int | None,
    conversation_id: str | None = None,
) -> int:
    with connect_db() as connection:
        connection.execute(
            """
            INSERT INTO handoffs (
                message_id, lead_id, conversation_id
            )
            VALUES (?, ?, ?)
            ON CONFLICT(message_id) DO NOTHING
            """,
            (message_id, lead_id, conversation_id),
        )

        row = connection.execute(
            "SELECT id FROM handoffs WHERE message_id = ?",
            (message_id,),
        ).fetchone()

        return row[0]


def get_handoff(handoff_id: int):
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT handoffs.id, handoffs.message_id,
                   handoffs.lead_id, handoffs.status,
                   handoffs.created_at, messages.message,
                   COALESCE(conversations.name, leads.name) AS name,
                   COALESCE(conversations.contact, leads.contact) AS contact,
                   conversations.request AS original_request
            FROM handoffs
            JOIN messages ON messages.id = handoffs.message_id
            LEFT JOIN leads ON leads.id = handoffs.lead_id
            LEFT JOIN conversations
                ON conversations.conversation_id = COALESCE(
                    handoffs.conversation_id,
                    leads.conversation_id
                )
            WHERE handoffs.id = ?
            """,
            (handoff_id,),
        ).fetchone()

    return dict(row) if row else None


def get_pending_handoffs():
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT handoffs.id, handoffs.message_id,
                   handoffs.lead_id, handoffs.status,
                   handoffs.created_at, messages.message,
                   COALESCE(conversations.name, leads.name) AS name,
                   COALESCE(conversations.contact, leads.contact) AS contact,
                   conversations.request AS original_request
            FROM handoffs
            JOIN messages ON messages.id = handoffs.message_id
            LEFT JOIN leads ON leads.id = handoffs.lead_id
            LEFT JOIN conversations
                ON conversations.conversation_id = COALESCE(
                    handoffs.conversation_id,
                    leads.conversation_id
                )
            WHERE handoffs.status = 'pending'
            ORDER BY handoffs.created_at ASC, handoffs.id ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def complete_handoff(handoff_id: int) -> bool:
    with connect_db() as connection:
        cursor = connection.execute(
            """
            UPDATE handoffs
            SET status = 'completed'
            WHERE id = ?
            """,
            (handoff_id,),
        )
        return cursor.rowcount > 0

def get_conversation(conversation_id: str):
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT conversation_id, name, contact, request,
                   created_at, updated_at
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

    return dict(row) if row else None

def save_conversation(
    conversation_id: str,
    name: str | None = None,
    contact: str | None = None,
    request: str | None = None,
):
    with connect_db() as connection:
        connection.execute(
            """
            INSERT INTO conversations (
                conversation_id, name, contact, request
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                name = COALESCE(excluded.name, conversations.name),
                contact = COALESCE(excluded.contact, conversations.contact),
                request = COALESCE(excluded.request, conversations.request),
                updated_at = CURRENT_TIMESTAMP
            """,
            (conversation_id, name, contact, request),
        )

def init_lead_conversations():
    with connect_db() as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(leads)")
        }

        if "conversation_id" not in columns:
            connection.execute(
                "ALTER TABLE leads ADD COLUMN conversation_id TEXT"
            )

        if "lead_score" not in columns:
            connection.execute(
                "ALTER TABLE leads ADD COLUMN lead_score TEXT"
            )

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_leads_conversation_id
            ON leads (conversation_id)
            WHERE conversation_id IS NOT NULL
        """)

def save_conversation_lead(
    conversation_id: str,
    message_id: int,
    name: str | None,
    contact: str | None,
    lead_score: str | None = None,
) -> int:
    with connect_db() as connection:
        connection.execute(
            """
            INSERT INTO leads (
                conversation_id,
                message_id,
                name,
                contact,
                lead_score
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id)
            WHERE conversation_id IS NOT NULL
            DO UPDATE SET
                name = COALESCE(excluded.name, leads.name),
                contact = COALESCE(excluded.contact, leads.contact),
                lead_score = COALESCE(excluded.lead_score, leads.lead_score)
            """,
            (
                conversation_id,
                message_id,
                name,
                contact,
                lead_score,
            ),
        )

        row = connection.execute(
            "SELECT id FROM leads WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()

        return row[0]

def init_handoff_conversations():
    with connect_db() as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(handoffs)")
        }

        if "conversation_id" not in columns:
            connection.execute(
                "ALTER TABLE handoffs ADD COLUMN conversation_id TEXT"
            )

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_handoffs_conversation_id
            ON handoffs (conversation_id)
        """)
def init_message_conversations():
    with connect_db() as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(messages)")
        }

        if "conversation_id" not in columns:
            connection.execute(
                "ALTER TABLE messages ADD COLUMN conversation_id TEXT"
            )

        if "role" not in columns:
            connection.execute(
                "ALTER TABLE messages ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
            )    

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_messages_conversation_id
            ON messages (conversation_id)
        """)
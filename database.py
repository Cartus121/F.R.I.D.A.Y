"""
Database Manager for F.R.I.D.A.Y.
Handles local SQLite and external database connections
"""

# Standard library imports
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
try:
    from sqlalchemy import create_engine, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Local imports
from config import EXTERNAL_DB, LOCAL_DB_PATH


class DatabaseManager:
    """Manages all database operations for F.R.I.D.A.Y."""
    
    def __init__(self):
        self.local_db_path = LOCAL_DB_PATH
        self.external_engine = None
        self._init_local_db()
        self._init_external_db()
    
    def _init_local_db(self):
        """Initialize local SQLite database with required tables"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript("""
            -- Calendar Events
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                location TEXT,
                reminder_minutes INTEGER DEFAULT 30,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Notes
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Reminders
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                remind_at DATETIME NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Conversation History
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                topic TEXT,
                sentiment TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- User Preferences
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Custom Commands
            CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_phrase TEXT NOT NULL UNIQUE,
                response TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- New table: Long-term memories about user
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 5,
                last_referenced DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- New table: AI personality traits that evolve
            CREATE TABLE IF NOT EXISTS personality_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trait_name TEXT UNIQUE NOT NULL,
                trait_value REAL DEFAULT 0.5,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- New table: Learned user preferences from conversations
            CREATE TABLE IF NOT EXISTS learned_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_type TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                times_confirmed INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- New table: Conversation summaries for context
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                summary TEXT NOT NULL,
                topics TEXT,
                mood TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Migrate existing tables - add missing columns
        self._migrate_database(cursor)
        
        default_traits = [
            ("warmth", 0.7, "How warm and friendly vs formal"),
            ("humor", 0.5, "How often to use humor"),
            ("curiosity", 0.6, "How much to ask follow-up questions"),
            ("directness", 0.5, "How direct vs elaborate in responses"),
            ("empathy", 0.7, "How emotionally attuned to user"),
            ("playfulness", 0.4, "How playful vs serious"),
            ("formality", 0.3, "How formal vs casual in speech"),
        ]
        
        for trait_name, trait_value, description in default_traits:
            cursor.execute("""
                INSERT OR IGNORE INTO personality_traits (trait_name, trait_value, description)
                VALUES (?, ?, ?)
            """, (trait_name, trait_value, description))
        
        conn.commit()
        conn.close()
        print("Local database initialized")
    
    def _migrate_database(self, cursor):
        """Add missing columns to existing tables"""
        # Check and add missing columns to conversations table
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'topic' not in columns:
            cursor.execute("ALTER TABLE conversations ADD COLUMN topic TEXT")
            print("  Added 'topic' column to conversations")
        
        if 'sentiment' not in columns:
            cursor.execute("ALTER TABLE conversations ADD COLUMN sentiment TEXT")
            print("  Added 'sentiment' column to conversations")
    
    def _init_external_db(self):
        """Initialize external database connection if configured"""
        if EXTERNAL_DB and SQLALCHEMY_AVAILABLE:
            try:
                db_type = EXTERNAL_DB.get("type", "postgresql")
                host = EXTERNAL_DB.get("host", "localhost")
                port = EXTERNAL_DB.get("port", 5432)
                database = EXTERNAL_DB.get("database", "")
                username = EXTERNAL_DB.get("username", "")
                password = EXTERNAL_DB.get("password", "")
                
                if db_type == "postgresql":
                    url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                elif db_type == "mysql":
                    url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
                else:
                    print(f"⚠️ Unsupported database type: {db_type}")
                    return
                
                self.external_engine = create_engine(url)
                # Test connection
                with self.external_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print(f"✅ Connected to external {db_type} database")
            except Exception as e:
                print(f"⚠️ Could not connect to external database: {e}")
                self.external_engine = None
    
    # =========================================================================
    # Calendar Events
    # =========================================================================
    
    def add_event(self, title: str, start_time: datetime, 
                  description: str = "", end_time: datetime = None,
                  location: str = "", reminder_minutes: int = 30) -> int:
        """Add a new calendar event"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (title, description, start_time, end_time, 
                              location, reminder_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, description, start_time, end_time, location, reminder_minutes))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id
    
    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Get upcoming events for the next N days"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events 
            WHERE start_time >= datetime('now') 
            AND start_time <= datetime('now', ?)
            ORDER BY start_time ASC
        """, (f'+{days} days',))
        
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return events
    
    def get_todays_events(self) -> List[Dict]:
        """Get all events for today"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events 
            WHERE date(start_time) = date('now')
            ORDER BY start_time ASC
        """)
        
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return events
    
    def delete_event(self, event_id: int) -> bool:
        """Delete an event by ID"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    # =========================================================================
    # Notes
    # =========================================================================
    
    def add_note(self, content: str, title: str = None, 
                 category: str = "general") -> int:
        """Add a new note"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        if not title:
            # Generate title from first few words
            words = content.split()[:5]
            title = " ".join(words) + ("..." if len(content.split()) > 5 else "")
        
        cursor.execute("""
            INSERT INTO notes (title, content, category)
            VALUES (?, ?, ?)
        """, (title, content, category))
        
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return note_id
    
    def get_notes(self, limit: int = 10, category: str = None) -> List[Dict]:
        """Get recent notes"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT * FROM notes 
                WHERE category = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (category, limit))
        else:
            cursor.execute("""
                SELECT * FROM notes 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        
        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return notes
    
    def search_notes(self, query: str) -> List[Dict]:
        """Search notes by content"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM notes 
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY created_at DESC
        """, (f'%{query}%', f'%{query}%'))
        
        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return notes
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    # =========================================================================
    # Reminders
    # =========================================================================
    
    def add_reminder(self, message: str, remind_at: datetime) -> int:
        """Add a new reminder"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders (message, remind_at)
            VALUES (?, ?)
        """, (message, remind_at))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return reminder_id
    
    def get_pending_reminders(self) -> List[Dict]:
        """Get all pending reminders that are due"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM reminders 
            WHERE is_completed = FALSE 
            AND remind_at <= datetime('now')
            ORDER BY remind_at ASC
        """)
        
        reminders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return reminders
    
    def mark_reminder_complete(self, reminder_id: int) -> bool:
        """Mark a reminder as completed"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reminders 
            SET is_completed = TRUE 
            WHERE id = ?
        """, (reminder_id,))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    # =========================================================================
    # Conversation History (Enhanced)
    # =========================================================================
    
    def save_conversation(self, user_message: str, assistant_response: str, 
                          topic: str = None, sentiment: str = None):
        """Save a conversation exchange with metadata"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (user_message, assistant_response, topic, sentiment)
            VALUES (?, ?, ?, ?)
        """, (user_message, assistant_response, topic, sentiment))
        
        conn.commit()
        conn.close()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversations 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return conversations
    
    def get_conversations_by_date(self, date: str) -> List[Dict]:
        """Get all conversations from a specific date"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE date(timestamp) = date(?)
            ORDER BY timestamp ASC
        """, (date,))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return conversations
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict]:
        """Search past conversations"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE user_message LIKE ? OR assistant_response LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', limit))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return conversations
    
    def get_conversation_count(self) -> int:
        """Get total number of conversations"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    # =========================================================================
    # =========================================================================
    
    def add_memory(self, memory_type: str, content: str, importance: int = 5) -> int:
        """Add a memory about the user (name, preferences, facts they shared)"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        # Check if similar memory exists
        cursor.execute("""
            SELECT id FROM user_memories 
            WHERE memory_type = ? AND content LIKE ?
        """, (memory_type, f'%{content[:50]}%'))
        
        existing = cursor.fetchone()
        if existing:
            # Update existing memory
            cursor.execute("""
                UPDATE user_memories 
                SET content = ?, importance = ?, last_referenced = datetime('now')
                WHERE id = ?
            """, (content, importance, existing[0]))
            memory_id = existing[0]
        else:
            cursor.execute("""
                INSERT INTO user_memories (memory_type, content, importance, last_referenced)
                VALUES (?, ?, ?, datetime('now'))
            """, (memory_type, content, importance))
            memory_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return memory_id
    
    def get_memories(self, memory_type: str = None, limit: int = 20) -> List[Dict]:
        """Get stored memories about the user"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT * FROM user_memories 
                WHERE memory_type = ?
                ORDER BY importance DESC, last_referenced DESC
                LIMIT ?
            """, (memory_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM user_memories 
                ORDER BY importance DESC, last_referenced DESC
                LIMIT ?
            """, (limit,))
        
        memories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return memories
    
    def get_all_memories_formatted(self) -> str:
        """Get all memories as formatted string for AI context"""
        memories = self.get_memories(limit=50)
        if not memories:
            return ""
        
        formatted = []
        for m in memories:
            formatted.append(f"- [{m['memory_type']}] {m['content']}")
        
        return "\n".join(formatted)
    
    # =========================================================================
    # =========================================================================
    
    def get_personality_traits(self) -> Dict[str, float]:
        """Get current personality trait values"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT trait_name, trait_value FROM personality_traits")
        
        traits = {row['trait_name']: row['trait_value'] for row in cursor.fetchall()}
        conn.close()
        return traits
    
    def update_personality_trait(self, trait_name: str, adjustment: float):
        """Adjust a personality trait (clamped between 0.0 and 1.0)"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE personality_traits 
            SET trait_value = MAX(0.0, MIN(1.0, trait_value + ?)),
                updated_at = datetime('now')
            WHERE trait_name = ?
        """, (adjustment, trait_name))
        
        conn.commit()
        conn.close()
    
    def get_personality_description(self) -> str:
        """Get personality as natural language description"""
        traits = self.get_personality_traits()
        descriptions = []
        
        if traits.get('warmth', 0.5) > 0.6:
            descriptions.append("warm and friendly")
        if traits.get('humor', 0.5) > 0.6:
            descriptions.append("has a good sense of humor")
        if traits.get('curiosity', 0.5) > 0.6:
            descriptions.append("curious and asks questions")
        if traits.get('directness', 0.5) > 0.6:
            descriptions.append("direct and to the point")
        if traits.get('empathy', 0.5) > 0.6:
            descriptions.append("emotionally attuned")
        if traits.get('playfulness', 0.5) > 0.6:
            descriptions.append("playful")
        if traits.get('formality', 0.5) < 0.4:
            descriptions.append("casual in speech")
        
        return ", ".join(descriptions) if descriptions else "balanced personality"
    
    # =========================================================================
    # =========================================================================
    
    def learn_preference(self, pref_type: str, pref_value: str, confidence: float = 0.5):
        """Learn or update a user preference"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, times_confirmed, confidence FROM learned_preferences
            WHERE preference_type = ? AND preference_value = ?
        """, (pref_type, pref_value))
        
        existing = cursor.fetchone()
        if existing:
            new_confidence = min(1.0, existing[2] + 0.1)
            cursor.execute("""
                UPDATE learned_preferences
                SET times_confirmed = times_confirmed + 1,
                    confidence = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (new_confidence, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO learned_preferences (preference_type, preference_value, confidence)
                VALUES (?, ?, ?)
            """, (pref_type, pref_value, confidence))
        
        conn.commit()
        conn.close()
    
    def get_learned_preferences(self) -> List[Dict]:
        """Get all learned preferences with high confidence"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM learned_preferences
            WHERE confidence > 0.4
            ORDER BY confidence DESC, times_confirmed DESC
        """)
        
        prefs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return prefs
    
    # =========================================================================
    # =========================================================================
    
    def save_daily_summary(self, date: str, summary: str, topics: str = None, mood: str = None):
        """Save a daily conversation summary"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO conversation_summaries (date, summary, topics, mood)
            VALUES (?, ?, ?, ?)
        """, (date, summary, topics, mood))
        
        conn.commit()
        conn.close()
    
    def get_recent_summaries(self, days: int = 7) -> List[Dict]:
        """Get recent daily summaries"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversation_summaries
            ORDER BY date DESC
            LIMIT ?
        """, (days,))
        
        summaries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return summaries
    
    # =========================================================================
    # External Database Queries
    # =========================================================================
    
    def query_external_db(self, query: str) -> Optional[List[Dict]]:
        """Execute a query on the external database"""
        if not self.external_engine:
            return None
        
        try:
            with self.external_engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return rows
        except Exception as e:
            print(f"External DB query error: {e}")
            return None
    
    def get_external_tables(self) -> Optional[List[str]]:
        """Get list of tables in external database"""
        if not self.external_engine:
            return None
        
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.external_engine)
            return inspector.get_table_names()
        except Exception as e:
            print(f"Error getting tables: {e}")
            return None


# Create global instance
db = DatabaseManager()

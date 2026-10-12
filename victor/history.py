class ConversationManager:
    def __init__(self, database):
        self.db = database

    def create(self, title="Nueva conversación"):
        with self.db.connect() as db:
            return db.execute("INSERT INTO conversations(title) VALUES(?)", (title[:100],)).lastrowid

    def list(self, query=""):
        with self.db.connect() as db:
            return [dict(r) for r in db.execute('''SELECT * FROM conversations c WHERE instr(lower(title),lower(?))>0
                OR EXISTS(SELECT 1 FROM messages m WHERE m.conversation_id=c.id AND instr(lower(m.content),lower(?))>0)
                ORDER BY id DESC LIMIT 200''', (query, query))]

    def get(self, conversation_id):
        with self.db.connect() as db:
            row = db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
            return dict(row) if row else None

    def messages(self, conversation_id, limit=200):
        with self.db.connect() as db:
            rows = db.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?", (conversation_id, limit)).fetchall()
            return [dict(r) for r in reversed(rows)]

    def add(self, conversation_id, role, content):
        with self.db.connect() as db:
            db.execute("INSERT INTO messages(conversation_id,role,content) VALUES(?,?,?)", (conversation_id, role, content))
            if role == "user":
                db.execute("UPDATE conversations SET title=? WHERE id=? AND title='Nueva conversación'", (content[:70], conversation_id))

    def delete(self, conversation_id):
        with self.db.connect() as db:
            db.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))

    def summarize(self, conversation_id, text, through_id):
        with self.db.connect() as db:
            db.execute("UPDATE conversations SET summary=?, summarized_id=? WHERE id=?", (text, through_id, conversation_id))

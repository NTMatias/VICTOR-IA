class MemoryManager:
    """Recuerdos explícitos, editables y separados del historial."""
    def __init__(self, database):
        self.db = database

    def remember(self, key: str, value: str):
        key, value = key.strip(), value.strip()
        if not key or not value or len(key) > 150 or len(value) > 4000:
            from victor.errors import VictorError
            raise VictorError("El recuerdo necesita una clave (hasta 150 caracteres) y un valor (hasta 4000).")
        with self.db.connect() as db:
            db.execute("INSERT INTO memories(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=CURRENT_TIMESTAMP", (key, value))
        return {"guardado": key}

    def recall(self, key: str = ""):
        return self.search_memory(key)

    def search_memory(self, query: str = ""):
        with self.db.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM memories WHERE instr(lower(key),lower(?))>0 OR instr(lower(value),lower(?))>0 ORDER BY updated DESC LIMIT 100", (query, query))]

    def forget(self, key: str):
        with self.db.connect() as db:
            count = db.execute("DELETE FROM memories WHERE key=?", (key,)).rowcount
        return {"eliminados": count}

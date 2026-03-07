import os
import re

MIGRATIONS_DIR = "migrations"

def make_idempotent():
    for filename in os.listdir(MIGRATIONS_DIR):
        if not filename.endswith(".sql"):
            continue
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace CREATE TABLE with CREATE TABLE IF NOT EXISTS
        content = re.sub(r'CREATE TABLE\s+(?!IF NOT EXISTS)([\w_]+)', r'CREATE TABLE IF NOT EXISTS \1', content, flags=re.IGNORECASE)
        
        # Replace CREATE INDEX with CREATE INDEX IF NOT EXISTS
        # Skip UNIQUE INDEX as CREATE UNIQUE INDEX IF NOT EXISTS is valid postgreSQL 9.5+
        content = re.sub(r'CREATE INDEX\s+(?!IF NOT EXISTS)([\w_]+)', r'CREATE INDEX IF NOT EXISTS \1', content, flags=re.IGNORECASE)
        content = re.sub(r'CREATE UNIQUE INDEX\s+(?!IF NOT EXISTS)([\w_]+)', r'CREATE UNIQUE INDEX IF NOT EXISTS \1', content, flags=re.IGNORECASE)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Processed {filename}")

if __name__ == "__main__":
    make_idempotent()

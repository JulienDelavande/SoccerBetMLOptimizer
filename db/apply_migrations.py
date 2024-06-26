import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from psycopg2 import sql, connect
from pathlib import Path

def apply_migration(engine, migration_file):
    with engine.connect() as conn:
        with open(migration_file, 'r') as file:
            migration_sql = file.read()
            conn.execute(text(migration_sql))
            conn.execute(
                text("""
                    INSERT INTO migration_history (migration_file)
                    VALUES (:migration_file)
                """),
                {'migration_file': os.path.basename(migration_file)}
            )
        conn.commit()

def get_applied_migrations(engine):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT migration_file FROM migration_history"))
        result = result.fetchall()
        return {tpl[0] for tpl in result}

def init_db():
    load_dotenv()
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_TN_MIGRATION_HISTORY = os.getenv('DB_TN_MIGRATION_HISTORY')

    MIGRATION_DIR = Path(__file__).parent / 'migrations'

    connection_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_url)


    # Create migration history table if not exists
    with engine.connect() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {DB_TN_MIGRATION_HISTORY} (
                id SERIAL PRIMARY KEY,
                migration_file VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

    applied_migrations = get_applied_migrations(engine)
    migration_files = sorted([f for f in os.listdir(MIGRATION_DIR) if f.endswith('.sql')])
    
    for migration_file in migration_files:
        if migration_file not in applied_migrations:
            print(f"Applying migration: {migration_file}")
            apply_migration(engine, os.path.join(MIGRATION_DIR, migration_file))
        else:
            print(f"Skipping already applied migration: {migration_file}")

if __name__ == "__main__":
    init_db()

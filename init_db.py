import os
from passlib.hash import bcrypt
from sqlalchemy import create_engine, text

APP_ROOT = os.path.dirname(__file__)
DEFAULT_SQLITE = f"sqlite:///{os.path.join(APP_ROOT, 'users.db')}"
DATABASE_URL = os.environ.get('DATABASE_URL') or DEFAULT_SQLITE


def init_db():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite:') else {})

    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            userid TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """))

        # insert default user with hashed password
        default_user = 'admin123'
        default_pass = 'Secret@123'
        hashed = bcrypt.hash(default_pass)
        # Use INSERT ... ON CONFLICT for Postgres, or INSERT OR IGNORE for sqlite
        if DATABASE_URL.startswith('sqlite:'):
            conn.execute(text("INSERT OR IGNORE INTO users (userid, password) VALUES (:u, :p)"), {"u": default_user, "p": hashed})
        else:
            # Postgres / others
            conn.execute(text("INSERT INTO users (userid, password) VALUES (:u, :p) ON CONFLICT (userid) DO NOTHING"), {"u": default_user, "p": hashed})

    print(f"DB initialized at: {DATABASE_URL}")


if __name__ == '__main__':
    init_db()

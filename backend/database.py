import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

def get_db():
    """
    Connects to Supabase. 
    RealDictCursor lets us access data by column name (like a dictionary).
    """
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()
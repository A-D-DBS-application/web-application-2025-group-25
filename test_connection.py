"""
Simple script to test Supabase connection
"""
import psycopg2
from psycopg2 import sql

# Test direct connection
print("Testing Supabase connection...")

conn = None

# Try connection pooler first (port 6543)
print("\n1. Trying connection pooler (port 6543)...")
try:
    conn = psycopg2.connect(
        host="db.hsjjntcivrvlguqfdqxl.supabase.co",
        port=6543,  # Connection pooler port
        database="postgres",
        user="postgres",
        password="5FJrydgxoSBBnqQV",
        connect_timeout=10,
        sslmode="require"
    )
    print("✓ Connection pooler works!")
except psycopg2.OperationalError as e:
    print(f"✗ Connection pooler failed: {e}")
    print("\n2. Trying direct connection (port 5432)...")
    try:
        conn = psycopg2.connect(
            host="db.hsjjntcivrvlguqfdqxl.supabase.co",
            port=5432,  # Direct connection port
            database="postgres",
            user="postgres",
            password="5FJrydgxoSBBnqQV",
            connect_timeout=10,
            sslmode="require"
        )
        print("✓ Direct connection works!")
    except psycopg2.OperationalError as e2:
        print(f"✗ Direct connection also failed: {e2}")
        raise e2

if conn:
    print("✓ Connection successful!")
    
    # Test query
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"✓ PostgreSQL version: {version[0]}")
    
    # Check if tables exist
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"\n✓ Found {len(tables)} tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    cur.close()
    conn.close()
    print("\n✓ Connection test completed successfully!")
    
except psycopg2.OperationalError as e:
    print(f"✗ Connection failed: {e}")
    print("\nPossible solutions:")
    print("1. Check if your IP is whitelisted in Supabase Dashboard > Settings > Database > Connection Pooling")
    print("2. Try using the connection pooler port (6543) instead of direct port (5432)")
    print("3. Get a fresh connection string from Supabase Dashboard > Settings > Database")
    print("4. Check your firewall/network settings")
    print("5. Try using Supabase's connection pooler URL if available")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()


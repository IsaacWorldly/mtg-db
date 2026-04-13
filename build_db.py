import requests
import sqlite3
import json
import os

DB_PATH = "mtg.db"

def read_sql_file(filename):
    """Read SQL file and return its contents"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Skipping structured table creation.")
        return None

# Step 1: Get the latest bulk card data metadata
print("Fetching bulk data metadata...")
bulk_url = "https://api.scryfall.com/bulk-data"
bulk_meta = requests.get(bulk_url).json()

# Find the "default_cards" bulk file (contains all non-digital, real MTG cards)
default_cards_uri = next(
    d["download_uri"] for d in bulk_meta["data"] if d["type"] == "default_cards"
)

print("Downloading card data...")
cards_json = requests.get(default_cards_uri).json()
print(f"Downloaded {len(cards_json)} cards.")

# Step 2: Create SQLite database
print("Creating database...")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Drop existing tables
cur.execute("DROP TABLE IF EXISTS cards")
cur.execute("DROP TABLE IF EXISTS cards_raw")

# Create raw JSON table
print("Creating cards_raw table...")
cur.execute("""
CREATE TABLE cards_raw (
    id TEXT PRIMARY KEY,
    json TEXT
)
""")

# Step 3: Insert raw JSON data
print("Inserting card data...")
for i, card in enumerate(cards_json):
    if i % 1000 == 0:
        print(f"Processed {i}/{len(cards_json)} cards...")
    
    cur.execute("""
    INSERT OR IGNORE INTO cards_raw (id, json)
    VALUES (?, ?)
    """, (
        card["id"],
        json.dumps(card)   # convert the whole card dict to a JSON string
    ))

print("Committing raw data...")
conn.commit()

# Step 4: Create structured cards table using SQL file
print("Creating structured cards table...")
sql_content = read_sql_file("create_cards_table.sql")

if sql_content:
    # Split the SQL file into individual statements
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    for statement in statements:
        if statement:
            try:
                cur.execute(statement)
                print(f"Executed: {statement[:50]}...")
            except Exception as e:
                print(f"Error executing statement: {e}")
                print(f"Statement: {statement[:100]}...")
    
    print("Committing structured data...")
    conn.commit()
else:
    print("Skipping structured table creation (SQL file not found)")

conn.close()

# Ensure decks + deck_cards tables exist (CREATE IF NOT EXISTS — preserves existing data)
print("Ensuring deck tables exist...")
from deck_ingest import ensure_tables, get_db
deck_conn = get_db()
ensure_tables(deck_conn)
deck_conn.close()

print(f"Database saved to {DB_PATH}")
print("Database build complete!")

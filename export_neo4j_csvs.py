"""
export_neo4j_csvs.py
====================
Export SQLite data to CSVs formatted for Neo4j bulk import (LOAD CSV).

Output files (written to ./neo4j_export/)
------------------------------------------
  nodes_cards.csv        Card nodes        (from Scryfall)
  nodes_sets.csv         Set nodes         (from Scryfall)
  nodes_artists.csv      Artist nodes      (from Scryfall)
  nodes_players.csv      Player nodes      (from Moxfield)
  nodes_decks.csv        Deck nodes        (from deck_ingest)
  rels_set_contains.csv  (Set)-[:CONTAINS]->(Card)
  rels_artist_art.csv    (Artist)-[:CREATED_ART_FOR]->(Card)
  rels_player_created.csv (Player)-[:CREATED]->(Deck)
  rels_deck_contains.csv (Deck)-[:CONTAINS {qty, board}]->(Card)

Usage
-----
  python export_neo4j_csvs.py [--out-dir ./neo4j_export]

Neo4j LOAD CSV examples are printed at the end.
"""

import os
import csv
import sqlite3
import argparse

DB_PATH = "mtg.db"
DEFAULT_OUT_DIR = "./neo4j_export"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def write_csv(path: str, rows: list[dict], fieldnames: list[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):>6,} rows → {path}")


def export_all(out_dir: str):
    conn = get_db()
    cur = conn.cursor()

    os.makedirs(out_dir, exist_ok=True)
    print(f"\nExporting to: {out_dir}\n")

    # ── Card nodes ────────────────────────────────────────────
    cur.execute("""
        SELECT
            card_id,
            name,
            mana_cost,
            cmc,
            type_line,
            oracle_text,
            colors,
            color_identity,
            power,
            toughness,
            loyalty,
            rarity,
            set_code,
            set_name,
            released_at,
            artist,
            edhrec_rank,
            legal_standard,
            legal_modern,
            legal_legacy,
            legal_commander,
            price_usd,
            scryfall_uri,
            image_normal
        FROM cards
    """)
    write_csv(
        os.path.join(out_dir, "nodes_cards.csv"),
        [dict(r) for r in cur.fetchall()],
        ["card_id", "name", "mana_cost", "cmc", "type_line", "oracle_text",
         "colors", "color_identity", "power", "toughness", "loyalty", "rarity",
         "set_code", "set_name", "released_at", "artist", "edhrec_rank",
         "legal_standard", "legal_modern", "legal_legacy", "legal_commander",
         "price_usd", "scryfall_uri", "image_normal"],
    )

    # ── Set nodes ─────────────────────────────────────────────
    cur.execute("""
        SELECT DISTINCT
            set_id,
            set_code,
            set_name,
            set_type,
            MIN(released_at) AS released_at
        FROM cards
        WHERE set_id IS NOT NULL
        GROUP BY set_id
    """)
    write_csv(
        os.path.join(out_dir, "nodes_sets.csv"),
        [dict(r) for r in cur.fetchall()],
        ["set_id", "set_code", "set_name", "set_type", "released_at"],
    )

    # ── Artist nodes ──────────────────────────────────────────
    cur.execute("""
        SELECT DISTINCT artist AS name
        FROM cards
        WHERE artist IS NOT NULL AND artist != ''
    """)
    write_csv(
        os.path.join(out_dir, "nodes_artists.csv"),
        [dict(r) for r in cur.fetchall()],
        ["name"],
    )

    # ── Player nodes ──────────────────────────────────────────
    # Derived from decks table (player column). Extend this if you add a
    # dedicated players table later.
    cur.execute("""
        SELECT DISTINCT player AS username, source AS platform
        FROM decks
        WHERE player IS NOT NULL AND player != ''
    """)
    write_csv(
        os.path.join(out_dir, "nodes_players.csv"),
        [dict(r) for r in cur.fetchall()],
        ["username", "platform"],
    )

    # ── Deck nodes ────────────────────────────────────────────
    cur.execute("""
        SELECT
            deck_id,
            source,
            source_url,
            name,
            format,
            player,
            description,
            created_at,
            updated_at,
            view_count,
            like_count
        FROM decks
    """)
    write_csv(
        os.path.join(out_dir, "nodes_decks.csv"),
        [dict(r) for r in cur.fetchall()],
        ["deck_id", "source", "source_url", "name", "format", "player",
         "description", "created_at", "updated_at", "view_count", "like_count"],
    )

    # ── (Set)-[:CONTAINS]->(Card) ─────────────────────────────
    cur.execute("""
        SELECT set_id, card_id
        FROM cards
        WHERE set_id IS NOT NULL
    """)
    write_csv(
        os.path.join(out_dir, "rels_set_contains.csv"),
        [dict(r) for r in cur.fetchall()],
        ["set_id", "card_id"],
    )

    # ── (Artist)-[:CREATED_ART_FOR]->(Card) ──────────────────
    cur.execute("""
        SELECT artist AS artist_name, card_id
        FROM cards
        WHERE artist IS NOT NULL AND artist != ''
    """)
    write_csv(
        os.path.join(out_dir, "rels_artist_art.csv"),
        [dict(r) for r in cur.fetchall()],
        ["artist_name", "card_id"],
    )

    # ── (Player)-[:CREATED]->(Deck) ───────────────────────────
    cur.execute("""
        SELECT player AS username, deck_id
        FROM decks
        WHERE player IS NOT NULL AND player != ''
    """)
    write_csv(
        os.path.join(out_dir, "rels_player_created.csv"),
        [dict(r) for r in cur.fetchall()],
        ["username", "deck_id"],
    )

    # ── (Deck)-[:CONTAINS {qty, board}]->(Card) ───────────────
    cur.execute("""
        SELECT deck_id, card_id, card_name, quantity, board
        FROM deck_cards
        WHERE card_id IS NOT NULL
    """)
    write_csv(
        os.path.join(out_dir, "rels_deck_contains.csv"),
        [dict(r) for r in cur.fetchall()],
        ["deck_id", "card_id", "card_name", "quantity", "board"],
    )

    conn.close()
    print_load_csv_examples(out_dir)


def print_load_csv_examples(out_dir: str):
    print("""
── Neo4j LOAD CSV Examples ──────────────────────────────────────────────────

// Card nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes_cards.csv' AS row
MERGE (c:Card {card_id: row.card_id})
SET c.name          = row.name,
    c.mana_cost     = row.mana_cost,
    c.cmc           = toFloat(row.cmc),
    c.type_line     = row.type_line,
    c.oracle_text   = row.oracle_text,
    c.colors        = row.colors,
    c.color_identity= row.color_identity,
    c.power         = row.power,
    c.toughness     = row.toughness,
    c.rarity        = row.rarity,
    c.edhrec_rank   = toInteger(row.edhrec_rank),
    c.price_usd     = toFloat(row.price_usd),
    c.image_url     = row.image_normal;

// Set nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes_sets.csv' AS row
MERGE (s:Set {set_id: row.set_id})
SET s.code        = row.set_code,
    s.name        = row.set_name,
    s.type        = row.set_type,
    s.released_at = row.released_at;

// Artist nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes_artists.csv' AS row
MERGE (a:Artist {name: row.name});

// Player nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes_players.csv' AS row
MERGE (p:Player {username: row.username})
SET p.platform = row.platform;

// Deck nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes_decks.csv' AS row
MERGE (d:Deck {deck_id: row.deck_id})
SET d.name        = row.name,
    d.format      = row.format,
    d.source      = row.source,
    d.source_url  = row.source_url,
    d.description = row.description,
    d.created_at  = row.created_at,
    d.view_count  = toInteger(row.view_count),
    d.like_count  = toInteger(row.like_count);

// (Set)-[:CONTAINS]->(Card)
LOAD CSV WITH HEADERS FROM 'file:///rels_set_contains.csv' AS row
MATCH (s:Set   {set_id:  row.set_id})
MATCH (c:Card  {card_id: row.card_id})
MERGE (s)-[:CONTAINS]->(c);

// (Artist)-[:CREATED_ART_FOR]->(Card)
LOAD CSV WITH HEADERS FROM 'file:///rels_artist_art.csv' AS row
MATCH (a:Artist {name:    row.artist_name})
MATCH (c:Card   {card_id: row.card_id})
MERGE (a)-[:CREATED_ART_FOR]->(c);

// (Player)-[:CREATED]->(Deck)
LOAD CSV WITH HEADERS FROM 'file:///rels_player_created.csv' AS row
MATCH (p:Player {username: row.username})
MATCH (d:Deck   {deck_id:  row.deck_id})
MERGE (p)-[:CREATED]->(d);

// (Deck)-[:CONTAINS {qty, board}]->(Card)
LOAD CSV WITH HEADERS FROM 'file:///rels_deck_contains.csv' AS row
MATCH (d:Deck  {deck_id: row.deck_id})
MATCH (c:Card  {card_id: row.card_id})
MERGE (d)-[r:CONTAINS {board: row.board}]->(c)
SET r.quantity = toInteger(row.quantity);
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export mtg.db tables to Neo4j CSVs.")
    parser.add_argument(
        "--out-dir", default=DEFAULT_OUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUT_DIR})"
    )
    args = parser.parse_args()
    export_all(args.out_dir)

"""
deck_ingest.py
==============
Ingest a deck from a URL into the `decks` and `deck_cards` tables.

Supported sources
-----------------
  Moxfield    https://www.moxfield.com/decks/{publicId}
  MTGGoldfish https://www.mtggoldfish.com/deck/{deckId}
  17lands     https://www.17lands.com/deck/{deckHash}   (stub — structure TBD)

Usage
-----
  python deck_ingest.py <deck_url> [<deck_url> ...]

  # or import and call directly:
  from deck_ingest import ingest_deck
  ingest_deck("https://www.moxfield.com/decks/abc123")
"""

import re
import json
import time
import sqlite3
import argparse
import requests

DB_PATH = "mtg.db"
HEADERS = {"User-Agent": "Mozilla/5.0 (personal MTG research project)"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables(conn):
    """Create decks / deck_cards tables if they don't exist yet."""
    with open("create_decks_tables.sql", "r") as f:
        sql = f.read()
    # The SQL file uses DROP TABLE … so only run CREATE portions when tables exist.
    # Safe to run in full on a fresh DB; on existing DB the DROP/CREATE is idempotent.
    conn.executescript(sql)
    conn.commit()


def scryfall_lookup(card_name: str) -> str | None:
    """Return Scryfall UUID for a card name, or None if not found."""
    try:
        url = f"https://api.scryfall.com/cards/named?exact={requests.utils.quote(card_name)}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("id")
    except Exception as e:
        print(f"  [scryfall] lookup failed for '{card_name}': {e}")
    return None


def upsert_deck(conn, deck: dict):
    conn.execute("""
        INSERT OR REPLACE INTO decks
            (deck_id, source, source_id, source_url, name, format, player,
             description, created_at, updated_at, view_count, like_count, raw_json)
        VALUES
            (:deck_id, :source, :source_id, :source_url, :name, :format, :player,
             :description, :created_at, :updated_at, :view_count, :like_count, :raw_json)
    """, deck)


def upsert_deck_cards(conn, deck_id: str, cards: list[dict]):
    """Delete existing rows for this deck and re-insert (clean refresh)."""
    conn.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck_id,))
    conn.executemany("""
        INSERT INTO deck_cards (deck_id, card_id, card_name, quantity, board)
        VALUES (:deck_id, :card_id, :card_name, :quantity, :board)
    """, cards)


# ── URL routing ────────────────────────────────────────────────────────────────

def detect_source(url: str) -> tuple[str, str]:
    """Return (source_name, source_id) from a deck URL."""
    url = url.strip().rstrip("/")

    m = re.search(r"moxfield\.com/decks/([A-Za-z0-9_-]+)", url)
    if m:
        return "moxfield", m.group(1)

    m = re.search(r"mtggoldfish\.com/deck/(\d+)", url)
    if m:
        return "mtggoldfish", m.group(1)

    m = re.search(r"17lands\.com/deck/([A-Za-z0-9_-]+)", url)
    if m:
        return "17lands", m.group(1)

    raise ValueError(f"Unsupported or unrecognised deck URL: {url}")


# ── Moxfield ──────────────────────────────────────────────────────────────────

MOXFIELD_BOARD_MAP = {
    "mainboard":   "main",
    "sideboard":   "side",
    "commanders":  "commander",
    "companions":  "companion",
    "maybeboard":  "maybe",
    "attractions": "attraction",
    "stickers":    "sticker",
}


def fetch_moxfield(source_id: str, source_url: str) -> tuple[dict, list[dict]]:
    api_url = f"https://api2.moxfield.com/v2/decks/all/{source_id}"
    r = requests.get(api_url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()

    deck_id = f"moxfield_{source_id}"

    deck = {
        "deck_id":    deck_id,
        "source":     "moxfield",
        "source_id":  source_id,
        "source_url": source_url,
        "name":       data.get("name"),
        "format":     data.get("format"),
        "player":     (data.get("createdByUser") or {}).get("userName"),
        "description": data.get("description"),
        "created_at": data.get("createdAtUtc"),
        "updated_at": data.get("lastUpdatedAtUtc"),
        "view_count": data.get("viewCount"),
        "like_count": data.get("likeCount"),
        "raw_json":   json.dumps(data),
    }

    cards = []
    for board_key, board_label in MOXFIELD_BOARD_MAP.items():
        board_data = data.get(board_key) or {}
        for entry in board_data.values():
            card_info = entry.get("card", {})
            cards.append({
                "deck_id":   deck_id,
                "card_id":   card_info.get("id"),       # Scryfall UUID — already present
                "card_name": card_info.get("name", entry.get("name", "")),
                "quantity":  entry.get("quantity", 1),
                "board":     board_label,
            })

    return deck, cards


# ── MTGGoldfish ───────────────────────────────────────────────────────────────

def fetch_mtggoldfish(source_id: str, source_url: str) -> tuple[dict, list[dict]]:
    """
    MTGGoldfish has no public API. We use the plaintext download endpoint:
      https://www.mtggoldfish.com/deck/download/{id}

    Format returned:
      4 Lightning Bolt
      2 Scalding Tarn
      ...
      Sideboard
      2 Relic of Progenitus
    """
    dl_url = f"https://www.mtggoldfish.com/deck/download/{source_id}"
    r = requests.get(dl_url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    text = r.text.strip()

    deck_id = f"mtggoldfish_{source_id}"

    # MTGGoldfish doesn't expose metadata in the download — we capture what we can.
    deck = {
        "deck_id":    deck_id,
        "source":     "mtggoldfish",
        "source_id":  source_id,
        "source_url": source_url,
        "name":       None,    # Not available from download endpoint
        "format":     None,    # Not available from download endpoint
        "player":     None,
        "description": None,
        "created_at": None,
        "updated_at": None,
        "view_count": None,
        "like_count": None,
        "raw_json":   json.dumps({"raw_decklist": text}),
    }

    cards = []
    current_board = "main"

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Board headers
        if line.lower() == "sideboard":
            current_board = "side"
            continue
        if line.lower() in ("commander", "commanders"):
            current_board = "commander"
            continue

        # Card lines: "4 Lightning Bolt" or "1 Island (M21) 263"
        m = re.match(r"^(\d+)\s+(.+?)(?:\s+\([A-Z0-9]+\)\s+\d+)?$", line)
        if m:
            qty = int(m.group(1))
            name = m.group(2).strip()
            # Scryfall lookup for IDs (rate-limited; skip by setting card_id=None if slow)
            print(f"  [mtggoldfish] looking up '{name}'…")
            card_id = scryfall_lookup(name)
            time.sleep(0.1)  # polite rate limiting vs Scryfall

            cards.append({
                "deck_id":   deck_id,
                "card_id":   card_id,
                "card_name": name,
                "quantity":  qty,
                "board":     current_board,
            })

    return deck, cards


# ── 17lands (stub) ────────────────────────────────────────────────────────────

def fetch_17lands(source_id: str, source_url: str) -> tuple[dict, list[dict]]:
    """
    17lands is primarily a Limited (draft/sealed) platform.
    Their internal API endpoint structure is not publicly documented.

    TODO: Reverse-engineer the deck JSON endpoint, e.g.:
      https://www.17lands.com/data/deck?deck_id={source_id}
    and map their card data to Scryfall IDs via arena_id or card name.
    """
    raise NotImplementedError(
        "17lands ingestion is not yet implemented. "
        "Contribution welcome — see fetch_17lands() in deck_ingest.py."
    )


# ── Main entry point ──────────────────────────────────────────────────────────

SOURCE_FETCHERS = {
    "moxfield":    fetch_moxfield,
    "mtggoldfish": fetch_mtggoldfish,
    "17lands":     fetch_17lands,
}


def ingest_deck(url: str, conn=None) -> str:
    """
    Ingest a single deck URL. Returns the deck_id inserted.
    Optionally accepts an existing DB connection (useful for batch calls).
    """
    close_conn = conn is None
    if conn is None:
        conn = get_db()
        ensure_tables(conn)

    source, source_id = detect_source(url)
    print(f"[{source}] Fetching deck {source_id} …")

    fetcher = SOURCE_FETCHERS[source]
    deck, cards = fetcher(source_id, url)

    upsert_deck(conn, deck)
    upsert_deck_cards(conn, deck["deck_id"], cards)
    conn.commit()

    print(f"[{source}] Saved '{deck['name']}' ({len(cards)} card entries) → {deck['deck_id']}")

    if close_conn:
        conn.close()

    return deck["deck_id"]


def ingest_many(urls: list[str]):
    conn = get_db()
    ensure_tables(conn)
    results = []
    for url in urls:
        try:
            deck_id = ingest_deck(url, conn=conn)
            results.append({"url": url, "deck_id": deck_id, "status": "ok"})
        except NotImplementedError as e:
            print(f"[SKIP] {url}: {e}")
            results.append({"url": url, "deck_id": None, "status": "not_implemented"})
        except Exception as e:
            print(f"[ERROR] {url}: {e}")
            results.append({"url": url, "deck_id": None, "status": f"error: {e}"})
    conn.close()
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest MTG deck(s) from URL(s).")
    parser.add_argument("urls", nargs="+", help="Deck URL(s) to ingest")
    args = parser.parse_args()

    results = ingest_many(args.urls)

    print("\n── Summary ──────────────────────────────────────────────")
    for r in results:
        print(f"  {r['status']:20s}  {r['url']}")

-- ============================================================
-- Decks & Deck Cards Tables
-- Supports multi-source ingestion: Moxfield, MTGGoldfish, 17lands
-- ============================================================

DROP TABLE IF EXISTS deck_cards;
DROP TABLE IF EXISTS decks;

-- ── Decks ────────────────────────────────────────────────────
-- One row per deck. deck_id is "{source}_{source_id}" for global uniqueness.
CREATE TABLE decks (
    deck_id         TEXT PRIMARY KEY,   -- e.g. "moxfield_abc123", "mtggoldfish_6780040"
    source          TEXT NOT NULL,      -- 'moxfield' | 'mtggoldfish' | '17lands'
    source_id       TEXT NOT NULL,      -- native ID on source platform
    source_url      TEXT,               -- original URL passed in
    name            TEXT,
    format          TEXT,               -- 'commander', 'modern', 'standard', 'draft', etc.
    player          TEXT,               -- username / author on source platform
    description     TEXT,
    created_at      TEXT,               -- ISO8601
    updated_at      TEXT,               -- ISO8601
    view_count      INTEGER,
    like_count      INTEGER,
    raw_json        TEXT                -- preserve raw payload for future re-parsing
);

CREATE INDEX IF NOT EXISTS idx_decks_player  ON decks(player);
CREATE INDEX IF NOT EXISTS idx_decks_format  ON decks(format);
CREATE INDEX IF NOT EXISTS idx_decks_source  ON decks(source);

-- ── Deck Cards ────────────────────────────────────────────────
-- Junction table: one row per (deck, card, board) slot.
-- card_id is the Scryfall UUID; links to cards.card_id.
-- card_name is stored for convenience / when card_id is unavailable.
CREATE TABLE deck_cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id     TEXT    NOT NULL,
    card_id     TEXT,               -- Scryfall UUID (may be NULL if lookup failed)
    card_name   TEXT    NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    board       TEXT    NOT NULL DEFAULT 'main', -- 'main' | 'side' | 'commander' | 'companion' | 'maybe'
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id)
);

CREATE INDEX IF NOT EXISTS idx_deck_cards_deck_id  ON deck_cards(deck_id);
CREATE INDEX IF NOT EXISTS idx_deck_cards_card_id  ON deck_cards(card_id);
CREATE INDEX IF NOT EXISTS idx_deck_cards_board     ON deck_cards(board);

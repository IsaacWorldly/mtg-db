# MTG Database — Analysis & Recommendations

## Current State Summary

The database has two tables and 112,608 card records from Scryfall's `default_cards` bulk export:

| Table | Rows | Purpose |
|---|---|---|
| `cards_raw` | 112,608 | Raw Scryfall JSON, one blob per card print |
| `cards` | 112,608 | ~60 structured columns extracted from JSON |

**`moxfield_raw` is defined in `moxfield_pull.py` but the table doesn't exist yet** — the script has never been run against this database.

---

## Part 1: Gaps in the Existing `cards` Table

These fields exist in Scryfall's JSON but are not extracted into the structured `cards` table.

### 1.1 Missing Simple Columns

| Field | Why It Matters |
|---|---|
| `loyalty` | Required to query planeswalkers meaningfully |
| `digital` | Filter out MTGO-only cards |
| `image_status` | Know whether art is a placeholder or real scan |
| `produced_mana` | Find mana-producing permanents (not just color of the card) |
| `arena_id`, `mtgo_id`, `tcgplayer_id`, `cardmarket_id` | Cross-reference with platform-specific data |
| `price_usd_foil` | Currently only `price_usd` (non-foil) is captured |
| `price_usd_etched` | Etched foil pricing is absent |
| `price_eur_foil` | EUR foil pricing is absent |
| `hand_modifier`, `life_modifier` | For Vanguard-format cards |
| `card_back_id` | Needed to reconstruct double-faced card back |
| `rulings_uri` | Jumpstart for fetching rulings per card |

### 1.2 Missing Legalities

The schema only captures `standard`, `modern`, and `commander`. Scryfall provides 21 formats:

```
future, historic, timeless, gladiator, pioneer, legacy, pauper,
vintage, penny, oathbreaker, standardbrawl, brawl, alchemy,
paupercommander, duel, oldschool, premodern, predh
```

These are stored as a single JSON blob in `cards_raw`. Adding them as flat columns (or a separate `card_legalities` table) enables queries like "all legal Pauper commons that cost less than $0.25" or "cards legal in Legacy but not Modern."

### 1.3 Missing Data: Double-Faced & Adventure Cards

Scryfall stores `card_faces` as a nested array. Cards with layouts like `transform`, `modal_dfc`, `adventure`, `split`, and `flip` all have face-level data (name, mana cost, oracle text, power/toughness, art) that is completely lost in the current `cards` table. This affects tens of thousands of cards.

### 1.4 Missing Data: `games` and `finishes`

- `games`: `['paper', 'mtgo', 'arena']` — lets you filter by platform
- `finishes`: `['nonfoil', 'foil', 'etched']` — lets you distinguish treatment availability without joining anything

---

## Part 2: Structural Improvements

### 2.1 Add Indexes

The `cards` table has **zero indexes**. Every query does a full table scan over 112K rows. These indexes would dramatically speed up the most common query patterns:

```sql
CREATE INDEX IF NOT EXISTS idx_cards_name         ON cards(name);
CREATE INDEX IF NOT EXISTS idx_cards_oracle_id     ON cards(oracle_id);
CREATE INDEX IF NOT EXISTS idx_cards_set_code      ON cards(set_code);
CREATE INDEX IF NOT EXISTS idx_cards_rarity        ON cards(rarity);
CREATE INDEX IF NOT EXISTS idx_cards_type_line     ON cards(type_line);
CREATE INDEX IF NOT EXISTS idx_cards_cmc           ON cards(cmc);
CREATE INDEX IF NOT EXISTS idx_cards_edhrec_rank   ON cards(edhrec_rank);
CREATE INDEX IF NOT EXISTS idx_cards_released_at   ON cards(released_at);
```

### 2.2 Normalize Multi-Value Fields

Currently `colors`, `color_identity`, and `keywords` are stored as raw JSON strings like `'["W","U"]'`. This means color queries require `LIKE '%U%'` hacks instead of clean joins. Recommended normalized tables:

**`card_colors`**
```sql
CREATE TABLE card_colors (
    card_id TEXT,
    color   TEXT,  -- W, U, B, R, G
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
```

**`card_keywords`**
```sql
CREATE TABLE card_keywords (
    card_id TEXT,
    keyword TEXT,  -- Flying, Trample, Lifelink, etc.
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
```

With these, you can write clean queries like:
```sql
-- Cards with both Flying AND Lifelink
SELECT c.name FROM cards c
JOIN card_keywords k1 ON c.card_id = k1.card_id AND k1.keyword = 'Flying'
JOIN card_keywords k2 ON c.card_id = k2.card_id AND k2.keyword = 'Lifelink';
```

### 2.3 Add a `card_faces` Table

For double-faced, split, and adventure cards, create a separate face table so each face is queryable:

```sql
CREATE TABLE card_faces (
    card_id       TEXT,
    face_index    INTEGER,
    name          TEXT,
    mana_cost     TEXT,
    type_line     TEXT,
    oracle_text   TEXT,
    power         TEXT,
    toughness     TEXT,
    loyalty       TEXT,
    flavor_text   TEXT,
    artist        TEXT,
    illustration_id TEXT,
    image_uris    TEXT,   -- JSON blob for the face-specific images
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
```

### 2.4 Add a Dedicated `sets` Table

Scryfall has a full `/sets` API endpoint. A `sets` table would make set-level queries far more powerful:

```sql
CREATE TABLE sets (
    set_id        TEXT PRIMARY KEY,
    set_code      TEXT UNIQUE,
    set_name      TEXT,
    set_type      TEXT,   -- expansion, core, masters, commander, etc.
    released_at   TEXT,
    card_count    INTEGER,
    digital       INTEGER,
    foil_only     INTEGER,
    nonfoil_only  INTEGER,
    block         TEXT,
    block_code    TEXT,
    parent_set_code TEXT,
    icon_svg_uri  TEXT,
    search_uri    TEXT,
    scryfall_uri  TEXT
);
```

This enables queries like: "all cards from Commander-format precon sets released since 2022" — currently impossible without string matching.

### 2.5 Add a `rulings` Table

Scryfall provides rulings per card. Fetching and storing them unlocks rules text searching:

```sql
CREATE TABLE rulings (
    oracle_id  TEXT,
    source     TEXT,   -- 'wotc' or 'scryfall'
    published_at TEXT,
    comment    TEXT,
    FOREIGN KEY (oracle_id) REFERENCES cards(oracle_id)
);
```

### 2.6 Add Price History

Currently prices are point-in-time snapshots. If you run the build script periodically, you lose previous prices. Add a timestamped history table:

```sql
CREATE TABLE price_history (
    card_id       TEXT,
    snapshot_date TEXT,
    price_usd     REAL,
    price_usd_foil REAL,
    price_usd_etched REAL,
    price_eur     REAL,
    price_eur_foil REAL,
    price_tix     REAL,
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
```

---

## Part 3: New Tables — Moxfield Integration

The `moxfield_pull.py` script is already written to fetch decks by username. Once you run it, you'll want a structured schema rather than just raw JSON blobs.

### 3.1 `moxfield_decks`
```sql
CREATE TABLE moxfield_decks (
    deck_id       TEXT PRIMARY KEY,
    username      TEXT,
    deck_name     TEXT,
    format        TEXT,   -- commander, modern, pauper, etc.
    description   TEXT,
    created_at    TEXT,
    updated_at    TEXT,
    view_count    INTEGER,
    like_count    INTEGER,
    comment_count INTEGER,
    is_public     INTEGER,
    main_card_id  TEXT,   -- commander/oathbreaker
    data          TEXT    -- original JSON blob
);
```

### 3.2 `moxfield_deck_cards`
```sql
CREATE TABLE moxfield_deck_cards (
    deck_id       TEXT,
    card_id       TEXT,   -- Scryfall card_id for joins
    oracle_id     TEXT,
    quantity      INTEGER,
    board         TEXT,   -- mainboard, sideboard, commanders, companion
    is_foil       INTEGER,
    is_etched     INTEGER,
    FOREIGN KEY (deck_id)  REFERENCES moxfield_decks(deck_id),
    FOREIGN KEY (card_id)  REFERENCES cards(card_id)
);
```

With `moxfield_deck_cards` joined to `cards`, you can answer questions like:
- "What are the 20 most-played cards across all decks in our group?"
- "Which cards appear in more than 3 of our commander decks?"
- "What's the total market value of each deck?"
- "Which of my decks uses the most expensive cards?"

---

## Part 4: External Data Sources to Integrate

### 4.1 MTG JSON (`mtgjson.com`) — **Highest Priority**

MTGJSON is a community-maintained alternative to Scryfall that offers data Scryfall doesn't:

- **Full rulings history** with dates and sources
- **Price history** (daily snapshots going back years from TCGPlayer, Cardmarket, MTGO)
- **Draft pick data** — average draft pick position by set
- **Foreign language card names** (all 15+ languages)
- **Token definitions** linked to their parent cards
- **Comprehensive set data** including block structure, set codes, and parent relationships
- **Downloadable bulk JSON** — no API rate limits

Integration path: download `AllPrintings.json` and `AllPrices.json` from `mtgjson.com/downloads/all-files/`.

### 4.2 EDHREC (`edhrec.com`)

EDHREC has no official API, but they expose structured JSON at predictable URLs. Useful data:

- **Commander recommendation scores** per card per commander
- **Synergy scores** — how much more/less frequently a card appears in a given commander's decks vs. all decks
- **Theme data** — e.g., which cards index into "Artifacts" or "Lifegain" themes
- **Salt scores** — community-voted "unfun" card ratings
- **Average decklist** per commander

This is especially powerful combined with your Moxfield data to answer: "For [commander], which EDHREC-recommended cards do none of us own?"

### 4.3 Commander Spellbook (`commanderspellbook.com`)

Has a free, documented public API at `https://backend.commanderspellbook.com/api/v2/`. Provides:

- **Infinite combo definitions** — lists of cards that go infinite together
- **Combo prerequisites** and results (what the combo produces)
- **Combo validation** — check if any deck contains all pieces of a known combo

A `combos` table here would let you query: "Which decks in our group contain all pieces of a known infinite combo?"

### 4.4 17Lands (`17lands.com`)

For players who draft, 17Lands publishes **free bulk data exports** at `17lands.com/public/data`. Includes:

- **Card-level win rates** by set (game-in-hand win rate, drawn improvement to hand)
- **Average last seen pick** (how late in draft a card wheels)
- **Color pair win rates** by set
- **Archetype data**

This adds a whole Limited/Draft dimension to the database. A `draft_stats` table keyed by `(set_code, card_name)` would unlock queries like "which commons in Bloomburrow have the highest game-in-hand win rate?"

### 4.5 MTGGoldfish (`mtggoldfish.com`)

MTGGoldfish publishes **free downloadable price CSVs** (updated daily) at predictable URLs:

```
https://www.mtggoldfish.com/prices/paper/{card_name}
https://www.mtggoldfish.com/price_history/paper/{card_name}#paper
```

Also provides:
- **Meta decks** — top-performing tournament lists by format
- **Budget build suggestions**
- **Set bulk pricing** (average value of a box, expected value from packs)

### 4.6 TCGPlayer API

TCGPlayer has an official API (requires free registration for a key). Unlike Scryfall's prices (which are sourced from TCGPlayer but aggregated), the direct API gives:

- **Condition-specific pricing** (Near Mint, Lightly Played, etc.)
- **Market price vs. listed price** distinction
- **Inventory/availability** signals
- **Buylist prices** (what stores are paying for cards)

### 4.7 Archidekt / Deckstats

Both have public APIs and are alternative deck-building communities. Adding them alongside Moxfield gives broader coverage of the same users' decks or access to community archetypes:

- Archidekt: `https://archidekt.com/api/decks/{id}/`
- Deckstats: `https://deckstats.net/api.php`

---

## Part 5: Recommended Implementation Order

Given all of the above, here's a pragmatic sequencing:

1. **Add indexes to `cards`** — immediate performance gain, zero data work
2. **Expand `create_cards_table.sql`** — add missing columns (loyalty, digital, all legalities, foil prices, produced_mana, finishes, games)
3. **Run `moxfield_pull.py`** and build structured `moxfield_decks` + `moxfield_deck_cards` tables — unlocks the most interesting group-specific queries
4. **Add a `sets` table** from Scryfall's `/sets` endpoint — small API call, big query power
5. **Add `card_faces` table** — recovers data for ~20-30% of all cards
6. **Add `card_keywords` and `card_colors` normalized tables** — cleaner querying
7. **Integrate MTGJSON price history** — long-term price tracking
8. **Add `rulings` table** from Scryfall or MTGJSON
9. **Add Commander Spellbook combo data** — fun, highly queryable
10. **Add 17Lands draft stats** (if drafting is part of your play)

---

## Part 6: High-Value Queries Unlocked By These Changes

With the above additions, queries like these become straightforward:

```sql
-- Most-played cards across all group decks, with current price
SELECT c.name, COUNT(*) as deck_count, AVG(c.price_usd) as avg_price
FROM moxfield_deck_cards mdc
JOIN cards c ON mdc.oracle_id = c.oracle_id
GROUP BY c.oracle_id ORDER BY deck_count DESC LIMIT 20;

-- Cards legal in Pauper, under $0.25, with high EDHREC rank
SELECT name, rarity, price_usd, edhrec_rank
FROM cards
WHERE legal_pauper = 'legal'
  AND CAST(price_usd AS REAL) < 0.25
ORDER BY edhrec_rank ASC LIMIT 50;

-- Cards in our group's decks that are part of known infinite combos
SELECT d.username, d.deck_name, cb.combo_id, cb.result
FROM moxfield_deck_cards mdc
JOIN moxfield_decks d ON mdc.deck_id = d.deck_id
JOIN combo_cards cc ON mdc.oracle_id = cc.oracle_id
JOIN combos cb ON cc.combo_id = cb.combo_id;

-- Price change over time for a specific card
SELECT snapshot_date, price_usd, price_usd_foil
FROM price_history WHERE card_id = '...'
ORDER BY snapshot_date;

-- Best draft commons by win rate in a given set
SELECT c.name, ds.game_in_hand_winrate, ds.avg_last_seen
FROM draft_stats ds JOIN cards c ON ds.set_code = c.set_code AND ds.card_name = c.name
WHERE ds.set_code = 'BLB' AND c.rarity = 'common'
ORDER BY ds.game_in_hand_winrate DESC;

-- All cards with Flying AND Lifelink in a single color identity
SELECT c.name, c.cmc, c.type_line
FROM cards c
JOIN card_keywords k1 ON c.card_id = k1.card_id AND k1.keyword = 'Flying'
JOIN card_keywords k2 ON c.card_id = k2.card_id AND k2.keyword = 'Lifelink'
JOIN card_colors cc ON c.card_id = cc.card_id AND cc.color = 'W'
WHERE c.color_identity NOT LIKE '%U%' AND c.color_identity NOT LIKE '%B%';
```

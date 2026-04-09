DROP TABLE IF EXISTS cards;
CREATE TABLE cards AS
SELECT
    -- ── Identity ───────────────────────────────────────────────────────────
    json_extract(json, '$.object')     AS object_type,
    json_extract(json, '$.id')         AS card_id,
    json_extract(json, '$.oracle_id')  AS oracle_id,
    json_extract(json, '$.name')       AS name,
    json_extract(json, '$.lang')       AS lang,
    json_extract(json, '$.released_at') AS released_at,
    json_extract(json, '$.layout')     AS layout,

    -- ── External platform IDs (Part 1.1) ──────────────────────────────────
    json_extract(json, '$.arena_id')       AS arena_id,
    json_extract(json, '$.mtgo_id')        AS mtgo_id,
    json_extract(json, '$.tcgplayer_id')   AS tcgplayer_id,
    json_extract(json, '$.cardmarket_id')  AS cardmarket_id,

    -- ── Gameplay stats ─────────────────────────────────────────────────────
    json_extract(json, '$.mana_cost')      AS mana_cost,
    json_extract(json, '$.cmc')            AS cmc,
    json_extract(json, '$.type_line')      AS type_line,
    json_extract(json, '$.oracle_text')    AS oracle_text,
    json_extract(json, '$.power')          AS power,
    json_extract(json, '$.toughness')      AS toughness,
    json_extract(json, '$.loyalty')        AS loyalty,        -- planeswalkers (Part 1.1)
    json_extract(json, '$.hand_modifier')  AS hand_modifier,  -- Vanguard (Part 1.1)
    json_extract(json, '$.life_modifier')  AS life_modifier,  -- Vanguard (Part 1.1)
    json_extract(json, '$.colors')         AS colors,
    json_extract(json, '$.color_identity') AS color_identity,
    json_extract(json, '$.produced_mana')  AS produced_mana,  -- mana sources (Part 1.1)
    json_extract(json, '$.keywords')       AS keywords,

    -- ── Print flags ────────────────────────────────────────────────────────
    json_extract(json, '$.reserved')       AS reserved,
    json_extract(json, '$.game_changer')   AS game_changer,
    json_extract(json, '$.digital')        AS digital,        -- MTGO-only cards (Part 1.1)
    json_extract(json, '$.foil')           AS foil,
    json_extract(json, '$.nonfoil')        AS nonfoil,
    json_extract(json, '$.finishes')       AS finishes,       -- nonfoil/foil/etched array (Part 1.4)
    json_extract(json, '$.games')          AS games,          -- paper/mtgo/arena array (Part 1.4)
    json_extract(json, '$.oversized')      AS oversized,
    json_extract(json, '$.promo')          AS promo,
    json_extract(json, '$.reprint')        AS reprint,
    json_extract(json, '$.variation')      AS variation,

    -- ── Set info ───────────────────────────────────────────────────────────
    json_extract(json, '$.set_id')          AS set_id,
    json_extract(json, '$.set')             AS set_code,
    json_extract(json, '$.set_name')        AS set_name,
    json_extract(json, '$.set_type')        AS set_type,
    json_extract(json, '$.collector_number') AS collector_number,
    json_extract(json, '$.rarity')          AS rarity,

    -- ── Card presentation ──────────────────────────────────────────────────
    json_extract(json, '$.flavor_text')    AS flavor_text,
    json_extract(json, '$.artist')         AS artist,
    json_extract(json, '$.illustration_id') AS illustration_id,
    json_extract(json, '$.border_color')   AS border_color,
    json_extract(json, '$.frame')          AS frame,
    json_extract(json, '$.security_stamp') AS security_stamp,
    json_extract(json, '$.full_art')       AS full_art,
    json_extract(json, '$.textless')       AS textless,
    json_extract(json, '$.booster')        AS booster,
    json_extract(json, '$.story_spotlight') AS story_spotlight,
    json_extract(json, '$.highres_image')  AS highres_image,
    json_extract(json, '$.image_status')   AS image_status,   -- scan quality (Part 1.1)
    json_extract(json, '$.card_back_id')   AS card_back_id,   -- DFC back face (Part 1.1)

    -- ── Images ─────────────────────────────────────────────────────────────
    json_extract(json, '$.image_uris.small')       AS image_small,
    json_extract(json, '$.image_uris.normal')      AS image_normal,
    json_extract(json, '$.image_uris.large')       AS image_large,
    json_extract(json, '$.image_uris.png')         AS image_png,
    json_extract(json, '$.image_uris.art_crop')    AS image_art_crop,
    json_extract(json, '$.image_uris.border_crop') AS image_border_crop,

    -- ── Multi-face data (Part 1.3) ─────────────────────────────────────────
    -- Stored as a JSON blob; Part 2 (card_faces table) will normalize these.
    -- NULL for single-faced cards; populated for DFC, split, adventure, flip, etc.
    json_extract(json, '$.card_faces') AS card_faces,

    -- ── Pricing (Part 1.1) ─────────────────────────────────────────────────
    json_extract(json, '$.prices.usd')        AS price_usd,
    json_extract(json, '$.prices.usd_foil')   AS price_usd_foil,   -- added
    json_extract(json, '$.prices.usd_etched') AS price_usd_etched,  -- added
    json_extract(json, '$.prices.eur')        AS price_eur,
    json_extract(json, '$.prices.eur_foil')   AS price_eur_foil,    -- added
    json_extract(json, '$.prices.tix')        AS price_tix,

    -- ── Legalities — all 21 formats (Part 1.2) ─────────────────────────────
    json_extract(json, '$.legalities.standard')       AS legal_standard,
    json_extract(json, '$.legalities.future')         AS legal_future,
    json_extract(json, '$.legalities.historic')       AS legal_historic,
    json_extract(json, '$.legalities.timeless')       AS legal_timeless,
    json_extract(json, '$.legalities.gladiator')      AS legal_gladiator,
    json_extract(json, '$.legalities.pioneer')        AS legal_pioneer,
    json_extract(json, '$.legalities.modern')         AS legal_modern,
    json_extract(json, '$.legalities.legacy')         AS legal_legacy,
    json_extract(json, '$.legalities.pauper')         AS legal_pauper,
    json_extract(json, '$.legalities.vintage')        AS legal_vintage,
    json_extract(json, '$.legalities.penny')          AS legal_penny,
    json_extract(json, '$.legalities.commander')      AS legal_commander,
    json_extract(json, '$.legalities.oathbreaker')    AS legal_oathbreaker,
    json_extract(json, '$.legalities.standardbrawl')  AS legal_standardbrawl,
    json_extract(json, '$.legalities.brawl')          AS legal_brawl,
    json_extract(json, '$.legalities.alchemy')        AS legal_alchemy,
    json_extract(json, '$.legalities.paupercommander') AS legal_paupercommander,
    json_extract(json, '$.legalities.duel')           AS legal_duel,
    json_extract(json, '$.legalities.oldschool')      AS legal_oldschool,
    json_extract(json, '$.legalities.premodern')      AS legal_premodern,
    json_extract(json, '$.legalities.predh')          AS legal_predh,

    -- ── Rankings ────────────────────────────────────────────────────────────
    json_extract(json, '$.edhrec_rank') AS edhrec_rank,
    json_extract(json, '$.penny_rank')  AS penny_rank,

    -- ── URIs ────────────────────────────────────────────────────────────────
    json_extract(json, '$.uri')                       AS uri,
    json_extract(json, '$.scryfall_uri')              AS scryfall_uri,
    json_extract(json, '$.rulings_uri')               AS rulings_uri,        -- added (Part 1.1)
    json_extract(json, '$.related_uris.gatherer')     AS uri_gatherer,
    json_extract(json, '$.related_uris.edhrec')       AS uri_edhrec,
    json_extract(json, '$.purchase_uris.tcgplayer')   AS purchase_tcgplayer,
    json_extract(json, '$.purchase_uris.cardmarket')  AS purchase_cardmarket

FROM cards_raw;
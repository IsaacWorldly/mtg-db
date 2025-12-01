# 🛠️ DB Browser for SQLite - Quick Start Guide

A quick reference guide for using DB Browser for SQLite with the MTG database.

## Installation

### macOS
```bash
brew install --cask db-browser-for-sqlite
```

### Windows
Download from: https://sqlitebrowser.org/

### Linux
```bash
# Ubuntu/Debian
sudo apt-get install sqlitebrowser

# Fedora
sudo dnf install sqlitebrowser
```

## Opening the Database

1. Launch DB Browser for SQLite
2. Click **"Open Database"**
3. Navigate to your project folder
4. Select `mtg.db`

## Essential Workflows

### Browse All Cards
1. Click **"Browse Data"** tab
2. Select `cards` table from dropdown
3. Use column filters to search
4. Click column headers to sort

### Run a Query
1. Click **"Execute SQL"** tab
2. Type your SQL query
3. Press **F5** or click "Execute SQL"
4. View results in bottom panel
5. Export if needed (CSV, JSON, etc.)

### Explore Schema
1. Click **"Database Structure"** tab
2. Expand tables to see columns
3. Right-click for options (Browse, Copy CREATE, etc.)

## Useful SQL Queries for MTG Database

### Basic Card Search
```sql
-- Find cards by name
SELECT name, mana_cost, type_line, rarity
FROM cards
WHERE name LIKE '%Lightning%'
ORDER BY name;
```

### Rarity Analysis
```sql
-- Rarity distribution
SELECT rarity, COUNT(*) as count
FROM cards
GROUP BY rarity
ORDER BY count DESC;
```

### Set Exploration
```sql
-- Cards from a specific set
SELECT name, mana_cost, type_line, rarity
FROM cards
WHERE set_name = 'The Lord of the Rings: Tales of Middle-earth'
ORDER BY name;
```

### Oracle Text Search
```sql
-- Find cards with specific abilities
SELECT name, mana_cost, oracle_text
FROM cards
WHERE oracle_text LIKE '%draw%card%'
LIMIT 50;
```

### Creature Power Analysis
```sql
-- Find powerful creatures
SELECT name, mana_cost, power, toughness, type_line
FROM cards
WHERE power IS NOT NULL
  AND CAST(power AS INTEGER) >= 5
ORDER BY CAST(power AS INTEGER) DESC
LIMIT 20;
```

### Color Identity Search
```sql
-- Find multicolor cards
SELECT name, mana_cost, colors, color_identity
FROM cards
WHERE colors LIKE '%U%' AND colors LIKE '%R%'
ORDER BY name;
```

### Price Analysis
```sql
-- Most expensive cards
SELECT name, usd, eur, tix, set_name
FROM cards
WHERE usd IS NOT NULL
ORDER BY CAST(usd AS REAL) DESC
LIMIT 20;
```

### Recent Releases
```sql
-- Latest cards
SELECT name, set_name, released_at, rarity
FROM cards
WHERE released_at >= '2024-01-01'
ORDER BY released_at DESC
LIMIT 50;
```

### Type Analysis
```sql
-- Count by card type
SELECT 
    CASE 
        WHEN type_line LIKE '%Creature%' THEN 'Creature'
        WHEN type_line LIKE '%Instant%' THEN 'Instant'
        WHEN type_line LIKE '%Sorcery%' THEN 'Sorcery'
        WHEN type_line LIKE '%Enchantment%' THEN 'Enchantment'
        WHEN type_line LIKE '%Artifact%' THEN 'Artifact'
        WHEN type_line LIKE '%Planeswalker%' THEN 'Planeswalker'
        WHEN type_line LIKE '%Land%' THEN 'Land'
        ELSE 'Other'
    END as card_type,
    COUNT(*) as count
FROM cards
GROUP BY card_type
ORDER BY count DESC;
```

## Keyboard Shortcuts

- **F5**: Execute SQL query
- **Ctrl+F** / **Cmd+F**: Find in editor
- **Ctrl+Enter**: Execute current line/selection
- **F7**: Query history

## Exporting Data

1. Run your query
2. In results panel, click **"Export"** button
3. Choose format: CSV, JSON, SQL, Excel
4. Select destination and save

## Tips

- **Use LIMIT** for large queries to avoid freezing
- **Save queries** as `.sql` files for reuse
- **Create indexes** on frequently queried columns
- **Backup database** before making structural changes
- **Use transactions** (BEGIN/COMMIT) for data modifications

## Troubleshooting

**Database locked?**
- Close Streamlit app or other connections

**Query too slow?**
- Add indexes: `CREATE INDEX idx_name ON cards(name);`
- Use LIMIT clauses
- Filter early in WHERE clause

**Large result sets?**
- Export to file instead of viewing in app
- Use pagination with LIMIT/OFFSET


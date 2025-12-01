# 🃏 MTG Database Explorer

A comprehensive Magic: The Gathering card database with a Streamlit web interface. This project builds a local SQLite database using the [Scryfall API](https://scryfall.com/docs/api) and provides an interactive web app for exploring MTG cards.

## ✨ Features

- **🗄️ Dual Database Structure**: Raw JSON storage + structured tables for optimal performance
- **🌐 Streamlit Web Interface**: Interactive web app with multiple tabs
- **🔍 Advanced Search**: Search by name, type, oracle text, or set
- **📝 Custom SQL Queries**: Write and execute your own SQL queries
- **🗄️ Database Explorer**: Dynamic table/column browser with data types
- **🔄 Refresh Data**: Update database with latest Scryfall data
- **🌐 Scryfall Integration**: Direct links to Scryfall for detailed card info
- **📊 Statistics & Charts**: Visual database statistics and card distributions
- **⚡ Quick Query Generator**: Auto-generate SQL queries for any table
- **🛠️ DB Browser for SQLite**: Professional database exploration tool (recommended for advanced users)

## 🚀 Quick Start

### 1. Setup Environment

**Windows:**
```cmd
py -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Build Database
```bash
# Windows
.venv\Scripts\python.exe build_db.py

# macOS/Linux
python build_db.py
```

### 4. Launch Web App
```bash
# Windows
.venv\Scripts\streamlit.exe run streamlit_app.py

# macOS/Linux
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

### 5. (Optional) Install DB Browser for SQLite

For more robust database exploration, we recommend **DB Browser for SQLite** - a powerful, free, open-source tool for exploring and managing SQLite databases.

> **Note:** DB Browser for SQLite is a standalone desktop application and does NOT require Python packages. It works independently with your `mtg.db` file. The Python packages in `requirements.txt` (like `sqlalchemy` and `tabulate`) are optional utilities that enhance Python-based database operations and work alongside DB Browser.

**Download & Install:**
- **macOS**: Download from [sqlitebrowser.org](https://sqlitebrowser.org/) or use Homebrew:
  ```bash
  brew install --cask db-browser-for-sqlite
  ```
- **Windows**: Download installer from [sqlitebrowser.org](https://sqlitebrowser.org/)
- **Linux**: 
  ```bash
  # Ubuntu/Debian
  sudo apt-get install sqlitebrowser
  
  # Fedora
  sudo dnf install sqlitebrowser
  ```

**Quick Start with DB Browser:**
1. Open DB Browser for SQLite
2. Click "Open Database" and select `mtg.db` from your project directory
3. Explore tables, run queries, and analyze data with the visual interface

See the [🛠️ DB Browser Guide](#-db-browser-for-sqlite-guide) section below for detailed usage instructions.

## 📁 Project Structure

```
mtg-db/
├── streamlit_app.py          # Main Streamlit web application
├── build_db.py              # Database builder with dual-table structure
├── create_cards_table.sql   # SQL schema for structured cards table
├── query_cards.py           # Example query script
├── moxfield_pull.py         # Moxfield deck data fetcher
├── requirements.txt         # Python dependencies
├── mtg.db                   # SQLite database (created after build)
├── README.md               # This file
└── DB_BROWSER_QUICK_START.md # Quick reference for DB Browser for SQLite
```

## 🗄️ Database Structure

### Tables Created:
- **`cards_raw`**: Raw JSON data from Scryfall API
- **`cards`**: Structured table with 50+ extracted columns including:
  - Basic info (name, mana_cost, type_line, oracle_text)
  - Images (small, normal, large, art_crop)
  - Pricing (USD, EUR, TIX)
  - Legality (Standard, Modern, Commander)
  - Set information and metadata

## 🌐 Web Interface Tabs

### 🔍 Quick Search
- Search cards by name, type, oracle text, or set
- Real-time filtering and results display

### 📝 Custom Query
- Write and execute custom SQL queries
- Example queries included
- Syntax highlighting and error handling

### 🎯 Card Lookup
- Detailed card information display
- Direct Scryfall integration
- JSON data viewer

### 🗄️ Database Explorer
- **Dynamic table browser** with row counts
- **Column information** with data types and constraints
- **Sample data** preview (first 3 rows)
- **Quick query generator** for any table
- **Advanced query options** (COUNT, DISTINCT, PRAGMA)

### 📊 Database Stats
- Card count and distribution statistics
- Rarity distribution charts
- Recent sets information
- Visual analytics

## 🔧 Usage Examples

### Search for Cards
```sql
-- Find all blue instants that draw cards
SELECT name, mana_cost, oracle_text
FROM cards
WHERE type_line LIKE '%Instant%'
  AND oracle_text LIKE '%draw%'
  AND colors LIKE '%U%'
LIMIT 20;
```

### Get Card Statistics
```sql
-- Rarity distribution
SELECT rarity, COUNT(*) as count
FROM cards
GROUP BY rarity
ORDER BY count DESC;
```

### Find Recent Cards
```sql
-- Latest cards from recent sets
SELECT name, set_name, released_at
FROM cards
WHERE released_at >= '2024-01-01'
ORDER BY released_at DESC
LIMIT 10;
```

## 🛠️ Advanced Features

### Refresh Database
Use the "🔄 Refresh Database" button in the web app to update with latest Scryfall data.

### Custom Queries
The Database Explorer tab provides:
- Auto-generated SELECT queries
- COUNT and DISTINCT examples
- Table structure queries (PRAGMA)

### Scryfall Integration
- Click "🌐 Open Scryfall" to browse cards online
- Direct links from card lookups
- Seamless integration with official MTG database

## 🛠️ DB Browser for SQLite Guide

**DB Browser for SQLite** is a powerful, free tool that provides professional-grade database exploration capabilities beyond what the Streamlit web interface offers.

### Why Use DB Browser?

- **Visual Schema Browser**: See all tables, columns, indexes, and relationships at a glance
- **Advanced Query Builder**: Build complex queries visually without writing SQL
- **Data Editing**: Edit, add, or delete records directly in the interface
- **Export Capabilities**: Export query results to CSV, JSON, SQL, or Excel
- **Query History**: Keep track of all your queries for easy reuse
- **Performance Analysis**: View query execution plans and optimize performance
- **Better for Large Datasets**: More efficient handling of large result sets

### Opening Your Database

1. Launch DB Browser for SQLite
2. Click **"Open Database"** (or File → Open Database)
3. Navigate to your project directory and select `mtg.db`
4. The database structure will appear in the left sidebar

### Key Features for MTG Database Exploration

#### 1. Browse Database Structure
- Click on the **"Database Structure"** tab
- Expand tables to see all columns with data types
- View indexes and triggers
- Right-click tables for options like "Browse Table" or "Copy CREATE statement"

#### 2. Browse Table Data
- Select a table (e.g., `cards` or `cards_raw`)
- Click the **"Browse Data"** tab
- View all records in a spreadsheet-like interface
- Use filters to search within columns
- Sort by clicking column headers
- Edit data directly (be careful with raw JSON data!)

#### 3. Execute SQL Queries
- Click the **"Execute SQL"** tab
- Write your SQL queries in the editor
- Use syntax highlighting and auto-completion
- Click **"Execute SQL"** (F5) to run queries
- Results appear in the bottom panel
- Export results using the toolbar buttons

#### 4. Useful Query Examples

**Find cards by name pattern:**
```sql
SELECT name, mana_cost, type_line, rarity
FROM cards
WHERE name LIKE '%Lightning%'
ORDER BY name;
```

**Explore rarity distribution:**
```sql
SELECT rarity, COUNT(*) as count
FROM cards
GROUP BY rarity
ORDER BY count DESC;
```

**Find cards from a specific set:**
```sql
SELECT name, mana_cost, type_line, rarity
FROM cards
WHERE set_name = 'The Lord of the Rings: Tales of Middle-earth'
ORDER BY name;
```

**Search oracle text:**
```sql
SELECT name, mana_cost, oracle_text
FROM cards
WHERE oracle_text LIKE '%draw%card%'
LIMIT 50;
```

**Complex query - Find powerful creatures:**
```sql
SELECT name, mana_cost, power, toughness, type_line
FROM cards
WHERE power IS NOT NULL
  AND toughness IS NOT NULL
  AND CAST(power AS INTEGER) >= 5
ORDER BY CAST(power AS INTEGER) DESC, CAST(toughness AS INTEGER) DESC
LIMIT 20;
```

#### 5. Export Data
- After running a query, use the **"Export"** button in the results panel
- Choose format: CSV, JSON, SQL, Excel, etc.
- Perfect for sharing results or importing into other tools

#### 6. Query History
- Access previous queries via **View → Query History**
- Save frequently used queries for quick access
- Organize queries by creating saved query files

#### 7. Database Statistics
- Use **Tools → Database Statistics** to get overview of your database
- See table sizes, row counts, and storage information
- Useful for understanding database structure

### Tips & Tricks

1. **Use Filters in Browse Data**: Click the filter icon in column headers to quickly filter data
2. **Save Queries**: Save your favorite queries as `.sql` files for reuse
3. **Use Transactions**: For data modifications, use transactions (BEGIN/COMMIT) to ensure data integrity
4. **Index Optimization**: Create indexes on frequently queried columns for better performance
5. **Backup First**: Always backup your database before making structural changes

### Keyboard Shortcuts

- **F5**: Execute SQL query
- **Ctrl+F** (Cmd+F on Mac): Find in SQL editor
- **Ctrl+Enter**: Execute current line/selection
- **F7**: Open query history

### Troubleshooting

- **Database is locked**: Close the Streamlit app or any other connections to the database
- **Query too slow**: Add indexes on frequently filtered columns
- **Large result sets**: Use LIMIT clauses or export to file for better performance

## 📊 Performance

- **Database Size**: ~750MB for complete MTG card database
- **Query Speed**: Structured tables provide fast queries
- **Memory Usage**: Optimized for local development
- **Caching**: Streamlit caching for improved performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [Scryfall](https://scryfall.com/) for the amazing MTG API
- [Streamlit](https://streamlit.io/) for the web framework
- [Wizards of the Coast](https://company.wizards.com/) for Magic: The Gathering
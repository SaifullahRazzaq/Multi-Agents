# Database Inspection Guide

This guide shows you how to view and manage your SQLite database.

## Method 1: Using the Custom Viewer Script (Easiest) ⭐

I've created a Python script that displays all your database contents in a readable format.

### Usage

```bash
cd backend
./venv/bin/python view_db.py
```

### What It Shows

- **Users Table**: All registered users with their preferences and activity
- **Messages Table**: Last 10 messages with user questions and agent responses
- **Transactions Table**: All Stripe payment transactions
- **Analytics Table**: Page view counts
- **Summary Statistics**: Total counts and agent usage breakdown

### Current Database Contents

```
📊 USERS TABLE
ID: 123
  Voice Preference: en-US-Standard-C
  Message Count: 3
  First Seen: 2025-11-27 17:32:36
  Last Seen: 2025-11-27 17:34:28

💬 MESSAGES TABLE (Last 10 of 3 total)
1. Math Agent: "What is 8 times 7?" → "56"
2. Science Agent: "What causes rain?" → "Water evaporates..."
3. Science Agent: "hello" → "Hello. Do you have a science question..."

📈 ANALYTICS
Page Views: 4

📊 SUMMARY
- Total Users: 1
- Total Messages: 3
- Total Transactions: 0
- Agent Usage: math (1), science (2)
```

## Method 2: Using SQLite Command Line

### Install SQLite (if not already installed)

```bash
# macOS (usually pre-installed)
sqlite3 --version

# If not installed:
brew install sqlite
```

### Open the Database

```bash
cd backend
sqlite3 sql_app.db
```

### Useful SQLite Commands

```sql
-- List all tables
.tables

-- Show table schema
.schema users
.schema messages
.schema transactions
.schema analytics

-- View all users
SELECT * FROM users;

-- View recent messages
SELECT id, user_id, agent_id, timestamp 
FROM messages 
ORDER BY timestamp DESC 
LIMIT 10;

-- View messages with full content
SELECT user_message, agent_reply 
FROM messages 
WHERE user_id = '123' 
ORDER BY timestamp DESC;

-- Count messages by agent
SELECT agent_id, COUNT(*) as count 
FROM messages 
GROUP BY agent_id;

-- View all transactions
SELECT * FROM transactions;

-- View analytics
SELECT * FROM analytics;

-- Exit SQLite
.quit
```

### Formatted Output

```bash
# Enable column mode for better readability
sqlite3 sql_app.db
.mode column
.headers on
SELECT * FROM users;
```

## Method 3: Using DB Browser for SQLite (GUI)

### Install

```bash
# macOS
brew install --cask db-browser-for-sqlite
```

### Usage

1. Open DB Browser for SQLite
2. Click "Open Database"
3. Navigate to `/Users/waleedjawaid/Documents/Agentic/backend/sql_app.db`
4. Browse tables in the "Browse Data" tab
5. Run custom SQL queries in the "Execute SQL" tab

## Method 4: Using Python Interactive Shell

```bash
cd backend
./venv/bin/python
```

```python
from database import SessionLocal
import models

db = SessionLocal()

# Get all users
users = db.query(models.User).all()
for user in users:
    print(f"User {user.id}: {user.message_count} messages")

# Get recent messages
messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(5).all()
for msg in messages:
    print(f"{msg.agent_id}: {msg.user_message[:50]}")

# Get analytics
analytics = db.query(models.Analytics).first()
print(f"Page views: {analytics.page_views}")

db.close()
```

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | String | User ID (primary key) |
| voice_preference | String | Selected TTS voice |
| first_seen | DateTime | First visit timestamp |
| last_seen | DateTime | Last activity timestamp |
| message_count | Integer | Total messages sent |

### Messages Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Message ID (auto-increment) |
| user_id | String | Foreign key to users |
| agent_id | String | Which agent handled it |
| user_message | Text | User's question |
| agent_reply | Text | Agent's response |
| timestamp | DateTime | When message was sent |

### Transactions Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Transaction ID |
| session_id | String | Stripe session ID (unique) |
| amount | Float | Payment amount |
| currency | String | Currency code (e.g., "usd") |
| user_id | String | Foreign key to users |
| timestamp | DateTime | Payment timestamp |
| status | String | Payment status |

### Analytics Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Analytics ID |
| page_views | Integer | Total page views |

## Common Queries

### Find Most Active Users

```sql
SELECT id, message_count, last_seen 
FROM users 
ORDER BY message_count DESC 
LIMIT 10;
```

### Get Conversation History for a User

```sql
SELECT timestamp, agent_id, user_message, agent_reply 
FROM messages 
WHERE user_id = '123' 
ORDER BY timestamp ASC;
```

### Calculate Total Revenue

```sql
SELECT SUM(amount) as total_revenue, COUNT(*) as transaction_count 
FROM transactions 
WHERE status = 'completed';
```

### Agent Performance Stats

```sql
SELECT 
    agent_id,
    COUNT(*) as total_messages,
    COUNT(DISTINCT user_id) as unique_users
FROM messages 
GROUP BY agent_id 
ORDER BY total_messages DESC;
```

## Backup Your Database

```bash
# Create a backup
cd backend
cp sql_app.db sql_app_backup_$(date +%Y%m%d_%H%M%S).db

# Or export to SQL
sqlite3 sql_app.db .dump > backup.sql
```

## Clear Database (Development Only)

```bash
# Delete the database file
cd backend
rm sql_app.db

# Restart the backend - it will create a fresh database
./venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

## Production Database (PostgreSQL)

When deployed to production with PostgreSQL, use these tools:

### Using psql (PostgreSQL CLI)

```bash
# Connect to database
psql $DATABASE_URL

# List tables
\dt

# View table
SELECT * FROM users;

# Exit
\q
```

### Using pgAdmin (GUI)

1. Download from https://www.pgadmin.org/
2. Add your Supabase/Render database connection
3. Browse tables visually

## Troubleshooting

### Database Locked Error

If you get "database is locked":
1. Make sure the backend server is stopped
2. Close any SQLite browser applications
3. Try again

### Permission Denied

```bash
# Fix permissions
cd backend
chmod 644 sql_app.db
```

### Database File Not Found

The database is created automatically when you first start the backend. If it doesn't exist:
1. Start the backend server
2. Make a test API call
3. The database will be created

---

**Quick Reference**: Use `./venv/bin/python view_db.py` for the easiest way to view your data!

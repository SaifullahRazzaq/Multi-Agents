-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    voice_preference VARCHAR DEFAULT 'en-US-Standard-C',
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0
);

-- Create Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    agent_id VARCHAR,
    user_message TEXT,
    agent_reply TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR UNIQUE,
    amount FLOAT,
    currency VARCHAR,
    user_id VARCHAR REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR
);

-- Create Analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    page_views INTEGER DEFAULT 0
);

-- Initialize Analytics row
INSERT INTO analytics (id, page_views) VALUES (1, 0) ON CONFLICT DO NOTHING;

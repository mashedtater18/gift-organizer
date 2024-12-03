-- schema.sql

-- Create the Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

-- Create the Gift Recipients table
CREATE TABLE recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    budget REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create the Gifts table
CREATE TABLE gifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    planned_cost REAL DEFAULT 0,
    actual_cost REAL DEFAULT 0,
    purchased BOOLEAN DEFAULT 0,
    arrived BOOLEAN DEFAULT 0,
    wrapped BOOLEAN DEFAULT 0,
    given BOOLEAN DEFAULT 0,
    FOREIGN KEY (recipient_id) REFERENCES recipients (id)
);

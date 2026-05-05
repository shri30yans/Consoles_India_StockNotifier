-- Migration: create app_users table with UNIQUE(email) constraint.
-- Run this if your database was initialized before this table was added.
-- Safe to run multiple times (IF NOT EXISTS / idempotent).

CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL
);

-- Only add index if UNIQUE(email) constraint does not already provide it.
-- The UNIQUE constraint above creates an implicit btree index, so a
-- separate idx_app_users_email is redundant. See recommended_indexes.sql
-- for the note about skipping this if UNIQUE(email) exists.

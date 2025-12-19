-- PostgreSQL Initialization Script
-- This script runs automatically when the container is first created

-- Create database for t4alerts_backend (user authentication system)
CREATE DATABASE t4alerts;

-- Grant all privileges to postgres user on t4alerts database
GRANT ALL PRIVILEGES ON DATABASE t4alerts TO postgres;

-- The default 'postgres' database is already created and used by the scraping system
-- for storing alerted_errors table

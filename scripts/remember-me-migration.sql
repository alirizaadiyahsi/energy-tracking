-- Migration to add remember_me column to sessions table
-- Run this migration to support "Remember Me" functionality

-- Add remember_me column to sessions table
ALTER TABLE auth.sessions 
ADD COLUMN remember_me BOOLEAN NOT NULL DEFAULT false;

-- Create index for better performance on remember_me queries  
CREATE INDEX idx_sessions_remember_me ON auth.sessions(remember_me);

-- Update existing sessions with longer expiration to mark them as remember_me sessions
-- This is a best-effort attempt to identify existing long-lived sessions
UPDATE auth.sessions 
SET remember_me = true 
WHERE expires_at > NOW() + INTERVAL '7 days';

-- Add comment to document the change
COMMENT ON COLUMN auth.sessions.remember_me IS 'Indicates if this session was created with "Remember Me" option, affecting token and session expiration times';

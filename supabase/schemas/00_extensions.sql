-- =============================================================================
-- EXTENSIONS SETUP
-- =============================================================================
-- PostgreSQL extensions required for the Slow Burn application
-- This must be loaded first as other schemas depend on these extensions
-- =============================================================================

-- Create a dedicated schema for extensions to avoid polluting the public schema
CREATE SCHEMA IF NOT EXISTS extensions;

-- Grant usage on extensions schema to authenticated users
-- This allows users to use the vector types and functions
GRANT USAGE ON SCHEMA extensions TO authenticated;
GRANT USAGE ON SCHEMA extensions TO service_role;

-- Enable UUID extension in public schema (standard practice for uuid-ossp)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

-- Enable vector extension in dedicated extensions schema for security
-- This prevents namespace pollution and provides better security boundaries
CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA extensions;

-- Comment on the extensions schema
COMMENT ON SCHEMA extensions IS 'Dedicated schema for PostgreSQL extensions to maintain security isolation';
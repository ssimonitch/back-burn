-- =============================================================================
-- SHARED FUNCTIONS
-- =============================================================================
-- Cross-table utility functions used by multiple tables
-- Includes timestamp management and other shared functionality
-- =============================================================================

-- Function to automatically update updated_at timestamp
-- Used by multiple tables that track modification times
-- SECURITY: Uses empty search_path to prevent search path manipulation attacks
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.update_updated_at_column() IS 'Trigger function to automatically update the updated_at timestamp when a row is modified';
-- Add deleted_at column to plans table for soft deletes
ALTER TABLE public.plans 
ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Create index for filtering non-deleted plans
CREATE INDEX idx_plans_deleted_at ON public.plans(deleted_at) 
WHERE deleted_at IS NULL;

-- Add comment
COMMENT ON COLUMN public.plans.deleted_at IS 'Timestamp when plan was soft-deleted. NULL means plan is active/not deleted.';
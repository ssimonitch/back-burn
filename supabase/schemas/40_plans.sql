-- =============================================================================
-- PLANS TABLE
-- =============================================================================
-- Versioned workout plan templates that can be followed by users or shared publicly
-- Plans are immutable once created - modifications create new versions
-- =============================================================================

-- Plans table (workout plan templates)
CREATE TABLE IF NOT EXISTS public.plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    training_style TEXT REFERENCES public.training_styles(name) ON DELETE RESTRICT,
    goal TEXT,
    difficulty_level TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    duration_weeks INTEGER CHECK (duration_weeks > 0),
    days_per_week INTEGER CHECK (days_per_week >= 1 AND days_per_week <= 7),
    is_public BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    -- Versioning fields for immutable plan history
    version_number INTEGER NOT NULL DEFAULT 1,
    parent_plan_id UUID REFERENCES public.plans(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    -- Ensure unique versioning per user and plan name
    UNIQUE(user_id, name, version_number)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_plans_user_id ON public.plans(user_id);
CREATE INDEX IF NOT EXISTS idx_plans_is_public ON public.plans(is_public) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_plans_parent ON public.plans(parent_plan_id);
CREATE INDEX IF NOT EXISTS idx_plans_training_style ON public.plans(training_style);
CREATE INDEX IF NOT EXISTS idx_plans_deleted_at ON public.plans(deleted_at) WHERE deleted_at IS NULL;

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.plans IS 'Versioned workout plan templates that can be followed by users or shared publicly. Plans are immutable once created - modifications create new versions.';
COMMENT ON COLUMN public.plans.training_style IS 'Primary training style/methodology for this plan (references training_styles.name)';
COMMENT ON COLUMN public.plans.goal IS 'Primary training goal this plan targets (e.g., "strength", "hypertrophy", "weight_loss")';
COMMENT ON COLUMN public.plans.duration_weeks IS 'Planned duration in weeks before progression or plan change';
COMMENT ON COLUMN public.plans.days_per_week IS 'Intended training frequency per week';
COMMENT ON COLUMN public.plans.is_public IS 'Whether this plan can be discovered and used by other users';
COMMENT ON COLUMN public.plans.metadata IS 'Additional plan configuration like periodization, rest weeks, deload protocols';
COMMENT ON COLUMN public.plans.version_number IS 'Version number for this plan iteration (increments with each modification)';
COMMENT ON COLUMN public.plans.parent_plan_id IS 'References the original plan this version derives from (NULL for v1)';
COMMENT ON COLUMN public.plans.is_active IS 'Whether this is the current active version of the plan (only one version per plan name should be active)';
COMMENT ON COLUMN public.plans.deleted_at IS 'Timestamp when plan was soft-deleted. NULL means plan is active/not deleted.';
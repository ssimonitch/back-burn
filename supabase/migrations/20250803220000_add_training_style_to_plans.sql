-- Add training_style column to plans table
-- This column references the training_styles reference table to categorize plans

ALTER TABLE public.plans 
ADD COLUMN training_style TEXT;

-- Add foreign key constraint to ensure valid training style references
ALTER TABLE public.plans 
ADD CONSTRAINT plans_training_style_fkey 
FOREIGN KEY (training_style) 
REFERENCES public.training_styles(name) 
ON DELETE RESTRICT;

-- Create index for training_style filtering
CREATE INDEX IF NOT EXISTS idx_plans_training_style 
ON public.plans(training_style);

-- Add comment for the new column
COMMENT ON COLUMN public.plans.training_style IS 'Primary training style/methodology for this plan (references training_styles.name)';
-- =============================================================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================================================
-- RLS policies must be in migrations due to Supabase declarative schema limitations
-- See: https://supabase.com/docs/guides/local-development/declarative-database-schemas#known-caveats
-- =============================================================================

-- =============================================================================
-- PROFILES TABLE POLICIES
-- =============================================================================

CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can insert own profile" ON public.profiles
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = id);

-- =============================================================================
-- EXERCISES TABLE POLICIES
-- =============================================================================

-- Exercises are public read for all authenticated users
CREATE POLICY "Authenticated users can view exercises" ON public.exercises
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

-- =============================================================================
-- PLANS TABLE POLICIES
-- =============================================================================

CREATE POLICY "Users can view own plans" ON public.plans
    FOR SELECT USING ((SELECT auth.uid()) = user_id OR is_public = true);

CREATE POLICY "Users can create own plans" ON public.plans
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own plans" ON public.plans
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own plans" ON public.plans
    FOR DELETE USING ((SELECT auth.uid()) = user_id);

-- =============================================================================
-- PLAN_EXERCISES TABLE POLICIES
-- =============================================================================

CREATE POLICY "Users can view plan exercises" ON public.plan_exercises
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.plans
            WHERE plans.id = plan_exercises.plan_id
            AND (plans.user_id = (SELECT auth.uid()) OR plans.is_public = true)
        )
    );

CREATE POLICY "Users can insert own plan exercises" ON public.plan_exercises
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.plans
            WHERE plans.id = plan_exercises.plan_id
            AND plans.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY "Users can update own plan exercises" ON public.plan_exercises
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.plans
            WHERE plans.id = plan_exercises.plan_id
            AND plans.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY "Users can delete own plan exercises" ON public.plan_exercises
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.plans
            WHERE plans.id = plan_exercises.plan_id
            AND plans.user_id = (SELECT auth.uid())
        )
    );

-- =============================================================================
-- WORKOUT_SESSIONS TABLE POLICIES
-- =============================================================================

CREATE POLICY "Users can view own workout sessions" ON public.workout_sessions
    FOR SELECT USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own workout sessions" ON public.workout_sessions
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own workout sessions" ON public.workout_sessions
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own workout sessions" ON public.workout_sessions
    FOR DELETE USING ((SELECT auth.uid()) = user_id);

-- =============================================================================
-- SETS TABLE POLICIES
-- =============================================================================

CREATE POLICY "Users can view own sets" ON public.sets
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.workout_sessions
            WHERE workout_sessions.id = sets.workout_session_id
            AND workout_sessions.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY "Users can insert own sets" ON public.sets
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.workout_sessions
            WHERE workout_sessions.id = sets.workout_session_id
            AND workout_sessions.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY "Users can update own sets" ON public.sets
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.workout_sessions
            WHERE workout_sessions.id = sets.workout_session_id
            AND workout_sessions.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY "Users can delete own sets" ON public.sets
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.workout_sessions
            WHERE workout_sessions.id = sets.workout_session_id
            AND workout_sessions.user_id = (SELECT auth.uid())
        )
    );

-- =============================================================================
-- CONVERSATIONS TABLE POLICIES
-- =============================================================================

CREATE POLICY "Users can view own conversations" ON public.conversations
    FOR SELECT USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own conversations" ON public.conversations
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own conversations" ON public.conversations
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

-- =============================================================================
-- MEMORIES TABLE POLICIES
-- =============================================================================

CREATE POLICY "Users can view own memories" ON public.memories
    FOR SELECT USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own memories" ON public.memories
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own memories" ON public.memories
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own memories" ON public.memories
    FOR DELETE USING ((SELECT auth.uid()) = user_id);

-- =============================================================================
-- REFERENCE TABLE POLICIES
-- =============================================================================
-- Reference tables are read-only for all authenticated users

CREATE POLICY "Authenticated users can view movement patterns" ON public.movement_patterns
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view muscle groups" ON public.muscle_groups
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view equipment types" ON public.equipment_types
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view training styles" ON public.training_styles
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

-- =============================================================================
-- JUNCTION TABLE POLICIES
-- =============================================================================
-- Junction tables are read-only for all authenticated users

CREATE POLICY "Authenticated users can view exercise movement patterns" ON public.exercise_movement_patterns
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view exercise muscles" ON public.exercise_muscles
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view exercise training styles" ON public.exercise_training_styles
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view exercise relationships" ON public.exercise_relationships
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

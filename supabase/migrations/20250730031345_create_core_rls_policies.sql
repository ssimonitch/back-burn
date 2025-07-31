-- Profiles table policies
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can insert own profile" ON public.profiles
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = id);

-- Exercises table policies (public read for all authenticated users)
CREATE POLICY "Authenticated users can view exercises" ON public.exercises
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

-- Plans table policies
CREATE POLICY "Users can view own plans" ON public.plans
    FOR SELECT USING ((SELECT auth.uid()) = user_id OR is_public = true);

CREATE POLICY "Users can create own plans" ON public.plans
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own plans" ON public.plans
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own plans" ON public.plans
    FOR DELETE USING ((SELECT auth.uid()) = user_id);

-- Plan_exercises table policies - avoid overlapping policies with FOR ALL
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

-- Workout_sessions table policies
CREATE POLICY "Users can view own workout sessions" ON public.workout_sessions
    FOR SELECT USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own workout sessions" ON public.workout_sessions
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own workout sessions" ON public.workout_sessions
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own workout sessions" ON public.workout_sessions
    FOR DELETE USING ((SELECT auth.uid()) = user_id);

-- Sets table policies - Split FOR ALL into separate operations
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

-- Conversations table policies
CREATE POLICY "Users can view own conversations" ON public.conversations
    FOR SELECT USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own conversations" ON public.conversations
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own conversations" ON public.conversations
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

-- Memories table policies
CREATE POLICY "Users can view own memories" ON public.memories
    FOR SELECT USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own memories" ON public.memories
    FOR INSERT WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own memories" ON public.memories
    FOR UPDATE USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own memories" ON public.memories
    FOR DELETE USING ((SELECT auth.uid()) = user_id);

-- Reference tables policies (read-only for authenticated users)
CREATE POLICY "Authenticated users can view movement patterns" ON public.movement_patterns
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view muscle groups" ON public.muscle_groups
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view equipment types" ON public.equipment_types
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view training styles" ON public.training_styles
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

-- Junction tables policies (read access for authenticated users)
CREATE POLICY "Authenticated users can view exercise movement patterns" ON public.exercise_movement_patterns
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view exercise muscles" ON public.exercise_muscles
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view exercise training styles" ON public.exercise_training_styles
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');

CREATE POLICY "Authenticated users can view exercise relationships" ON public.exercise_relationships
    FOR SELECT USING ((SELECT auth.role()) = 'authenticated');
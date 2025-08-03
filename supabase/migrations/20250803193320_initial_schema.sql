create extension if not exists "vector" with schema "extensions";


create table "public"."conversations" (
    "id" uuid not null default uuid_generate_v4(),
    "user_id" uuid not null,
    "started_at" timestamp with time zone not null default now(),
    "ended_at" timestamp with time zone,
    "context" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."conversations" enable row level security;

create table "public"."equipment_types" (
    "id" uuid not null default uuid_generate_v4(),
    "name" text not null,
    "category" text,
    "description" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."equipment_types" enable row level security;

create table "public"."exercise_movement_patterns" (
    "id" uuid not null default uuid_generate_v4(),
    "exercise_id" uuid not null,
    "movement_pattern_id" uuid not null,
    "is_primary" boolean default true,
    "created_at" timestamp with time zone default now()
);


alter table "public"."exercise_movement_patterns" enable row level security;

create table "public"."exercise_muscles" (
    "id" uuid not null default uuid_generate_v4(),
    "exercise_id" uuid not null,
    "muscle_group_id" uuid not null,
    "muscle_role" text not null,
    "activation_level" integer,
    "created_at" timestamp with time zone default now()
);


alter table "public"."exercise_muscles" enable row level security;

create table "public"."exercise_relationships" (
    "id" uuid not null default uuid_generate_v4(),
    "parent_exercise_id" uuid not null,
    "related_exercise_id" uuid not null,
    "relationship_type" text not null,
    "notes" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."exercise_relationships" enable row level security;

create table "public"."exercise_training_styles" (
    "id" uuid not null default uuid_generate_v4(),
    "exercise_id" uuid not null,
    "training_style_id" uuid not null,
    "suitability_score" integer not null,
    "optimal_rep_min" integer,
    "optimal_rep_max" integer,
    "notes" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."exercise_training_styles" enable row level security;

create table "public"."exercises" (
    "id" uuid not null default uuid_generate_v4(),
    "name" text not null,
    "description" text,
    "instructions" text[],
    "tips" text[],
    "primary_equipment_id" uuid,
    "secondary_equipment_id" uuid,
    "force_vector" text,
    "exercise_category" text,
    "mechanic_type" text,
    "body_region" text,
    "difficulty_level" text,
    "laterality" text,
    "load_type" text,
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."exercises" enable row level security;

create table "public"."memories" (
    "id" uuid not null default uuid_generate_v4(),
    "user_id" uuid not null,
    "conversation_id" uuid,
    "content" text not null,
    "embedding" halfvec(3072),
    "memory_type" text,
    "importance_score" numeric(3,2),
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."memories" enable row level security;

create table "public"."movement_patterns" (
    "id" uuid not null default uuid_generate_v4(),
    "name" text not null,
    "description" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."movement_patterns" enable row level security;

create table "public"."muscle_groups" (
    "id" uuid not null default uuid_generate_v4(),
    "name" text not null,
    "muscle_region" text not null,
    "description" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."muscle_groups" enable row level security;

create table "public"."plan_exercises" (
    "id" uuid not null default uuid_generate_v4(),
    "plan_id" uuid not null,
    "exercise_id" uuid not null,
    "day_of_week" integer not null,
    "order_in_day" integer not null,
    "sets" integer not null,
    "target_reps" integer[] not null,
    "rest_seconds" integer,
    "notes" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."plan_exercises" enable row level security;

create table "public"."plans" (
    "id" uuid not null default uuid_generate_v4(),
    "user_id" uuid not null,
    "name" text not null,
    "description" text,
    "goal" text,
    "difficulty_level" text,
    "duration_weeks" integer,
    "days_per_week" integer,
    "is_public" boolean default false,
    "metadata" jsonb default '{}'::jsonb,
    "version_number" integer not null default 1,
    "parent_plan_id" uuid,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now()
);


alter table "public"."plans" enable row level security;

create table "public"."profiles" (
    "id" uuid not null,
    "username" text not null,
    "full_name" text,
    "age" integer,
    "fitness_level" text,
    "goals" text[],
    "preferences" jsonb default '{}'::jsonb,
    "affinity_score" integer default 0,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."profiles" enable row level security;

create table "public"."sets" (
    "id" uuid not null default uuid_generate_v4(),
    "workout_session_id" uuid not null,
    "exercise_id" uuid not null,
    "set_number" integer not null,
    "weight" numeric(10,2),
    "reps" integer not null,
    "rest_taken_seconds" integer,
    "rpe" integer,
    "volume_load" numeric(12,2) generated always as ((weight * (reps)::numeric)) stored,
    "tempo" text,
    "range_of_motion_quality" text,
    "form_quality" integer,
    "estimated_1rm" numeric(10,2),
    "intensity_percentage" numeric(5,2),
    "set_type" text,
    "reps_in_reserve" integer,
    "reached_failure" boolean default false,
    "failure_type" text,
    "equipment_variation" text,
    "assistance_type" text,
    "notes" text,
    "technique_cues" text[],
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."sets" enable row level security;

create table "public"."training_styles" (
    "id" uuid not null default uuid_generate_v4(),
    "name" text not null,
    "description" text,
    "typical_rep_range" text,
    "typical_set_range" text,
    "rest_periods" text,
    "focus_description" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."training_styles" enable row level security;

create table "public"."workout_sessions" (
    "id" uuid not null default uuid_generate_v4(),
    "user_id" uuid not null,
    "plan_id" uuid,
    "started_at" timestamp with time zone not null default now(),
    "completed_at" timestamp with time zone,
    "notes" text,
    "mood" text,
    "overall_rpe" integer,
    "pre_workout_energy" integer,
    "post_workout_energy" integer,
    "workout_type" text,
    "training_phase" text,
    "total_volume" numeric(12,2),
    "total_sets" integer,
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."workout_sessions" enable row level security;

CREATE UNIQUE INDEX conversations_pkey ON public.conversations USING btree (id);

CREATE UNIQUE INDEX equipment_types_name_key ON public.equipment_types USING btree (name);

CREATE UNIQUE INDEX equipment_types_pkey ON public.equipment_types USING btree (id);

CREATE UNIQUE INDEX exercise_movement_patterns_exercise_id_movement_pattern_id_key ON public.exercise_movement_patterns USING btree (exercise_id, movement_pattern_id);

CREATE UNIQUE INDEX exercise_movement_patterns_pkey ON public.exercise_movement_patterns USING btree (id);

CREATE UNIQUE INDEX exercise_muscles_exercise_id_muscle_group_id_key ON public.exercise_muscles USING btree (exercise_id, muscle_group_id);

CREATE UNIQUE INDEX exercise_muscles_pkey ON public.exercise_muscles USING btree (id);

CREATE UNIQUE INDEX exercise_relationships_parent_exercise_id_related_exercise__key ON public.exercise_relationships USING btree (parent_exercise_id, related_exercise_id, relationship_type);

CREATE UNIQUE INDEX exercise_relationships_pkey ON public.exercise_relationships USING btree (id);

CREATE UNIQUE INDEX exercise_training_styles_exercise_id_training_style_id_key ON public.exercise_training_styles USING btree (exercise_id, training_style_id);

CREATE UNIQUE INDEX exercise_training_styles_pkey ON public.exercise_training_styles USING btree (id);

CREATE UNIQUE INDEX exercises_name_primary_equipment_id_key ON public.exercises USING btree (name, primary_equipment_id);

CREATE UNIQUE INDEX exercises_pkey ON public.exercises USING btree (id);

CREATE INDEX idx_conversations_started_at ON public.conversations USING btree (started_at DESC);

CREATE INDEX idx_conversations_user_id ON public.conversations USING btree (user_id);

CREATE INDEX idx_exercise_movement_patterns_exercise ON public.exercise_movement_patterns USING btree (exercise_id);

CREATE INDEX idx_exercise_movement_patterns_pattern ON public.exercise_movement_patterns USING btree (movement_pattern_id);

CREATE INDEX idx_exercise_muscles_exercise ON public.exercise_muscles USING btree (exercise_id);

CREATE INDEX idx_exercise_muscles_muscle ON public.exercise_muscles USING btree (muscle_group_id);

CREATE INDEX idx_exercise_muscles_role ON public.exercise_muscles USING btree (muscle_role);

CREATE INDEX idx_exercise_relationships_parent ON public.exercise_relationships USING btree (parent_exercise_id);

CREATE INDEX idx_exercise_relationships_related ON public.exercise_relationships USING btree (related_exercise_id);

CREATE INDEX idx_exercise_relationships_type ON public.exercise_relationships USING btree (relationship_type);

CREATE INDEX idx_exercise_training_styles_exercise ON public.exercise_training_styles USING btree (exercise_id);

CREATE INDEX idx_exercise_training_styles_style ON public.exercise_training_styles USING btree (training_style_id);

CREATE INDEX idx_exercises_body_region ON public.exercises USING btree (body_region);

CREATE INDEX idx_exercises_category ON public.exercises USING btree (exercise_category);

CREATE INDEX idx_exercises_primary_equipment ON public.exercises USING btree (primary_equipment_id);

CREATE INDEX idx_memories_conversation_id ON public.memories USING btree (conversation_id);

CREATE INDEX idx_memories_embedding ON public.memories USING hnsw (embedding halfvec_l2_ops);

CREATE INDEX idx_memories_memory_type ON public.memories USING btree (memory_type);

CREATE INDEX idx_memories_user_id ON public.memories USING btree (user_id);

CREATE INDEX idx_plan_exercises_day ON public.plan_exercises USING btree (day_of_week);

CREATE INDEX idx_plan_exercises_exercise_id ON public.plan_exercises USING btree (exercise_id);

CREATE INDEX idx_plan_exercises_plan_id ON public.plan_exercises USING btree (plan_id);

CREATE INDEX idx_plans_is_public ON public.plans USING btree (is_public) WHERE (is_public = true);

CREATE INDEX idx_plans_parent ON public.plans USING btree (parent_plan_id);

CREATE INDEX idx_plans_user_id ON public.plans USING btree (user_id);

CREATE INDEX idx_sets_exercise_id ON public.sets USING btree (exercise_id);

CREATE INDEX idx_sets_set_type ON public.sets USING btree (set_type);

CREATE INDEX idx_sets_workout_session_id ON public.sets USING btree (workout_session_id);

CREATE INDEX idx_workout_sessions_plan_id ON public.workout_sessions USING btree (plan_id);

CREATE INDEX idx_workout_sessions_started_at ON public.workout_sessions USING btree (started_at DESC);

CREATE INDEX idx_workout_sessions_user_id ON public.workout_sessions USING btree (user_id);

CREATE UNIQUE INDEX memories_pkey ON public.memories USING btree (id);

CREATE UNIQUE INDEX movement_patterns_name_key ON public.movement_patterns USING btree (name);

CREATE UNIQUE INDEX movement_patterns_pkey ON public.movement_patterns USING btree (id);

CREATE UNIQUE INDEX muscle_groups_name_key ON public.muscle_groups USING btree (name);

CREATE UNIQUE INDEX muscle_groups_pkey ON public.muscle_groups USING btree (id);

CREATE UNIQUE INDEX plan_exercises_pkey ON public.plan_exercises USING btree (id);

CREATE UNIQUE INDEX plan_exercises_plan_id_day_of_week_order_in_day_key ON public.plan_exercises USING btree (plan_id, day_of_week, order_in_day);

CREATE UNIQUE INDEX plans_pkey ON public.plans USING btree (id);

CREATE UNIQUE INDEX plans_user_id_name_version_number_key ON public.plans USING btree (user_id, name, version_number);

CREATE UNIQUE INDEX profiles_pkey ON public.profiles USING btree (id);

CREATE UNIQUE INDEX profiles_username_key ON public.profiles USING btree (username);

CREATE UNIQUE INDEX sets_pkey ON public.sets USING btree (id);

CREATE UNIQUE INDEX training_styles_name_key ON public.training_styles USING btree (name);

CREATE UNIQUE INDEX training_styles_pkey ON public.training_styles USING btree (id);

CREATE UNIQUE INDEX workout_sessions_pkey ON public.workout_sessions USING btree (id);

alter table "public"."conversations" add constraint "conversations_pkey" PRIMARY KEY using index "conversations_pkey";

alter table "public"."equipment_types" add constraint "equipment_types_pkey" PRIMARY KEY using index "equipment_types_pkey";

alter table "public"."exercise_movement_patterns" add constraint "exercise_movement_patterns_pkey" PRIMARY KEY using index "exercise_movement_patterns_pkey";

alter table "public"."exercise_muscles" add constraint "exercise_muscles_pkey" PRIMARY KEY using index "exercise_muscles_pkey";

alter table "public"."exercise_relationships" add constraint "exercise_relationships_pkey" PRIMARY KEY using index "exercise_relationships_pkey";

alter table "public"."exercise_training_styles" add constraint "exercise_training_styles_pkey" PRIMARY KEY using index "exercise_training_styles_pkey";

alter table "public"."exercises" add constraint "exercises_pkey" PRIMARY KEY using index "exercises_pkey";

alter table "public"."memories" add constraint "memories_pkey" PRIMARY KEY using index "memories_pkey";

alter table "public"."movement_patterns" add constraint "movement_patterns_pkey" PRIMARY KEY using index "movement_patterns_pkey";

alter table "public"."muscle_groups" add constraint "muscle_groups_pkey" PRIMARY KEY using index "muscle_groups_pkey";

alter table "public"."plan_exercises" add constraint "plan_exercises_pkey" PRIMARY KEY using index "plan_exercises_pkey";

alter table "public"."plans" add constraint "plans_pkey" PRIMARY KEY using index "plans_pkey";

alter table "public"."profiles" add constraint "profiles_pkey" PRIMARY KEY using index "profiles_pkey";

alter table "public"."sets" add constraint "sets_pkey" PRIMARY KEY using index "sets_pkey";

alter table "public"."training_styles" add constraint "training_styles_pkey" PRIMARY KEY using index "training_styles_pkey";

alter table "public"."workout_sessions" add constraint "workout_sessions_pkey" PRIMARY KEY using index "workout_sessions_pkey";

alter table "public"."conversations" add constraint "conversations_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE not valid;

alter table "public"."conversations" validate constraint "conversations_user_id_fkey";

alter table "public"."equipment_types" add constraint "equipment_types_category_check" CHECK ((category = ANY (ARRAY['free_weight'::text, 'machine'::text, 'bodyweight'::text, 'cable'::text, 'other'::text]))) not valid;

alter table "public"."equipment_types" validate constraint "equipment_types_category_check";

alter table "public"."equipment_types" add constraint "equipment_types_name_key" UNIQUE using index "equipment_types_name_key";

alter table "public"."exercise_movement_patterns" add constraint "exercise_movement_patterns_exercise_id_fkey" FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_movement_patterns" validate constraint "exercise_movement_patterns_exercise_id_fkey";

alter table "public"."exercise_movement_patterns" add constraint "exercise_movement_patterns_exercise_id_movement_pattern_id_key" UNIQUE using index "exercise_movement_patterns_exercise_id_movement_pattern_id_key";

alter table "public"."exercise_movement_patterns" add constraint "exercise_movement_patterns_movement_pattern_id_fkey" FOREIGN KEY (movement_pattern_id) REFERENCES movement_patterns(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_movement_patterns" validate constraint "exercise_movement_patterns_movement_pattern_id_fkey";

alter table "public"."exercise_muscles" add constraint "exercise_muscles_activation_level_check" CHECK (((activation_level >= 1) AND (activation_level <= 5))) not valid;

alter table "public"."exercise_muscles" validate constraint "exercise_muscles_activation_level_check";

alter table "public"."exercise_muscles" add constraint "exercise_muscles_exercise_id_fkey" FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_muscles" validate constraint "exercise_muscles_exercise_id_fkey";

alter table "public"."exercise_muscles" add constraint "exercise_muscles_exercise_id_muscle_group_id_key" UNIQUE using index "exercise_muscles_exercise_id_muscle_group_id_key";

alter table "public"."exercise_muscles" add constraint "exercise_muscles_muscle_group_id_fkey" FOREIGN KEY (muscle_group_id) REFERENCES muscle_groups(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_muscles" validate constraint "exercise_muscles_muscle_group_id_fkey";

alter table "public"."exercise_muscles" add constraint "exercise_muscles_muscle_role_check" CHECK ((muscle_role = ANY (ARRAY['primary'::text, 'secondary'::text, 'stabilizer'::text]))) not valid;

alter table "public"."exercise_muscles" validate constraint "exercise_muscles_muscle_role_check";

alter table "public"."exercise_relationships" add constraint "exercise_relationships_check" CHECK ((parent_exercise_id <> related_exercise_id)) not valid;

alter table "public"."exercise_relationships" validate constraint "exercise_relationships_check";

alter table "public"."exercise_relationships" add constraint "exercise_relationships_parent_exercise_id_fkey" FOREIGN KEY (parent_exercise_id) REFERENCES exercises(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_relationships" validate constraint "exercise_relationships_parent_exercise_id_fkey";

alter table "public"."exercise_relationships" add constraint "exercise_relationships_parent_exercise_id_related_exercise__key" UNIQUE using index "exercise_relationships_parent_exercise_id_related_exercise__key";

alter table "public"."exercise_relationships" add constraint "exercise_relationships_related_exercise_id_fkey" FOREIGN KEY (related_exercise_id) REFERENCES exercises(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_relationships" validate constraint "exercise_relationships_related_exercise_id_fkey";

alter table "public"."exercise_relationships" add constraint "exercise_relationships_relationship_type_check" CHECK ((relationship_type = ANY (ARRAY['variation'::text, 'progression'::text, 'regression'::text, 'alternative'::text, 'antagonist'::text, 'superset'::text]))) not valid;

alter table "public"."exercise_relationships" validate constraint "exercise_relationships_relationship_type_check";

alter table "public"."exercise_training_styles" add constraint "exercise_training_styles_check" CHECK (((optimal_rep_max > 0) AND (optimal_rep_max >= optimal_rep_min))) not valid;

alter table "public"."exercise_training_styles" validate constraint "exercise_training_styles_check";

alter table "public"."exercise_training_styles" add constraint "exercise_training_styles_exercise_id_fkey" FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_training_styles" validate constraint "exercise_training_styles_exercise_id_fkey";

alter table "public"."exercise_training_styles" add constraint "exercise_training_styles_exercise_id_training_style_id_key" UNIQUE using index "exercise_training_styles_exercise_id_training_style_id_key";

alter table "public"."exercise_training_styles" add constraint "exercise_training_styles_optimal_rep_min_check" CHECK ((optimal_rep_min > 0)) not valid;

alter table "public"."exercise_training_styles" validate constraint "exercise_training_styles_optimal_rep_min_check";

alter table "public"."exercise_training_styles" add constraint "exercise_training_styles_suitability_score_check" CHECK (((suitability_score >= 1) AND (suitability_score <= 5))) not valid;

alter table "public"."exercise_training_styles" validate constraint "exercise_training_styles_suitability_score_check";

alter table "public"."exercise_training_styles" add constraint "exercise_training_styles_training_style_id_fkey" FOREIGN KEY (training_style_id) REFERENCES training_styles(id) ON DELETE CASCADE not valid;

alter table "public"."exercise_training_styles" validate constraint "exercise_training_styles_training_style_id_fkey";

alter table "public"."exercises" add constraint "exercises_body_region_check" CHECK ((body_region = ANY (ARRAY['upper'::text, 'lower'::text, 'full_body'::text, 'core'::text]))) not valid;

alter table "public"."exercises" validate constraint "exercises_body_region_check";

alter table "public"."exercises" add constraint "exercises_difficulty_level_check" CHECK ((difficulty_level = ANY (ARRAY['beginner'::text, 'intermediate'::text, 'advanced'::text, 'expert'::text]))) not valid;

alter table "public"."exercises" validate constraint "exercises_difficulty_level_check";

alter table "public"."exercises" add constraint "exercises_exercise_category_check" CHECK ((exercise_category = ANY (ARRAY['strength'::text, 'cardio'::text, 'mobility'::text, 'plyometric'::text, 'sport_specific'::text, 'corrective'::text, 'balance'::text, 'hypertrophy'::text]))) not valid;

alter table "public"."exercises" validate constraint "exercises_exercise_category_check";

alter table "public"."exercises" add constraint "exercises_force_vector_check" CHECK ((force_vector = ANY (ARRAY['vertical'::text, 'horizontal'::text, 'lateral'::text, 'rotational'::text, 'multi_planar'::text]))) not valid;

alter table "public"."exercises" validate constraint "exercises_force_vector_check";

alter table "public"."exercises" add constraint "exercises_laterality_check" CHECK ((laterality = ANY (ARRAY['bilateral'::text, 'unilateral_left'::text, 'unilateral_right'::text, 'unilateral_alternating'::text]))) not valid;

alter table "public"."exercises" validate constraint "exercises_laterality_check";

alter table "public"."exercises" add constraint "exercises_load_type_check" CHECK ((load_type = ANY (ARRAY['external'::text, 'bodyweight'::text, 'assisted'::text, 'weighted_bodyweight'::text]))) not valid;

alter table "public"."exercises" validate constraint "exercises_load_type_check";

alter table "public"."exercises" add constraint "exercises_mechanic_type_check" CHECK ((mechanic_type = ANY (ARRAY['compound'::text, 'isolation'::text, 'hybrid'::text]))) not valid;

alter table "public"."exercises" validate constraint "exercises_mechanic_type_check";

alter table "public"."exercises" add constraint "exercises_name_primary_equipment_id_key" UNIQUE using index "exercises_name_primary_equipment_id_key";

alter table "public"."exercises" add constraint "exercises_primary_equipment_id_fkey" FOREIGN KEY (primary_equipment_id) REFERENCES equipment_types(id) ON DELETE SET NULL not valid;

alter table "public"."exercises" validate constraint "exercises_primary_equipment_id_fkey";

alter table "public"."exercises" add constraint "exercises_secondary_equipment_id_fkey" FOREIGN KEY (secondary_equipment_id) REFERENCES equipment_types(id) ON DELETE SET NULL not valid;

alter table "public"."exercises" validate constraint "exercises_secondary_equipment_id_fkey";

alter table "public"."memories" add constraint "memories_conversation_id_fkey" FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE not valid;

alter table "public"."memories" validate constraint "memories_conversation_id_fkey";

alter table "public"."memories" add constraint "memories_importance_score_check" CHECK (((importance_score >= (0)::numeric) AND (importance_score <= (1)::numeric))) not valid;

alter table "public"."memories" validate constraint "memories_importance_score_check";

alter table "public"."memories" add constraint "memories_memory_type_check" CHECK ((memory_type = ANY (ARRAY['conversation'::text, 'preference'::text, 'goal'::text, 'achievement'::text, 'feedback'::text]))) not valid;

alter table "public"."memories" validate constraint "memories_memory_type_check";

alter table "public"."memories" add constraint "memories_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE not valid;

alter table "public"."memories" validate constraint "memories_user_id_fkey";

alter table "public"."movement_patterns" add constraint "movement_patterns_name_key" UNIQUE using index "movement_patterns_name_key";

alter table "public"."muscle_groups" add constraint "muscle_groups_muscle_region_check" CHECK ((muscle_region = ANY (ARRAY['upper'::text, 'lower'::text, 'core'::text, 'full_body'::text, 'posterior_chain'::text]))) not valid;

alter table "public"."muscle_groups" validate constraint "muscle_groups_muscle_region_check";

alter table "public"."muscle_groups" add constraint "muscle_groups_name_key" UNIQUE using index "muscle_groups_name_key";

alter table "public"."plan_exercises" add constraint "plan_exercises_day_of_week_check" CHECK (((day_of_week >= 1) AND (day_of_week <= 7))) not valid;

alter table "public"."plan_exercises" validate constraint "plan_exercises_day_of_week_check";

alter table "public"."plan_exercises" add constraint "plan_exercises_exercise_id_fkey" FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE not valid;

alter table "public"."plan_exercises" validate constraint "plan_exercises_exercise_id_fkey";

alter table "public"."plan_exercises" add constraint "plan_exercises_order_in_day_check" CHECK ((order_in_day > 0)) not valid;

alter table "public"."plan_exercises" validate constraint "plan_exercises_order_in_day_check";

alter table "public"."plan_exercises" add constraint "plan_exercises_plan_id_day_of_week_order_in_day_key" UNIQUE using index "plan_exercises_plan_id_day_of_week_order_in_day_key";

alter table "public"."plan_exercises" add constraint "plan_exercises_plan_id_fkey" FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE not valid;

alter table "public"."plan_exercises" validate constraint "plan_exercises_plan_id_fkey";

alter table "public"."plan_exercises" add constraint "plan_exercises_rest_seconds_check" CHECK ((rest_seconds >= 0)) not valid;

alter table "public"."plan_exercises" validate constraint "plan_exercises_rest_seconds_check";

alter table "public"."plan_exercises" add constraint "plan_exercises_sets_check" CHECK ((sets > 0)) not valid;

alter table "public"."plan_exercises" validate constraint "plan_exercises_sets_check";

alter table "public"."plans" add constraint "plans_days_per_week_check" CHECK (((days_per_week >= 1) AND (days_per_week <= 7))) not valid;

alter table "public"."plans" validate constraint "plans_days_per_week_check";

alter table "public"."plans" add constraint "plans_difficulty_level_check" CHECK ((difficulty_level = ANY (ARRAY['beginner'::text, 'intermediate'::text, 'advanced'::text]))) not valid;

alter table "public"."plans" validate constraint "plans_difficulty_level_check";

alter table "public"."plans" add constraint "plans_duration_weeks_check" CHECK ((duration_weeks > 0)) not valid;

alter table "public"."plans" validate constraint "plans_duration_weeks_check";

alter table "public"."plans" add constraint "plans_parent_plan_id_fkey" FOREIGN KEY (parent_plan_id) REFERENCES plans(id) not valid;

alter table "public"."plans" validate constraint "plans_parent_plan_id_fkey";

alter table "public"."plans" add constraint "plans_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE not valid;

alter table "public"."plans" validate constraint "plans_user_id_fkey";

alter table "public"."plans" add constraint "plans_user_id_name_version_number_key" UNIQUE using index "plans_user_id_name_version_number_key";

alter table "public"."profiles" add constraint "profiles_affinity_score_check" CHECK ((affinity_score >= 0)) not valid;

alter table "public"."profiles" validate constraint "profiles_affinity_score_check";

alter table "public"."profiles" add constraint "profiles_age_check" CHECK (((age >= 13) AND (age <= 120))) not valid;

alter table "public"."profiles" validate constraint "profiles_age_check";

alter table "public"."profiles" add constraint "profiles_fitness_level_check" CHECK ((fitness_level = ANY (ARRAY['beginner'::text, 'intermediate'::text, 'advanced'::text]))) not valid;

alter table "public"."profiles" validate constraint "profiles_fitness_level_check";

alter table "public"."profiles" add constraint "profiles_id_fkey" FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."profiles" validate constraint "profiles_id_fkey";

alter table "public"."profiles" add constraint "profiles_username_key" UNIQUE using index "profiles_username_key";

alter table "public"."sets" add constraint "sets_assistance_type_check" CHECK ((assistance_type = ANY (ARRAY['none'::text, 'spotter'::text, 'machine_assist'::text, 'band_assist'::text]))) not valid;

alter table "public"."sets" validate constraint "sets_assistance_type_check";

alter table "public"."sets" add constraint "sets_exercise_id_fkey" FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE not valid;

alter table "public"."sets" validate constraint "sets_exercise_id_fkey";

alter table "public"."sets" add constraint "sets_failure_type_check" CHECK ((failure_type = ANY (ARRAY['muscular'::text, 'form'::text, 'cardiovascular'::text, 'motivation'::text]))) not valid;

alter table "public"."sets" validate constraint "sets_failure_type_check";

alter table "public"."sets" add constraint "sets_form_quality_check" CHECK (((form_quality >= 1) AND (form_quality <= 5))) not valid;

alter table "public"."sets" validate constraint "sets_form_quality_check";

alter table "public"."sets" add constraint "sets_intensity_percentage_check" CHECK (((intensity_percentage >= (0)::numeric) AND (intensity_percentage <= (200)::numeric))) not valid;

alter table "public"."sets" validate constraint "sets_intensity_percentage_check";

alter table "public"."sets" add constraint "sets_range_of_motion_quality_check" CHECK ((range_of_motion_quality = ANY (ARRAY['full'::text, 'partial'::text, 'limited'::text, 'assisted'::text]))) not valid;

alter table "public"."sets" validate constraint "sets_range_of_motion_quality_check";

alter table "public"."sets" add constraint "sets_reps_check" CHECK ((reps > 0)) not valid;

alter table "public"."sets" validate constraint "sets_reps_check";

alter table "public"."sets" add constraint "sets_reps_in_reserve_check" CHECK ((reps_in_reserve >= 0)) not valid;

alter table "public"."sets" validate constraint "sets_reps_in_reserve_check";

alter table "public"."sets" add constraint "sets_rest_taken_seconds_check" CHECK ((rest_taken_seconds >= 0)) not valid;

alter table "public"."sets" validate constraint "sets_rest_taken_seconds_check";

alter table "public"."sets" add constraint "sets_rpe_check" CHECK (((rpe >= 1) AND (rpe <= 10))) not valid;

alter table "public"."sets" validate constraint "sets_rpe_check";

alter table "public"."sets" add constraint "sets_set_number_check" CHECK ((set_number > 0)) not valid;

alter table "public"."sets" validate constraint "sets_set_number_check";

alter table "public"."sets" add constraint "sets_set_type_check" CHECK ((set_type = ANY (ARRAY['working'::text, 'warmup'::text, 'backoff'::text, 'drop'::text, 'cluster'::text, 'rest_pause'::text, 'amrap'::text]))) not valid;

alter table "public"."sets" validate constraint "sets_set_type_check";

alter table "public"."sets" add constraint "sets_weight_check" CHECK ((weight >= (0)::numeric)) not valid;

alter table "public"."sets" validate constraint "sets_weight_check";

alter table "public"."sets" add constraint "sets_workout_session_id_fkey" FOREIGN KEY (workout_session_id) REFERENCES workout_sessions(id) ON DELETE CASCADE not valid;

alter table "public"."sets" validate constraint "sets_workout_session_id_fkey";

alter table "public"."training_styles" add constraint "training_styles_name_key" UNIQUE using index "training_styles_name_key";

alter table "public"."workout_sessions" add constraint "workout_sessions_mood_check" CHECK ((mood = ANY (ARRAY['great'::text, 'good'::text, 'neutral'::text, 'tired'::text, 'exhausted'::text]))) not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_mood_check";

alter table "public"."workout_sessions" add constraint "workout_sessions_overall_rpe_check" CHECK (((overall_rpe >= 1) AND (overall_rpe <= 10))) not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_overall_rpe_check";

alter table "public"."workout_sessions" add constraint "workout_sessions_plan_id_fkey" FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_plan_id_fkey";

alter table "public"."workout_sessions" add constraint "workout_sessions_post_workout_energy_check" CHECK (((post_workout_energy >= 1) AND (post_workout_energy <= 10))) not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_post_workout_energy_check";

alter table "public"."workout_sessions" add constraint "workout_sessions_pre_workout_energy_check" CHECK (((pre_workout_energy >= 1) AND (pre_workout_energy <= 10))) not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_pre_workout_energy_check";

alter table "public"."workout_sessions" add constraint "workout_sessions_training_phase_check" CHECK ((training_phase = ANY (ARRAY['accumulation'::text, 'intensification'::text, 'realization'::text, 'deload'::text, 'testing'::text]))) not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_training_phase_check";

alter table "public"."workout_sessions" add constraint "workout_sessions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_user_id_fkey";

alter table "public"."workout_sessions" add constraint "workout_sessions_workout_type_check" CHECK ((workout_type = ANY (ARRAY['strength'::text, 'hypertrophy'::text, 'power'::text, 'endurance'::text, 'mixed'::text, 'technique'::text, 'deload'::text]))) not valid;

alter table "public"."workout_sessions" validate constraint "workout_sessions_workout_type_check";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
BEGIN
    INSERT INTO public.profiles (id, username, full_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.increment_affinity_score(p_user_id uuid, p_points integer DEFAULT 1)
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
    new_score INTEGER;
BEGIN
    UPDATE public.profiles 
    SET affinity_score = affinity_score + p_points
    WHERE id = p_user_id
    RETURNING affinity_score INTO new_score;
    
    RETURN new_score;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.search_memories(p_user_id uuid, p_query_embedding halfvec, p_limit integer DEFAULT 10, p_threshold double precision DEFAULT 0.7)
 RETURNS TABLE(id uuid, content text, memory_type text, importance_score numeric, similarity double precision, created_at timestamp with time zone, metadata jsonb)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.content,
        m.memory_type,
        m.importance_score,
        1 - (m.embedding OPERATOR(extensions.<=>) p_query_embedding) AS similarity,
        m.created_at,
        m.metadata
    FROM public.memories m
    WHERE m.user_id = p_user_id
        AND m.embedding IS NOT NULL
        AND 1 - (m.embedding OPERATOR(extensions.<=>) p_query_embedding) > p_threshold
    ORDER BY m.embedding OPERATOR(extensions.<=>) p_query_embedding
    LIMIT p_limit;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
;

grant delete on table "public"."conversations" to "anon";

grant insert on table "public"."conversations" to "anon";

grant references on table "public"."conversations" to "anon";

grant select on table "public"."conversations" to "anon";

grant trigger on table "public"."conversations" to "anon";

grant truncate on table "public"."conversations" to "anon";

grant update on table "public"."conversations" to "anon";

grant delete on table "public"."conversations" to "authenticated";

grant insert on table "public"."conversations" to "authenticated";

grant references on table "public"."conversations" to "authenticated";

grant select on table "public"."conversations" to "authenticated";

grant trigger on table "public"."conversations" to "authenticated";

grant truncate on table "public"."conversations" to "authenticated";

grant update on table "public"."conversations" to "authenticated";

grant delete on table "public"."conversations" to "service_role";

grant insert on table "public"."conversations" to "service_role";

grant references on table "public"."conversations" to "service_role";

grant select on table "public"."conversations" to "service_role";

grant trigger on table "public"."conversations" to "service_role";

grant truncate on table "public"."conversations" to "service_role";

grant update on table "public"."conversations" to "service_role";

grant delete on table "public"."equipment_types" to "anon";

grant insert on table "public"."equipment_types" to "anon";

grant references on table "public"."equipment_types" to "anon";

grant select on table "public"."equipment_types" to "anon";

grant trigger on table "public"."equipment_types" to "anon";

grant truncate on table "public"."equipment_types" to "anon";

grant update on table "public"."equipment_types" to "anon";

grant delete on table "public"."equipment_types" to "authenticated";

grant insert on table "public"."equipment_types" to "authenticated";

grant references on table "public"."equipment_types" to "authenticated";

grant select on table "public"."equipment_types" to "authenticated";

grant trigger on table "public"."equipment_types" to "authenticated";

grant truncate on table "public"."equipment_types" to "authenticated";

grant update on table "public"."equipment_types" to "authenticated";

grant delete on table "public"."equipment_types" to "service_role";

grant insert on table "public"."equipment_types" to "service_role";

grant references on table "public"."equipment_types" to "service_role";

grant select on table "public"."equipment_types" to "service_role";

grant trigger on table "public"."equipment_types" to "service_role";

grant truncate on table "public"."equipment_types" to "service_role";

grant update on table "public"."equipment_types" to "service_role";

grant delete on table "public"."exercise_movement_patterns" to "anon";

grant insert on table "public"."exercise_movement_patterns" to "anon";

grant references on table "public"."exercise_movement_patterns" to "anon";

grant select on table "public"."exercise_movement_patterns" to "anon";

grant trigger on table "public"."exercise_movement_patterns" to "anon";

grant truncate on table "public"."exercise_movement_patterns" to "anon";

grant update on table "public"."exercise_movement_patterns" to "anon";

grant delete on table "public"."exercise_movement_patterns" to "authenticated";

grant insert on table "public"."exercise_movement_patterns" to "authenticated";

grant references on table "public"."exercise_movement_patterns" to "authenticated";

grant select on table "public"."exercise_movement_patterns" to "authenticated";

grant trigger on table "public"."exercise_movement_patterns" to "authenticated";

grant truncate on table "public"."exercise_movement_patterns" to "authenticated";

grant update on table "public"."exercise_movement_patterns" to "authenticated";

grant delete on table "public"."exercise_movement_patterns" to "service_role";

grant insert on table "public"."exercise_movement_patterns" to "service_role";

grant references on table "public"."exercise_movement_patterns" to "service_role";

grant select on table "public"."exercise_movement_patterns" to "service_role";

grant trigger on table "public"."exercise_movement_patterns" to "service_role";

grant truncate on table "public"."exercise_movement_patterns" to "service_role";

grant update on table "public"."exercise_movement_patterns" to "service_role";

grant delete on table "public"."exercise_muscles" to "anon";

grant insert on table "public"."exercise_muscles" to "anon";

grant references on table "public"."exercise_muscles" to "anon";

grant select on table "public"."exercise_muscles" to "anon";

grant trigger on table "public"."exercise_muscles" to "anon";

grant truncate on table "public"."exercise_muscles" to "anon";

grant update on table "public"."exercise_muscles" to "anon";

grant delete on table "public"."exercise_muscles" to "authenticated";

grant insert on table "public"."exercise_muscles" to "authenticated";

grant references on table "public"."exercise_muscles" to "authenticated";

grant select on table "public"."exercise_muscles" to "authenticated";

grant trigger on table "public"."exercise_muscles" to "authenticated";

grant truncate on table "public"."exercise_muscles" to "authenticated";

grant update on table "public"."exercise_muscles" to "authenticated";

grant delete on table "public"."exercise_muscles" to "service_role";

grant insert on table "public"."exercise_muscles" to "service_role";

grant references on table "public"."exercise_muscles" to "service_role";

grant select on table "public"."exercise_muscles" to "service_role";

grant trigger on table "public"."exercise_muscles" to "service_role";

grant truncate on table "public"."exercise_muscles" to "service_role";

grant update on table "public"."exercise_muscles" to "service_role";

grant delete on table "public"."exercise_relationships" to "anon";

grant insert on table "public"."exercise_relationships" to "anon";

grant references on table "public"."exercise_relationships" to "anon";

grant select on table "public"."exercise_relationships" to "anon";

grant trigger on table "public"."exercise_relationships" to "anon";

grant truncate on table "public"."exercise_relationships" to "anon";

grant update on table "public"."exercise_relationships" to "anon";

grant delete on table "public"."exercise_relationships" to "authenticated";

grant insert on table "public"."exercise_relationships" to "authenticated";

grant references on table "public"."exercise_relationships" to "authenticated";

grant select on table "public"."exercise_relationships" to "authenticated";

grant trigger on table "public"."exercise_relationships" to "authenticated";

grant truncate on table "public"."exercise_relationships" to "authenticated";

grant update on table "public"."exercise_relationships" to "authenticated";

grant delete on table "public"."exercise_relationships" to "service_role";

grant insert on table "public"."exercise_relationships" to "service_role";

grant references on table "public"."exercise_relationships" to "service_role";

grant select on table "public"."exercise_relationships" to "service_role";

grant trigger on table "public"."exercise_relationships" to "service_role";

grant truncate on table "public"."exercise_relationships" to "service_role";

grant update on table "public"."exercise_relationships" to "service_role";

grant delete on table "public"."exercise_training_styles" to "anon";

grant insert on table "public"."exercise_training_styles" to "anon";

grant references on table "public"."exercise_training_styles" to "anon";

grant select on table "public"."exercise_training_styles" to "anon";

grant trigger on table "public"."exercise_training_styles" to "anon";

grant truncate on table "public"."exercise_training_styles" to "anon";

grant update on table "public"."exercise_training_styles" to "anon";

grant delete on table "public"."exercise_training_styles" to "authenticated";

grant insert on table "public"."exercise_training_styles" to "authenticated";

grant references on table "public"."exercise_training_styles" to "authenticated";

grant select on table "public"."exercise_training_styles" to "authenticated";

grant trigger on table "public"."exercise_training_styles" to "authenticated";

grant truncate on table "public"."exercise_training_styles" to "authenticated";

grant update on table "public"."exercise_training_styles" to "authenticated";

grant delete on table "public"."exercise_training_styles" to "service_role";

grant insert on table "public"."exercise_training_styles" to "service_role";

grant references on table "public"."exercise_training_styles" to "service_role";

grant select on table "public"."exercise_training_styles" to "service_role";

grant trigger on table "public"."exercise_training_styles" to "service_role";

grant truncate on table "public"."exercise_training_styles" to "service_role";

grant update on table "public"."exercise_training_styles" to "service_role";

grant delete on table "public"."exercises" to "anon";

grant insert on table "public"."exercises" to "anon";

grant references on table "public"."exercises" to "anon";

grant select on table "public"."exercises" to "anon";

grant trigger on table "public"."exercises" to "anon";

grant truncate on table "public"."exercises" to "anon";

grant update on table "public"."exercises" to "anon";

grant delete on table "public"."exercises" to "authenticated";

grant insert on table "public"."exercises" to "authenticated";

grant references on table "public"."exercises" to "authenticated";

grant select on table "public"."exercises" to "authenticated";

grant trigger on table "public"."exercises" to "authenticated";

grant truncate on table "public"."exercises" to "authenticated";

grant update on table "public"."exercises" to "authenticated";

grant delete on table "public"."exercises" to "service_role";

grant insert on table "public"."exercises" to "service_role";

grant references on table "public"."exercises" to "service_role";

grant select on table "public"."exercises" to "service_role";

grant trigger on table "public"."exercises" to "service_role";

grant truncate on table "public"."exercises" to "service_role";

grant update on table "public"."exercises" to "service_role";

grant delete on table "public"."memories" to "anon";

grant insert on table "public"."memories" to "anon";

grant references on table "public"."memories" to "anon";

grant select on table "public"."memories" to "anon";

grant trigger on table "public"."memories" to "anon";

grant truncate on table "public"."memories" to "anon";

grant update on table "public"."memories" to "anon";

grant delete on table "public"."memories" to "authenticated";

grant insert on table "public"."memories" to "authenticated";

grant references on table "public"."memories" to "authenticated";

grant select on table "public"."memories" to "authenticated";

grant trigger on table "public"."memories" to "authenticated";

grant truncate on table "public"."memories" to "authenticated";

grant update on table "public"."memories" to "authenticated";

grant delete on table "public"."memories" to "service_role";

grant insert on table "public"."memories" to "service_role";

grant references on table "public"."memories" to "service_role";

grant select on table "public"."memories" to "service_role";

grant trigger on table "public"."memories" to "service_role";

grant truncate on table "public"."memories" to "service_role";

grant update on table "public"."memories" to "service_role";

grant delete on table "public"."movement_patterns" to "anon";

grant insert on table "public"."movement_patterns" to "anon";

grant references on table "public"."movement_patterns" to "anon";

grant select on table "public"."movement_patterns" to "anon";

grant trigger on table "public"."movement_patterns" to "anon";

grant truncate on table "public"."movement_patterns" to "anon";

grant update on table "public"."movement_patterns" to "anon";

grant delete on table "public"."movement_patterns" to "authenticated";

grant insert on table "public"."movement_patterns" to "authenticated";

grant references on table "public"."movement_patterns" to "authenticated";

grant select on table "public"."movement_patterns" to "authenticated";

grant trigger on table "public"."movement_patterns" to "authenticated";

grant truncate on table "public"."movement_patterns" to "authenticated";

grant update on table "public"."movement_patterns" to "authenticated";

grant delete on table "public"."movement_patterns" to "service_role";

grant insert on table "public"."movement_patterns" to "service_role";

grant references on table "public"."movement_patterns" to "service_role";

grant select on table "public"."movement_patterns" to "service_role";

grant trigger on table "public"."movement_patterns" to "service_role";

grant truncate on table "public"."movement_patterns" to "service_role";

grant update on table "public"."movement_patterns" to "service_role";

grant delete on table "public"."muscle_groups" to "anon";

grant insert on table "public"."muscle_groups" to "anon";

grant references on table "public"."muscle_groups" to "anon";

grant select on table "public"."muscle_groups" to "anon";

grant trigger on table "public"."muscle_groups" to "anon";

grant truncate on table "public"."muscle_groups" to "anon";

grant update on table "public"."muscle_groups" to "anon";

grant delete on table "public"."muscle_groups" to "authenticated";

grant insert on table "public"."muscle_groups" to "authenticated";

grant references on table "public"."muscle_groups" to "authenticated";

grant select on table "public"."muscle_groups" to "authenticated";

grant trigger on table "public"."muscle_groups" to "authenticated";

grant truncate on table "public"."muscle_groups" to "authenticated";

grant update on table "public"."muscle_groups" to "authenticated";

grant delete on table "public"."muscle_groups" to "service_role";

grant insert on table "public"."muscle_groups" to "service_role";

grant references on table "public"."muscle_groups" to "service_role";

grant select on table "public"."muscle_groups" to "service_role";

grant trigger on table "public"."muscle_groups" to "service_role";

grant truncate on table "public"."muscle_groups" to "service_role";

grant update on table "public"."muscle_groups" to "service_role";

grant delete on table "public"."plan_exercises" to "anon";

grant insert on table "public"."plan_exercises" to "anon";

grant references on table "public"."plan_exercises" to "anon";

grant select on table "public"."plan_exercises" to "anon";

grant trigger on table "public"."plan_exercises" to "anon";

grant truncate on table "public"."plan_exercises" to "anon";

grant update on table "public"."plan_exercises" to "anon";

grant delete on table "public"."plan_exercises" to "authenticated";

grant insert on table "public"."plan_exercises" to "authenticated";

grant references on table "public"."plan_exercises" to "authenticated";

grant select on table "public"."plan_exercises" to "authenticated";

grant trigger on table "public"."plan_exercises" to "authenticated";

grant truncate on table "public"."plan_exercises" to "authenticated";

grant update on table "public"."plan_exercises" to "authenticated";

grant delete on table "public"."plan_exercises" to "service_role";

grant insert on table "public"."plan_exercises" to "service_role";

grant references on table "public"."plan_exercises" to "service_role";

grant select on table "public"."plan_exercises" to "service_role";

grant trigger on table "public"."plan_exercises" to "service_role";

grant truncate on table "public"."plan_exercises" to "service_role";

grant update on table "public"."plan_exercises" to "service_role";

grant delete on table "public"."plans" to "anon";

grant insert on table "public"."plans" to "anon";

grant references on table "public"."plans" to "anon";

grant select on table "public"."plans" to "anon";

grant trigger on table "public"."plans" to "anon";

grant truncate on table "public"."plans" to "anon";

grant update on table "public"."plans" to "anon";

grant delete on table "public"."plans" to "authenticated";

grant insert on table "public"."plans" to "authenticated";

grant references on table "public"."plans" to "authenticated";

grant select on table "public"."plans" to "authenticated";

grant trigger on table "public"."plans" to "authenticated";

grant truncate on table "public"."plans" to "authenticated";

grant update on table "public"."plans" to "authenticated";

grant delete on table "public"."plans" to "service_role";

grant insert on table "public"."plans" to "service_role";

grant references on table "public"."plans" to "service_role";

grant select on table "public"."plans" to "service_role";

grant trigger on table "public"."plans" to "service_role";

grant truncate on table "public"."plans" to "service_role";

grant update on table "public"."plans" to "service_role";

grant delete on table "public"."profiles" to "anon";

grant insert on table "public"."profiles" to "anon";

grant references on table "public"."profiles" to "anon";

grant select on table "public"."profiles" to "anon";

grant trigger on table "public"."profiles" to "anon";

grant truncate on table "public"."profiles" to "anon";

grant update on table "public"."profiles" to "anon";

grant delete on table "public"."profiles" to "authenticated";

grant insert on table "public"."profiles" to "authenticated";

grant references on table "public"."profiles" to "authenticated";

grant select on table "public"."profiles" to "authenticated";

grant trigger on table "public"."profiles" to "authenticated";

grant truncate on table "public"."profiles" to "authenticated";

grant update on table "public"."profiles" to "authenticated";

grant delete on table "public"."profiles" to "service_role";

grant insert on table "public"."profiles" to "service_role";

grant references on table "public"."profiles" to "service_role";

grant select on table "public"."profiles" to "service_role";

grant trigger on table "public"."profiles" to "service_role";

grant truncate on table "public"."profiles" to "service_role";

grant update on table "public"."profiles" to "service_role";

grant delete on table "public"."sets" to "anon";

grant insert on table "public"."sets" to "anon";

grant references on table "public"."sets" to "anon";

grant select on table "public"."sets" to "anon";

grant trigger on table "public"."sets" to "anon";

grant truncate on table "public"."sets" to "anon";

grant update on table "public"."sets" to "anon";

grant delete on table "public"."sets" to "authenticated";

grant insert on table "public"."sets" to "authenticated";

grant references on table "public"."sets" to "authenticated";

grant select on table "public"."sets" to "authenticated";

grant trigger on table "public"."sets" to "authenticated";

grant truncate on table "public"."sets" to "authenticated";

grant update on table "public"."sets" to "authenticated";

grant delete on table "public"."sets" to "service_role";

grant insert on table "public"."sets" to "service_role";

grant references on table "public"."sets" to "service_role";

grant select on table "public"."sets" to "service_role";

grant trigger on table "public"."sets" to "service_role";

grant truncate on table "public"."sets" to "service_role";

grant update on table "public"."sets" to "service_role";

grant delete on table "public"."training_styles" to "anon";

grant insert on table "public"."training_styles" to "anon";

grant references on table "public"."training_styles" to "anon";

grant select on table "public"."training_styles" to "anon";

grant trigger on table "public"."training_styles" to "anon";

grant truncate on table "public"."training_styles" to "anon";

grant update on table "public"."training_styles" to "anon";

grant delete on table "public"."training_styles" to "authenticated";

grant insert on table "public"."training_styles" to "authenticated";

grant references on table "public"."training_styles" to "authenticated";

grant select on table "public"."training_styles" to "authenticated";

grant trigger on table "public"."training_styles" to "authenticated";

grant truncate on table "public"."training_styles" to "authenticated";

grant update on table "public"."training_styles" to "authenticated";

grant delete on table "public"."training_styles" to "service_role";

grant insert on table "public"."training_styles" to "service_role";

grant references on table "public"."training_styles" to "service_role";

grant select on table "public"."training_styles" to "service_role";

grant trigger on table "public"."training_styles" to "service_role";

grant truncate on table "public"."training_styles" to "service_role";

grant update on table "public"."training_styles" to "service_role";

grant delete on table "public"."workout_sessions" to "anon";

grant insert on table "public"."workout_sessions" to "anon";

grant references on table "public"."workout_sessions" to "anon";

grant select on table "public"."workout_sessions" to "anon";

grant trigger on table "public"."workout_sessions" to "anon";

grant truncate on table "public"."workout_sessions" to "anon";

grant update on table "public"."workout_sessions" to "anon";

grant delete on table "public"."workout_sessions" to "authenticated";

grant insert on table "public"."workout_sessions" to "authenticated";

grant references on table "public"."workout_sessions" to "authenticated";

grant select on table "public"."workout_sessions" to "authenticated";

grant trigger on table "public"."workout_sessions" to "authenticated";

grant truncate on table "public"."workout_sessions" to "authenticated";

grant update on table "public"."workout_sessions" to "authenticated";

grant delete on table "public"."workout_sessions" to "service_role";

grant insert on table "public"."workout_sessions" to "service_role";

grant references on table "public"."workout_sessions" to "service_role";

grant select on table "public"."workout_sessions" to "service_role";

grant trigger on table "public"."workout_sessions" to "service_role";

grant truncate on table "public"."workout_sessions" to "service_role";

grant update on table "public"."workout_sessions" to "service_role";

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON public.conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exercises_updated_at BEFORE UPDATE ON public.exercises FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON public.memories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sets_updated_at BEFORE UPDATE ON public.sets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workout_sessions_updated_at BEFORE UPDATE ON public.workout_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();



# Database Architecture Documentation

## Overview

This document provides comprehensive documentation for the Slow Burn AI Fitness Companion database schema. The database is built on PostgreSQL with the pgvector extension for AI semantic memory functionality and Supabase for authentication and real-time features.

## Database Schema Architecture

### Design Principles

1. **Security-First**: All tables implement Row Level Security (RLS) policies
2. **Performance Optimized**: Strategic indexes including HNSW for vector search
3. **Audit Trail**: Created/updated timestamps with automatic triggers
4. **Scalability**: Normalized design with efficient foreign key relationships
5. **Extensibility**: JSONB metadata fields for future expansion
6. **Data Integrity**: Comprehensive check constraints and foreign keys

### Technology Stack

- **Database**: PostgreSQL 15+
- **Vector Extension**: pgvector with halfvec(3072) for embeddings
- **Authentication**: Supabase Auth integration
- **Hosting**: Supabase Platform
- **Connection**: Row Level Security (RLS) enabled on all tables

## Entity Relationship Diagram (Text-Based)

```
AUTH LAYER (Supabase)
             
 auth.users   (Supabase managed)
     ,       
       1:1
      �
USER PROFILES
             
 profiles     �  (user_id foreign keys)
 - id (PK)      
 - username     
 - affinity     
                
                  
REFERENCE TABLES  
                                                                 
movement_         muscle_        equipment_      training_       
patterns          groups         types           styles          
- id (PK)         - id (PK)      - id (PK)       - id (PK)       
- name            - name         - name          - name          
      ,                 ,              ,                 ,       
                                                             
                                                             
EXERCISES SYSTEM                                              
                 4                                           
 exercises                                                   
 - id (PK)           �    <                <                   
 - name                                   
 - primary_equip_id  �    <                
 - force_vector           
 - difficulty             
     ,                    
                           
       1:M                  M:M
      �                     �
                                                                          
exercise_          exercise_          exercise_training_  exercise_       
movement_          muscles            styles              relationships   
patterns           - exercise_id      - exercise_id       - parent_ex_id  
- exercise_id      - muscle_grp_id    - training_st_id    - related_ex_id 
- pattern_id       - muscle_role      - suitability       - relationship  
                                                                          

WORKOUT PLANNING                  
                                
 plans        �                 $
 - id (PK)                      
 - user_id    �                 <      
 - version                            
 - parent_id  �  (self-ref)          
     ,                               
                                      
       1:M                            
      �                                
                                     
 plan_exercises                       
 - plan_id                            
 - exercise_id      �                 
 - day_of_week                         
 - order_in_day                        
                                       
                                         
WORKOUT EXECUTION                        
                                       
 workout_         �                    $
 sessions                              
 - id (PK)                             
 - user_id        �                    
 - plan_id        (optional)
 - started_at    
 - mood, rpe     
     ,           
       1:M
      �
                 
 sets            
 - id (PK)       
 - session_id     
 - exercise_id    �                   
 - weight, reps                       
 - volume_load    (calculated)        
 - rpe, rir                           
                                      
                                        
AI SYSTEM                               
                                      
 conversations    �                   $
 - id (PK)                            
 - user_id        �                   < 
 - started_at                          
 - context                             
     ,                                 
       1:M                              
      �                                  
                                       
 memories         �                   $ 
 - id (PK)                             
 - user_id        �                    
 - conv_id                              
 - content                              
 - embedding      halfvec(3072)         
 - memory_type                          
                                        
                                          
Legend:                                   
    Foreign Key Relationship              
�   Points to Primary Key                
1:1 One-to-One                           
1:M One-to-Many                          
M:M Many-to-Many (via junction table)    
```

## Table Relationships and Foreign Keys

### Core User System

#### profiles
- **Primary Key**: `id` (UUID)
- **Foreign Keys**: 
  - `id` � `auth.users(id)` ON DELETE CASCADE
- **Relationships**:
  - 1:1 with `auth.users` (extends Supabase auth)
  - 1:M with `plans` (user creates multiple workout plans)
  - 1:M with `workout_sessions` (user performs multiple workouts)
  - 1:M with `conversations` (user has multiple AI chat sessions)
  - 1:M with `memories` (user has multiple AI memory entries)

### Reference Data System

#### movement_patterns, muscle_groups, equipment_types, training_styles
- **Primary Key**: `id` (UUID)
- **No Foreign Keys**: Reference tables at top of hierarchy
- **Relationships**: M:M with `exercises` via junction tables

### Exercise System

#### exercises
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `primary_equipment_id` � `equipment_types(id)` ON DELETE SET NULL
  - `secondary_equipment_id` � `equipment_types(id)` ON DELETE SET NULL
- **Cascade Behavior**: Equipment deletion doesn't delete exercises (SET NULL)
- **Relationships**:
  - M:M with `movement_patterns` via `exercise_movement_patterns`
  - M:M with `muscle_groups` via `exercise_muscles`
  - M:M with `training_styles` via `exercise_training_styles`
  - 1:M with `exercise_relationships` (self-referencing for variations)
  - 1:M with `plan_exercises` (exercises used in plans)
  - 1:M with `sets` (exercises performed in workouts)

#### Junction Tables (exercise_*)
- **exercise_movement_patterns**:
  - `exercise_id` � `exercises(id)` ON DELETE CASCADE
  - `movement_pattern_id` � `movement_patterns(id)` ON DELETE CASCADE
- **exercise_muscles**:
  - `exercise_id` � `exercises(id)` ON DELETE CASCADE
  - `muscle_group_id` � `muscle_groups(id)` ON DELETE CASCADE
- **exercise_training_styles**:
  - `exercise_id` � `exercises(id)` ON DELETE CASCADE
  - `training_style_id` � `training_styles(id)` ON DELETE CASCADE
- **exercise_relationships**:
  - `parent_exercise_id` � `exercises(id)` ON DELETE CASCADE
  - `related_exercise_id` � `exercises(id)` ON DELETE CASCADE

**Cascade Behavior**: All junction tables CASCADE delete when parent exercise is deleted

### Workout Planning System

#### plans
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `user_id` � `profiles(id)` ON DELETE CASCADE
  - `parent_plan_id` � `plans(id)` (self-referencing for versioning)
- **Cascade Behavior**: 
  - User deletion cascades to delete all their plans
  - Parent plan deletion leaves orphaned versions (no CASCADE)
- **Relationships**:
  - M:1 with `profiles` (user owns multiple plans)
  - 1:M with `plan_exercises` (plan contains multiple exercises)
  - 1:M with `workout_sessions` (plan can be followed multiple times)

#### plan_exercises
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `plan_id` � `plans(id)` ON DELETE CASCADE
  - `exercise_id` � `exercises(id)` ON DELETE CASCADE
- **Cascade Behavior**: Both plan and exercise deletion remove plan_exercises
- **Unique Constraint**: `(plan_id, day_of_week, order_in_day)` ensures exercise ordering

### Workout Execution System

#### workout_sessions
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `user_id` � `profiles(id)` ON DELETE CASCADE
  - `plan_id` � `plans(id)` ON DELETE SET NULL
- **Cascade Behavior**:
  - User deletion cascades to delete all their sessions
  - Plan deletion preserves sessions but removes plan reference
- **Relationships**:
  - M:1 with `profiles` (user performs multiple workouts)
  - M:1 with `plans` (optional - ad-hoc workouts have NULL plan_id)
  - 1:M with `sets` (session contains multiple sets)

#### sets
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `workout_session_id` � `workout_sessions(id)` ON DELETE CASCADE
  - `exercise_id` � `exercises(id)` ON DELETE CASCADE
- **Cascade Behavior**: Both session and exercise deletion remove sets
- **Calculated Fields**: `volume_load` = `weight * reps` (GENERATED STORED)

### AI System

#### conversations
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `user_id` � `profiles(id)` ON DELETE CASCADE
- **Cascade Behavior**: User deletion cascades to delete all conversations
- **Relationships**:
  - M:1 with `profiles` (user has multiple conversations)
  - 1:M with `memories` (conversation generates multiple memories)

#### memories
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `user_id` � `profiles(id)` ON DELETE CASCADE
  - `conversation_id` � `conversations(id)` ON DELETE CASCADE
- **Cascade Behavior**: Both user and conversation deletion remove memories
- **Special Fields**: `embedding` halfvec(3072) for vector similarity search

## Cascade Behaviors Summary

### DELETE CASCADE (Child deleted when parent deleted)
- `profiles` � All user data (plans, sessions, conversations, memories)
- `exercises` � Junction table entries (movement_patterns, muscles, etc.)
- `plans` � `plan_exercises` entries
- `workout_sessions` � `sets` entries
- `conversations` � `memories` entries

### SET NULL (Reference removed but child preserved)
- `equipment_types` � `exercises` (primary/secondary equipment)
- `plans` � `workout_sessions` (preserves session when plan deleted)

### No Action (Reference tables preserved)
- All reference tables (`movement_patterns`, `muscle_groups`, etc.)

## Indexes and Performance

### Primary Indexes (Automatically Created)
- Primary keys on all tables (UUID with btree index)
- Unique constraints create automatic indexes

### Foreign Key Indexes (Performance Critical)
```sql
-- User data access patterns
CREATE INDEX idx_plans_user_id ON public.plans(user_id);
CREATE INDEX idx_workout_sessions_user_id ON public.workout_sessions(user_id);
CREATE INDEX idx_memories_user_id ON public.memories(user_id);
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);

-- Workout data joins
CREATE INDEX idx_sets_workout_session_id ON public.sets(workout_session_id);
CREATE INDEX idx_sets_exercise_id ON public.sets(exercise_id);
CREATE INDEX idx_plan_exercises_plan_id ON public.plan_exercises(plan_id);
CREATE INDEX idx_plan_exercises_exercise_id ON public.plan_exercises(exercise_id);

-- AI system
CREATE INDEX idx_memories_conversation_id ON public.memories(conversation_id);
```

### Vector Search Index (AI-Specific)
```sql
-- HNSW index for fast vector similarity search
CREATE INDEX idx_memories_embedding 
ON public.memories 
USING hnsw (embedding extensions.halfvec_l2_ops);
```

## Database Functions

### User Management Functions

#### `increment_affinity_score(p_user_id UUID, p_points INTEGER)`
- **Purpose**: Atomically increment user's AI companion affinity score
- **Usage**: Called after workout completion or positive AI interactions
- **Returns**: New affinity score value
- **Security**: SECURITY DEFINER with empty search_path

#### `handle_new_user()`
- **Purpose**: Automatically create profile when new auth.users record created
- **Trigger**: AFTER INSERT on auth.users
- **Behavior**: Creates profile with username from email or metadata

### AI Functions

#### `search_memories(p_user_id UUID, p_query_embedding halfvec(3072), p_limit INTEGER, p_threshold FLOAT)`
- **Purpose**: Semantic search through user's AI memories using vector similarity
- **Algorithm**: Uses L2 distance with configurable similarity threshold
- **Returns**: Matching memories ordered by similarity with scores
- **Performance**: Leverages HNSW index for sub-linear search time

## Row Level Security (RLS)

All tables implement comprehensive RLS policies:

### User Data Isolation
- **profiles**: Users can only access their own profile
- **plans**: Users can view own plans + public plans, modify only own
- **workout_sessions**: Users can only access their own sessions
- **sets**: Users can only access sets from their own sessions
- **conversations/memories**: Users can only access their own AI data

### Shared Reference Data
- **exercises**: All authenticated users have read access
- **Reference tables**: All authenticated users have read access
- **Junction tables**: All authenticated users have read access

### Policy Examples
```sql
-- User isolation
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING ((SELECT auth.uid()) = id);

-- Public sharing with ownership
CREATE POLICY "Users can view own plans" ON public.plans
    FOR SELECT USING ((SELECT auth.uid()) = user_id OR is_public = true);

-- Transitive access through relationships
CREATE POLICY "Users can view own sets" ON public.sets
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.workout_sessions 
            WHERE workout_sessions.id = sets.workout_session_id 
            AND workout_sessions.user_id = (SELECT auth.uid())
        )
    );
```

## Query Examples

### User Workout History
```sql
-- Get user's recent workouts with exercise details
SELECT 
    ws.started_at,
    ws.completed_at,
    ws.overall_rpe,
    ws.mood,
    p.name as plan_name,
    COUNT(s.id) as total_sets,
    SUM(s.volume_load) as total_volume
FROM workout_sessions ws
LEFT JOIN plans p ON ws.plan_id = p.id
LEFT JOIN sets s ON ws.id = s.workout_session_id
WHERE ws.user_id = $1
    AND ws.completed_at IS NOT NULL
GROUP BY ws.id, ws.started_at, ws.completed_at, ws.overall_rpe, ws.mood, p.name
ORDER BY ws.started_at DESC
LIMIT 10;
```

### Exercise Performance Progression
```sql
-- Track progression for specific exercise
WITH exercise_progress AS (
    SELECT 
        s.created_at::date as workout_date,
        e.name as exercise_name,
        MAX(s.weight) as max_weight,
        SUM(s.volume_load) as total_volume,
        AVG(s.rpe) as avg_rpe
    FROM sets s
    JOIN exercises e ON s.exercise_id = e.id
    JOIN workout_sessions ws ON s.workout_session_id = ws.id
    WHERE ws.user_id = $1 
        AND e.name = $2
        AND s.set_type = 'working'
    GROUP BY s.created_at::date, e.name
)
SELECT 
    workout_date,
    max_weight,
    total_volume,
    avg_rpe,
    LAG(max_weight) OVER (ORDER BY workout_date) as previous_max_weight
FROM exercise_progress
ORDER BY workout_date;
```

### AI Memory Search
```sql
-- Semantic search through user memories
SELECT 
    content,
    memory_type,
    importance_score,
    similarity,
    created_at
FROM search_memories(
    $1::UUID,          -- user_id
    $2::halfvec(3072), -- query_embedding
    10,                -- limit
    0.7                -- similarity_threshold
)
WHERE memory_type IN ('preference', 'goal', 'achievement')
ORDER BY similarity DESC, importance_score DESC;
```

### Plan Analytics
```sql
-- Analyze plan effectiveness
WITH plan_stats AS (
    SELECT 
        p.name,
        p.goal,
        COUNT(DISTINCT ws.id) as times_followed,
        AVG(ws.overall_rpe) as avg_session_rpe,
        AVG(ws.post_workout_energy) as avg_post_energy,
        SUM(CASE WHEN ws.completed_at IS NOT NULL THEN 1 ELSE 0 END) as completed_sessions
    FROM plans p
    LEFT JOIN workout_sessions ws ON p.id = ws.plan_id
    WHERE p.user_id = $1
    GROUP BY p.id, p.name, p.goal
)
SELECT 
    name,
    goal,
    times_followed,
    completed_sessions,
    ROUND(avg_session_rpe, 1) as avg_rpe,
    ROUND(avg_post_energy, 1) as avg_energy,
    ROUND((completed_sessions::float / NULLIF(times_followed, 0)) * 100, 1) as completion_rate
FROM plan_stats
WHERE times_followed > 0
ORDER BY completion_rate DESC, times_followed DESC;
```

## Maintenance and Monitoring

### Automatic Maintenance
- **updated_at triggers**: Automatically maintain modification timestamps
- **Profile creation**: Auto-create profiles for new auth users
- **Volume calculations**: Stored generated columns for performance

### Performance Monitoring
- Monitor HNSW index performance on memories table
- Watch for foreign key constraint violations
- Track RLS policy performance impact

### Backup Considerations
- Vector embeddings are large - consider selective backup strategies
- Reference data is static - can be excluded from frequent backups
- User workout data is critical - prioritize in backup strategy

### Scaling Considerations
- Partition large tables by user_id for horizontal scaling
- Consider read replicas for analytics workloads
- Monitor vector index memory usage as embeddings grow

## Security Notes

### Data Protection
- All user data isolated via RLS policies
- No cross-user data access possible through application queries
- Database functions use SECURITY DEFINER with restricted search_path

### Vector Search Security
- Embeddings contain semantic information - ensure proper access controls
- Search results filtered by user_id to prevent data leakage
- Consider embedding anonymization for analytics

### Authentication Integration
- Tight integration with Supabase auth system
- JWT tokens validated at database level
- Automatic profile creation prevents orphaned auth records

This documentation provides a comprehensive guide to understanding, querying, and maintaining the Slow Burn database schema. The schema is designed for scalability, security, and performance while supporting both traditional fitness tracking and modern AI-powered features.
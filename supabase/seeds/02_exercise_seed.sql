-- Seed data for Slow Burn fitness application
-- This file populates initial exercise data

-- =============================================================================
-- EXERCISE SEED DATA
-- =============================================================================

-- Insert exercises with enhanced classification
-- Get equipment IDs for reference (will be used in the exercise inserts)

INSERT INTO public.exercises (
    name, description, instructions, tips,
    primary_equipment_id, exercise_category, mechanic_type, body_region,
    difficulty_level, laterality, load_type
) VALUES
-- PUSH MOVEMENTS
(
    'Push-up',
    'Classic bodyweight chest and tricep exercise',
    ARRAY[
        'Start in plank position with hands shoulder-width apart',
        'Lower body until chest nearly touches ground',
        'Push back up to starting position',
        'Keep core tight and body in straight line'
    ],
    ARRAY[
        'Keep elbows at 45-degree angle to body',
        'Squeeze glutes to maintain plank',
        'Full range of motion for maximum benefit'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'bodyweight'),
    'strength', 'compound', 'upper', 'beginner',
    'bilateral', 'bodyweight'
),
(
    'Bench Press',
    'Fundamental horizontal pushing exercise for chest development',
    ARRAY[
        'Lie on bench with feet flat on floor',
        'Grip bar slightly wider than shoulder-width',
        'Lower bar to chest with control',
        'Press bar back to starting position'
    ],
    ARRAY[
        'Keep shoulder blades retracted',
        'Maintain natural arch in lower back',
        'Bar should touch chest at nipple line',
        'Drive legs into ground for stability'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'Incline Bench Press',
    'Upper chest focused bench press variation',
    ARRAY[
        'Set bench to 30-45 degree incline',
        'Lie back with shoulder blades retracted',
        'Lower bar to upper chest with control',
        'Press bar straight up from chest'
    ],
    ARRAY[
        'Target upper portion of chest',
        'Bar touches higher on chest than flat bench',
        'Maintain leg drive and back arch'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'Close-Grip Bench Press',
    'Tricep-focused bench press variation with narrow grip',
    ARRAY[
        'Lie on bench with hands 6-12 inches apart',
        'Keep elbows closer to body than regular bench',
        'Lower bar to lower chest/upper abdomen',
        'Press up focusing on tricep contraction'
    ],
    ARRAY[
        'Primary focus is tricep development',
        'Keep wrists straight and strong',
        'Elbows should track forward, not flare'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'Pause Bench Press',
    'Competition-style bench with controlled pause',
    ARRAY[
        'Set up exactly like regular bench press',
        'Lower bar to chest and pause for 1-2 seconds',
        'Hold bar motionless against chest',
        'Press up explosively after pause'
    ],
    ARRAY[
        'Essential for powerlifting competition prep',
        'Builds strength off the chest',
        'Do not relax during pause'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'advanced',
    'bilateral', 'external'
),
(
    'Dumbbell Bench Press',
    'Unilateral bench press variation for stability',
    ARRAY[
        'Lie on bench holding dumbbells at chest level',
        'Press dumbbells up and slightly inward',
        'Lower with control to stretch position',
        'Press back up to starting position'
    ],
    ARRAY[
        'Greater range of motion than barbell',
        'Requires more stabilization',
        'Can address strength imbalances'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'dumbbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'Tempo Bench Press',
    'Bench press with controlled tempo for increased time under tension',
    ARRAY[
        'Lie on bench with feet flat on floor',
        'Lower bar slowly for 3-4 seconds to chest',
        'Pause briefly at chest',
        'Press bar back up at normal speed'
    ],
    ARRAY[
        'Focus on control during descent',
        'Maintain shoulder blade retraction',
        'Common tempo: 3-1-1-0 (3 sec down, 1 sec pause, 1 sec up, 0 sec rest)'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'Overhead Press',
    'Vertical pressing movement for shoulder and core strength',
    ARRAY[
        'Stand with feet hip-width apart',
        'Grip bar at shoulder level',
        'Press bar straight overhead',
        'Lower with control to starting position'
    ],
    ARRAY[
        'Keep core braced throughout movement',
        'Press bar over mid-foot',
        'Squeeze glutes for stability'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),

-- PULL MOVEMENTS
(
    'Pull-up',
    'Bodyweight vertical pulling exercise for back and biceps',
    ARRAY[
        'Hang from bar with overhand grip',
        'Pull body up until chin clears bar',
        'Lower with control to full extension',
        'Repeat for desired reps'
    ],
    ARRAY[
        'Start from dead hang position',
        'Engage lats to initiate movement',
        'Avoid swinging or kipping'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'pull_up_bar'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'bodyweight'
),

-- SQUAT MOVEMENTS  
(
    'Bodyweight Squat',
    'Fundamental lower body movement pattern',
    ARRAY[
        'Stand with feet shoulder-width apart',
        'Lower body by bending hips and knees',
        'Descend until thighs parallel to floor',
        'Drive through heels to return to standing'
    ],
    ARRAY[
        'Keep chest up and core engaged',
        'Weight should be on heels',
        'Knees track over toes'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'bodyweight'),
    'strength', 'compound', 'lower', 'beginner',
    'bilateral', 'bodyweight'
),
(
    'Back Squat',
    'King of lower body exercises for strength and mass',
    ARRAY[
        'Position bar on upper back in squat rack',
        'Step back with feet shoulder-width apart',
        'Descend by bending hips and knees',
        'Drive through heels to return to standing'
    ],
    ARRAY[
        'Keep chest up and core braced',
        'Descend until hip crease below knee',
        'Maintain neutral spine throughout'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'intermediate',
    'bilateral', 'external'
),
(
    'Front Squat',
    'Quad-dominant squat variation with front-loaded barbell',
    ARRAY[
        'Position bar across front delts and clavicles',
        'Maintain high elbows and upright torso',
        'Descend with knees tracking over toes',
        'Drive through heels while keeping torso upright'
    ],
    ARRAY[
        'Keep elbows high throughout movement',
        'Brace core harder than back squat',
        'Focus on ankle mobility for depth'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'advanced',
    'bilateral', 'external'
),
(
    'Safety Squat Bar Squat',
    'Squat variation with cambered bar and handles',
    ARRAY[
        'Position safety squat bar on upper back',
        'Hold handles for stability and control',
        'Descend with normal squat mechanics',
        'Drive up maintaining forward lean accommodation'
    ],
    ARRAY[
        'Bar naturally shifts center of gravity forward',
        'Great for those with shoulder mobility issues',
        'Increased quadriceps activation'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'safety_squat_bar'),
    'strength', 'compound', 'lower', 'intermediate',
    'bilateral', 'external'
),
(
    'Box Squat',
    'Squat variation with controlled pause on box',
    ARRAY[
        'Set box at parallel or slightly below',
        'Descend and sit back fully on box',
        'Pause briefly maintaining tension',
        'Explode up from seated position'
    ],
    ARRAY[
        'Sit back onto box, do not just touch',
        'Maintain arch and tension during pause',
        'Great for learning proper hip hinge'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'intermediate',
    'bilateral', 'external'
),
(
    'Pause Squat',
    'Squat with controlled pause at bottom position',
    ARRAY[
        'Perform normal squat descent',
        'Pause for 2-3 seconds at bottom',
        'Maintain tension and positioning',
        'Drive up explosively from pause'
    ],
    ARRAY[
        'Do not relax during pause',
        'Keep knees out and chest up',
        'Builds strength out of the hole'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'advanced',
    'bilateral', 'external'
),
(
    'Tempo Squat',
    'Squat with controlled tempo for increased time under tension',
    ARRAY[
        'Position bar on upper back in squat rack',
        'Descend slowly for 3-4 seconds',
        'Pause briefly at bottom position',
        'Drive up at normal speed'
    ],
    ARRAY[
        'Focus on control during descent',
        'Maintain tension throughout movement',
        'Common tempo: 3-1-1-0 (3 sec down, 1 sec pause, 1 sec up, 0 sec rest)'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'intermediate',
    'bilateral', 'external'
),

-- HINGE MOVEMENTS
(
    'Deadlift',
    'Fundamental hip hinge movement for posterior chain strength',
    ARRAY[
        'Stand with feet hip-width apart, bar over mid-foot',
        'Hinge at hips and bend knees to grip bar',
        'Drive through heels and extend hips to stand',
        'Lower bar with control to starting position'
    ],
    ARRAY[
        'Keep bar close to body throughout movement',
        'Maintain neutral spine and engaged core',
        'Lead with hips when lowering'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'full_body', 'intermediate',
    'bilateral', 'external'
),
(
    'Sumo Deadlift',
    'Wide-stance deadlift variation emphasizing hips and quads',
    ARRAY[
        'Stand with wide stance, toes pointed out',
        'Grip bar with hands inside legs',
        'Keep torso more upright than conventional',
        'Drive knees out while extending hips'
    ],
    ARRAY[
        'Mobility requirements are different than conventional',
        'Keep knees tracking over toes',
        'Shorter range of motion but different leverage'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'full_body', 'intermediate',
    'bilateral', 'external'
),
(
    'Romanian Deadlift',
    'Hip-dominant movement emphasizing hamstrings and glutes',
    ARRAY[
        'Stand holding barbell with feet hip-width apart',
        'Hinge at hips, pushing them back',
        'Lower bar along legs until stretch in hamstrings',
        'Drive hips forward to return to standing'
    ],
    ARRAY[
        'Keep knees slightly bent throughout',
        'Maintain natural arch in lower back',
        'Feel stretch in hamstrings at bottom'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'intermediate',
    'bilateral', 'external'
),
(
    'Stiff Leg Deadlift',
    'Straight-leg variation for maximum hamstring stretch',
    ARRAY[
        'Stand holding barbell with legs straight',
        'Hinge at hips keeping legs extended',
        'Lower bar until maximum hamstring stretch',
        'Return by driving hips forward'
    ],
    ARRAY[
        'Requires excellent hamstring flexibility',
        'Keep weight lighter than Romanian deadlift',
        'Focus on stretch and mind-muscle connection'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'advanced',
    'bilateral', 'external'
),
(
    'Trap Bar Deadlift',
    'Deadlift variation using hexagonal trap bar',
    ARRAY[
        'Step inside trap bar with feet hip-width apart',
        'Grip handles at sides, maintain neutral spine',
        'Drive through heels and extend hips to stand',
        'Lower with control to starting position'
    ],
    ARRAY[
        'More quad-dominant than conventional deadlift',
        'Easier to maintain neutral spine',
        'Great for beginners learning hip hinge'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'trap_bar'),
    'strength', 'compound', 'full_body', 'beginner',
    'bilateral', 'external'
),
(
    'Deficit Deadlift',
    'Deadlift from elevated platform for increased range',
    ARRAY[
        'Stand on 1-4 inch platform or plates',
        'Perform conventional deadlift setup',
        'Increased range of motion at bottom',
        'Focus on strength off the floor'
    ],
    ARRAY[
        'Use lighter weight than conventional',
        'Builds strength in hardest part of lift',
        'Requires good mobility and flexibility'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'full_body', 'advanced',
    'bilateral', 'external'
),
(
    'Rack Pull',
    'Partial range deadlift from elevated starting position',
    ARRAY[
        'Set barbell on pins at knee height or higher',
        'Perform deadlift from elevated position',
        'Focus on lockout portion of movement',
        'Lower bar back to pins with control'
    ],
    ARRAY[
        'Allows heavier loading than full deadlift',
        'Builds lockout strength and confidence',
        'Good for those with mobility limitations'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'full_body', 'intermediate',
    'bilateral', 'external'
),
(
    'Tempo Deadlift',
    'Deadlift with controlled tempo for increased time under tension',
    ARRAY[
        'Stand with feet hip-width apart, bar over mid-foot',
        'Lower bar slowly for 3-4 seconds',
        'Pause briefly when bar reaches mid-shin',
        'Drive through heels at normal speed to stand'
    ],
    ARRAY[
        'Focus on control during lowering phase',
        'Maintain bar path close to body',
        'Common tempo: 1-0-3-1 (1 sec up, 0 sec pause, 3 sec down, 1 sec pause)'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'full_body', 'intermediate',
    'bilateral', 'external'
),

-- LUNGE MOVEMENTS
(
    'Bodyweight Lunge',
    'Single-leg movement for unilateral strength and stability',
    ARRAY[
        'Stand with feet hip-width apart',
        'Step forward into lunge position',
        'Lower until both knees at 90 degrees',
        'Push through front heel to return to start'
    ],
    ARRAY[
        'Keep torso upright throughout movement',
        'Front knee should track over ankle',
        'Equal weight on both legs at bottom'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'bodyweight'),
    'strength', 'compound', 'lower', 'beginner',
    'unilateral_alternating', 'bodyweight'
),
(
    'Bulgarian Split Squat',
    'Single-leg squat with rear foot elevated',
    ARRAY[
        'Stand 2-3 feet in front of bench or elevated surface',
        'Place top of rear foot on bench behind you',
        'Lower front leg until thigh parallel to ground',
        'Drive through front heel to return to start'
    ],
    ARRAY[
        'Most weight should be on front leg',
        'Keep torso upright and core engaged',
        'Control the descent, do not bounce'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'bodyweight'),
    'strength', 'compound', 'lower', 'intermediate',
    'unilateral_alternating', 'bodyweight'
),

-- ESSENTIAL POWERBUILDING ACCESSORIES
(
    'Hip Thrust',
    'Glute-dominant exercise for posterior chain development',
    ARRAY[
        'Sit with upper back against bench, barbell over hips',
        'Feet flat on floor, knees bent at 90 degrees',
        'Drive hips up by squeezing glutes hard',
        'Lower with control to starting position'
    ],
    ARRAY[
        'Focus on glute contraction, not back extension',
        'Pause briefly at top of movement',
        'Keep core braced throughout'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'intermediate',
    'bilateral', 'external'
),
(
    'Good Morning',
    'Hip hinge movement for posterior chain and spinal erectors',
    ARRAY[
        'Position barbell on upper back like back squat',
        'Stand with feet hip-width apart',
        'Hinge at hips while keeping knees slightly bent',
        'Return to standing by driving hips forward'
    ],
    ARRAY[
        'Keep chest up and maintain spinal position',
        'Movement should be felt in hamstrings and glutes',
        'Start with lighter weight to learn movement'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'lower', 'advanced',
    'bilateral', 'external'
),
(
    'Barbell Row',
    'Horizontal pulling for back thickness and strength',
    ARRAY[
        'Stand holding barbell with overhand grip',
        'Hinge at hips maintaining neutral spine',
        'Pull bar to lower chest/upper abdomen',
        'Squeeze shoulder blades together at top'
    ],
    ARRAY[
        'Keep core braced throughout movement',
        'Row to same spot consistently',
        'Control both concentric and eccentric'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'T-Bar Row',
    'Horizontal pulling with neutral grip and chest support',
    ARRAY[
        'Stand straddling T-bar with chest against pad',
        'Grip handles with neutral hand position',
        'Pull handles to chest while squeezing shoulder blades',
        'Lower with control to full arm extension'
    ],
    ARRAY[
        'Chest support reduces lower back stress',
        'Focus on pulling with lats and rhomboids',
        'Keep elbows close to body'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'Face Pull',
    'Rear delt and upper back isolation exercise',
    ARRAY[
        'Set cable at upper chest height',
        'Grip rope with overhand grip',
        'Pull rope to face while separating hands',
        'Squeeze shoulder blades and rear delts'
    ],
    ARRAY[
        'Critical for shoulder health and posture',
        'Keep elbows high throughout movement',
        'Focus on external rotation at end range'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'cable_machine'),
    'strength', 'isolation', 'upper', 'beginner',
    'bilateral', 'external'
),
(
    'Dumbbell Flye',
    'Chest isolation exercise with stretched position',
    ARRAY[
        'Lie on bench holding dumbbells over chest',
        'Lower weights out to sides with slight elbow bend',
        'Feel stretch in chest at bottom position',
        'Bring weights back together over chest'
    ],
    ARRAY[
        'Focus on chest stretch and contraction',
        'Keep slight bend in elbows throughout',
        'Control the weight, especially on descent'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'dumbbell'),
    'hypertrophy', 'isolation', 'upper', 'intermediate',
    'bilateral', 'external'
),
(
    'Tricep Dip',
    'Bodyweight tricep exercise with scalable difficulty',
    ARRAY[
        'Position hands on parallel bars or bench edge',
        'Lower body until upper arms parallel to ground',
        'Press up by extending arms fully',
        'Keep torso upright throughout movement'
    ],
    ARRAY[
        'Can be modified with feet elevation or assistance',
        'Focus on tricep contraction',
        'Avoid excessive forward lean'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'parallettes'),
    'strength', 'compound', 'upper', 'intermediate',
    'bilateral', 'bodyweight'
),
(
    'Barbell Curl',
    'Bicep isolation exercise for arm development',
    ARRAY[
        'Stand holding barbell with underhand grip',
        'Keep elbows at sides and curl weight up',
        'Squeeze biceps at top of movement',
        'Lower with control to starting position'
    ],
    ARRAY[
        'Avoid swinging or using momentum',
        'Keep wrists straight and strong',
        'Focus on bicep contraction'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'barbell'),
    'hypertrophy', 'isolation', 'upper', 'beginner',
    'bilateral', 'external'
),
(
    'Glute Ham Raise',
    'Posterior chain exercise for hamstrings and glutes',
    ARRAY[
        'Position on GHD with feet secured',
        'Lower torso under control using hamstrings',
        'Use hamstrings to pull body back to start',
        'Keep core engaged throughout movement'
    ],
    ARRAY[
        'One of the best hamstring exercises',
        'Can modify difficulty with hand position',
        'Focus on hamstring and glute activation'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'glute_ham_developer'),
    'strength', 'compound', 'lower', 'advanced',
    'bilateral', 'bodyweight'
),

-- CORE MOVEMENTS
(
    'Plank',
    'Isometric core strengthening exercise',
    ARRAY[
        'Start in push-up position on forearms',
        'Keep body in straight line from head to heels',
        'Hold position while breathing normally',
        'Maintain neutral spine throughout'
    ],
    ARRAY[
        'Squeeze glutes and engage core',
        'Keep hips level, avoid sagging or piking',
        'Breathe normally throughout hold'
    ],
    (SELECT id FROM public.equipment_types WHERE name = 'bodyweight'),
    'strength', 'isolation', 'core', 'beginner',
    'bilateral', 'bodyweight'
);

-- =============================================================================
-- EXERCISE RELATIONSHIPS
-- =============================================================================

-- Insert exercise movement pattern relationships
INSERT INTO public.exercise_movement_patterns (exercise_id, movement_pattern_id, is_primary)
SELECT 
    e.id,
    mp.id,
    true
FROM public.exercises e
CROSS JOIN public.movement_patterns mp
WHERE 
    -- Push movements
    (e.name = 'Push-up' AND mp.name = 'push_horizontal') OR
    (e.name = 'Bench Press' AND mp.name = 'push_horizontal') OR
    (e.name = 'Incline Bench Press' AND mp.name = 'push_horizontal') OR
    (e.name = 'Close-Grip Bench Press' AND mp.name = 'push_horizontal') OR
    (e.name = 'Pause Bench Press' AND mp.name = 'pause') OR
    (e.name = 'Dumbbell Bench Press' AND mp.name = 'push_horizontal') OR
    (e.name = 'Tempo Bench Press' AND mp.name = 'tempo') OR
    (e.name = 'Overhead Press' AND mp.name = 'push_vertical') OR
    (e.name = 'Tricep Dip' AND mp.name = 'push_vertical') OR
    -- Pull movements
    (e.name = 'Pull-up' AND mp.name = 'pull_vertical') OR
    (e.name = 'Barbell Row' AND mp.name = 'pull_horizontal') OR
    (e.name = 'T-Bar Row' AND mp.name = 'pull_horizontal') OR
    (e.name = 'Face Pull' AND mp.name = 'pull_horizontal') OR
    -- Squat movements
    (e.name = 'Bodyweight Squat' AND mp.name = 'squat') OR
    (e.name = 'Back Squat' AND mp.name = 'squat') OR
    (e.name = 'Front Squat' AND mp.name = 'squat') OR
    (e.name = 'Safety Squat Bar Squat' AND mp.name = 'squat') OR
    (e.name = 'Box Squat' AND mp.name = 'squat') OR
    (e.name = 'Pause Squat' AND mp.name = 'pause') OR
    (e.name = 'Tempo Squat' AND mp.name = 'tempo') OR
    -- Hinge movements
    (e.name = 'Deadlift' AND mp.name = 'hinge') OR
    (e.name = 'Sumo Deadlift' AND mp.name = 'hinge') OR
    (e.name = 'Romanian Deadlift' AND mp.name = 'hinge') OR
    (e.name = 'Stiff Leg Deadlift' AND mp.name = 'hinge') OR
    (e.name = 'Trap Bar Deadlift' AND mp.name = 'hinge') OR
    (e.name = 'Deficit Deadlift' AND mp.name = 'hinge') OR
    (e.name = 'Rack Pull' AND mp.name = 'partial_range') OR
    (e.name = 'Tempo Deadlift' AND mp.name = 'tempo') OR
    (e.name = 'Good Morning' AND mp.name = 'hinge') OR
    -- Lunge movements
    (e.name = 'Bodyweight Lunge' AND mp.name = 'lunge') OR
    (e.name = 'Bulgarian Split Squat' AND mp.name = 'unilateral') OR
    -- Bridge movements
    (e.name = 'Hip Thrust' AND mp.name = 'bridge') OR
    (e.name = 'Glute Ham Raise' AND mp.name = 'hinge')
ON CONFLICT (exercise_id, movement_pattern_id) DO NOTHING;

-- Insert exercise muscle group relationships
INSERT INTO public.exercise_muscles (exercise_id, muscle_group_id, muscle_role, activation_level)
SELECT 
    e.id,
    mg.id,
    muscle_data.role,
    muscle_data.activation
FROM public.exercises e
CROSS JOIN public.muscle_groups mg
CROSS JOIN (
    VALUES 
    -- Push-up
    ('Push-up', 'chest_middle', 'primary', 5),
    ('Push-up', 'triceps_lateral', 'secondary', 4),
    ('Push-up', 'front_delts', 'secondary', 3),
    ('Push-up', 'rectus_abdominis', 'stabilizer', 3),
    
    -- Bench Press
    ('Bench Press', 'chest_middle', 'primary', 5),
    ('Bench Press', 'triceps_lateral', 'secondary', 4),
    ('Bench Press', 'front_delts', 'secondary', 3),
    ('Bench Press', 'serratus', 'stabilizer', 2),
    
    -- Incline Bench Press
    ('Incline Bench Press', 'chest_upper', 'primary', 5),
    ('Incline Bench Press', 'front_delts', 'primary', 4),
    ('Incline Bench Press', 'triceps_lateral', 'secondary', 4),
    
    -- Close-Grip Bench Press
    ('Close-Grip Bench Press', 'triceps_lateral', 'primary', 5),
    ('Close-Grip Bench Press', 'triceps_long', 'primary', 5),
    ('Close-Grip Bench Press', 'chest_middle', 'secondary', 3),
    ('Close-Grip Bench Press', 'front_delts', 'secondary', 3),
    
    -- Pause Bench Press
    ('Pause Bench Press', 'chest_middle', 'primary', 5),
    ('Pause Bench Press', 'triceps_lateral', 'secondary', 4),
    ('Pause Bench Press', 'front_delts', 'secondary', 3),
    
    -- Tempo Bench Press
    ('Tempo Bench Press', 'chest_middle', 'primary', 5),
    ('Tempo Bench Press', 'triceps_lateral', 'secondary', 4),
    ('Tempo Bench Press', 'front_delts', 'secondary', 3),
    ('Tempo Bench Press', 'serratus', 'stabilizer', 3),
    
    -- Dumbbell Bench Press
    ('Dumbbell Bench Press', 'chest_middle', 'primary', 5),
    ('Dumbbell Bench Press', 'triceps_lateral', 'secondary', 4),
    ('Dumbbell Bench Press', 'front_delts', 'secondary', 3),
    ('Dumbbell Bench Press', 'rotator_cuff', 'stabilizer', 4),
    
    -- Overhead Press
    ('Overhead Press', 'front_delts', 'primary', 5),
    ('Overhead Press', 'side_delts', 'primary', 4),
    ('Overhead Press', 'triceps_lateral', 'secondary', 4),
    ('Overhead Press', 'rectus_abdominis', 'stabilizer', 4),
    ('Overhead Press', 'upper_traps', 'stabilizer', 3),
    
    -- Pull-up
    ('Pull-up', 'lats', 'primary', 5),
    ('Pull-up', 'biceps', 'secondary', 4),
    ('Pull-up', 'rhomboids', 'secondary', 4),
    ('Pull-up', 'rear_delts', 'secondary', 3),
    ('Pull-up', 'mid_traps', 'secondary', 3),
    
    
    -- Barbell Row
    ('Barbell Row', 'lats', 'primary', 5),
    ('Barbell Row', 'rhomboids', 'primary', 5),
    ('Barbell Row', 'mid_traps', 'primary', 4),
    ('Barbell Row', 'biceps', 'secondary', 4),
    ('Barbell Row', 'rear_delts', 'secondary', 4),
    
    -- T-Bar Row
    ('T-Bar Row', 'lats', 'primary', 5),
    ('T-Bar Row', 'rhomboids', 'primary', 5),
    ('T-Bar Row', 'mid_traps', 'primary', 4),
    ('T-Bar Row', 'biceps', 'secondary', 4),
    
    -- Face Pull
    ('Face Pull', 'rear_delts', 'primary', 5),
    ('Face Pull', 'mid_traps', 'primary', 4),
    ('Face Pull', 'rhomboids', 'secondary', 4),
    ('Face Pull', 'rotator_cuff', 'secondary', 4),
    
    -- Bodyweight Squat
    ('Bodyweight Squat', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Bodyweight Squat', 'quadriceps_vastus_medialis', 'primary', 5),
    ('Bodyweight Squat', 'glutes_maximus', 'primary', 4),
    ('Bodyweight Squat', 'hamstrings_biceps_femoris', 'secondary', 3),
    
    -- Back Squat
    ('Back Squat', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Back Squat', 'quadriceps_vastus_medialis', 'primary', 5),
    ('Back Squat', 'glutes_maximus', 'primary', 5),
    ('Back Squat', 'hamstrings_biceps_femoris', 'secondary', 4),
    ('Back Squat', 'erector_spinae', 'stabilizer', 4),
    ('Back Squat', 'rectus_abdominis', 'stabilizer', 4),
    
    -- Front Squat
    ('Front Squat', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Front Squat', 'quadriceps_vastus_medialis', 'primary', 5),
    ('Front Squat', 'quadriceps_rectus_femoris', 'primary', 5),
    ('Front Squat', 'glutes_maximus', 'secondary', 4),
    ('Front Squat', 'rectus_abdominis', 'stabilizer', 5),
    ('Front Squat', 'erector_spinae', 'stabilizer', 4),
    
    -- Safety Squat Bar Squat
    ('Safety Squat Bar Squat', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Safety Squat Bar Squat', 'quadriceps_vastus_medialis', 'primary', 5),
    ('Safety Squat Bar Squat', 'glutes_maximus', 'primary', 4),
    ('Safety Squat Bar Squat', 'rectus_abdominis', 'stabilizer', 4),
    
    -- Box Squat
    ('Box Squat', 'glutes_maximus', 'primary', 5),
    ('Box Squat', 'quadriceps_vastus_lateralis', 'primary', 4),
    ('Box Squat', 'hamstrings_biceps_femoris', 'secondary', 4),
    
    -- Pause Squat
    ('Pause Squat', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Pause Squat', 'quadriceps_vastus_medialis', 'primary', 5),
    ('Pause Squat', 'glutes_maximus', 'primary', 5),
    ('Pause Squat', 'rectus_abdominis', 'stabilizer', 5),
    
    -- Tempo Squat
    ('Tempo Squat', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Tempo Squat', 'quadriceps_vastus_medialis', 'primary', 5),
    ('Tempo Squat', 'glutes_maximus', 'primary', 5),
    ('Tempo Squat', 'hamstrings_biceps_femoris', 'secondary', 4),
    ('Tempo Squat', 'rectus_abdominis', 'stabilizer', 4),
    
    -- Deadlift
    ('Deadlift', 'hamstrings_biceps_femoris', 'primary', 5),
    ('Deadlift', 'glutes_maximus', 'primary', 5),
    ('Deadlift', 'erector_spinae', 'primary', 4),
    ('Deadlift', 'lats', 'stabilizer', 4),
    ('Deadlift', 'upper_traps', 'stabilizer', 4),
    ('Deadlift', 'forearms_flexors', 'stabilizer', 5),
    
    -- Sumo Deadlift
    ('Sumo Deadlift', 'glutes_maximus', 'primary', 5),
    ('Sumo Deadlift', 'quadriceps_vastus_lateralis', 'primary', 4),
    ('Sumo Deadlift', 'adductors', 'primary', 4),
    ('Sumo Deadlift', 'hamstrings_biceps_femoris', 'secondary', 4),
    ('Sumo Deadlift', 'erector_spinae', 'stabilizer', 4),
    
    -- Romanian Deadlift
    ('Romanian Deadlift', 'hamstrings_biceps_femoris', 'primary', 5),
    ('Romanian Deadlift', 'hamstrings_semitendinosus', 'primary', 5),
    ('Romanian Deadlift', 'glutes_maximus', 'primary', 5),
    ('Romanian Deadlift', 'erector_spinae', 'stabilizer', 4),
    
    -- Stiff Leg Deadlift
    ('Stiff Leg Deadlift', 'hamstrings_biceps_femoris', 'primary', 5),
    ('Stiff Leg Deadlift', 'hamstrings_semitendinosus', 'primary', 5),
    ('Stiff Leg Deadlift', 'glutes_maximus', 'secondary', 4),
    
    -- Trap Bar Deadlift
    ('Trap Bar Deadlift', 'quadriceps_vastus_lateralis', 'primary', 4),
    ('Trap Bar Deadlift', 'glutes_maximus', 'primary', 5),
    ('Trap Bar Deadlift', 'hamstrings_biceps_femoris', 'primary', 4),
    ('Trap Bar Deadlift', 'erector_spinae', 'stabilizer', 4),
    
    -- Deficit Deadlift
    ('Deficit Deadlift', 'hamstrings_biceps_femoris', 'primary', 5),
    ('Deficit Deadlift', 'glutes_maximus', 'primary', 5),
    ('Deficit Deadlift', 'erector_spinae', 'primary', 4),
    ('Deficit Deadlift', 'quadriceps_vastus_lateralis', 'secondary', 4),
    
    -- Rack Pull
    ('Rack Pull', 'erector_spinae', 'primary', 5),
    ('Rack Pull', 'upper_traps', 'primary', 5),
    ('Rack Pull', 'glutes_maximus', 'secondary', 4),
    ('Rack Pull', 'forearms_flexors', 'stabilizer', 5),
    
    -- Tempo Deadlift
    ('Tempo Deadlift', 'hamstrings_biceps_femoris', 'primary', 5),
    ('Tempo Deadlift', 'glutes_maximus', 'primary', 5),
    ('Tempo Deadlift', 'erector_spinae', 'primary', 4),
    ('Tempo Deadlift', 'lats', 'stabilizer', 4),
    ('Tempo Deadlift', 'forearms_flexors', 'stabilizer', 5),
    
    -- Bodyweight Lunge
    ('Bodyweight Lunge', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Bodyweight Lunge', 'glutes_maximus', 'primary', 4),
    ('Bodyweight Lunge', 'hamstrings_biceps_femoris', 'secondary', 3),
    ('Bodyweight Lunge', 'rectus_abdominis', 'stabilizer', 3),
    
    -- Bulgarian Split Squat
    ('Bulgarian Split Squat', 'quadriceps_vastus_lateralis', 'primary', 5),
    ('Bulgarian Split Squat', 'glutes_maximus', 'primary', 5),
    ('Bulgarian Split Squat', 'hamstrings_biceps_femoris', 'secondary', 3),
    ('Bulgarian Split Squat', 'glutes_medius', 'stabilizer', 4),
    
    -- Hip Thrust
    ('Hip Thrust', 'glutes_maximus', 'primary', 5),
    ('Hip Thrust', 'hamstrings_biceps_femoris', 'secondary', 3),
    ('Hip Thrust', 'rectus_abdominis', 'stabilizer', 3),
    
    -- Good Morning
    ('Good Morning', 'hamstrings_biceps_femoris', 'primary', 5),
    ('Good Morning', 'glutes_maximus', 'primary', 4),
    ('Good Morning', 'erector_spinae', 'primary', 5),
    
    -- Dumbbell Flye
    ('Dumbbell Flye', 'chest_middle', 'primary', 5),
    ('Dumbbell Flye', 'chest_upper', 'secondary', 3),
    ('Dumbbell Flye', 'front_delts', 'stabilizer', 3),
    
    -- Tricep Dip
    ('Tricep Dip', 'triceps_lateral', 'primary', 5),
    ('Tricep Dip', 'triceps_long', 'primary', 5),
    ('Tricep Dip', 'chest_lower', 'secondary', 3),
    ('Tricep Dip', 'front_delts', 'secondary', 3),
    
    -- Barbell Curl
    ('Barbell Curl', 'biceps', 'primary', 5),
    ('Barbell Curl', 'brachialis', 'secondary', 4),
    ('Barbell Curl', 'forearms_flexors', 'stabilizer', 3),
    
    -- Glute Ham Raise
    ('Glute Ham Raise', 'hamstrings_biceps_femoris', 'primary', 5),
    ('Glute Ham Raise', 'hamstrings_semitendinosus', 'primary', 5),
    ('Glute Ham Raise', 'glutes_maximus', 'primary', 4),
    ('Glute Ham Raise', 'erector_spinae', 'stabilizer', 3),
    
    -- Plank
    ('Plank', 'rectus_abdominis', 'primary', 5),
    ('Plank', 'transverse_abdominis', 'primary', 5),
    ('Plank', 'front_delts', 'stabilizer', 3),
    ('Plank', 'glutes_maximus', 'stabilizer', 3)
) AS muscle_data(exercise_name, muscle_name, role, activation)
WHERE e.name = muscle_data.exercise_name AND mg.name = muscle_data.muscle_name
ON CONFLICT (exercise_id, muscle_group_id) DO NOTHING;
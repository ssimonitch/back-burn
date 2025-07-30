-- Seed data for Slow Burn fitness application
-- This file populates reference data

-- =============================================================================
-- REFERENCE DATA
-- =============================================================================

-- Insert training styles reference data
INSERT INTO public.training_styles (name, description, typical_rep_range, typical_set_range, rest_periods, focus_description) VALUES
('powerlifting', 'Competition-focused strength training emphasizing squat, bench press, and deadlift', '1-6', '3-8', '3-8 minutes', 'Maximal strength development and technique refinement for competition lifts'),
('bodybuilding', 'Physique-focused training emphasizing muscle hypertrophy and definition', '6-15', '3-6', '60-180 seconds', 'Muscle size, symmetry, and definition through progressive overload and volume'),
('powerbuilding', 'Hybrid approach combining strength and hypertrophy training methods', '1-15', '3-8', '90-300 seconds', 'Building both maximal strength and muscle size through varied rep ranges'),
('general_fitness', 'Well-rounded training for overall health, strength, and conditioning', '8-20', '2-4', '30-120 seconds', 'Functional movement, cardiovascular health, and basic strength development'),
('athletic_performance', 'Sport-specific training emphasizing power, speed, and movement quality', '1-12', '3-6', '60-300 seconds', 'Sport-specific strength, power, speed, and movement efficiency')
ON CONFLICT (name) DO NOTHING;

-- Insert specialized muscle groups
INSERT INTO public.muscle_groups (name, muscle_region, description) VALUES
-- Upper region specializations
('serratus_anterior', 'upper', 'Muscle responsible for protraction and upward rotation of the scapula, important for shoulder health and pressing movements'),
('rotator_cuff', 'upper', 'Group of four muscles (supraspinatus, infraspinatus, teres minor, subscapularis) that stabilize the shoulder joint'),
-- Lower region specializations
('gluteus_medius', 'lower', 'Hip abductor and stabilizer muscle crucial for single-leg stability and injury prevention'),
('tibialis_anterior', 'lower', 'Shin muscle responsible for dorsiflexion and foot stability during gait and jumping'),
-- Core region specializations
('spinal_erectors', 'core', 'Deep back muscles that extend and stabilize the spine, essential for posture and lifting mechanics'),
-- Posterior chain specialization
('posterior_chain_complex', 'posterior_chain', 'Integrated system of glutes, hamstrings, erector spinae, and upper back muscles working together in hip-hinge patterns')
ON CONFLICT (name) DO NOTHING;

-- Insert core movement patterns
INSERT INTO public.movement_patterns (name, description) VALUES
('squat', 'Hip and knee dominant movement - squatting motion'),
('hinge', 'Hip dominant movement - bending at hips with minimal knee bend'),
('push_vertical', 'Vertical pushing movement - overhead pressing'),
('push_horizontal', 'Horizontal pushing movement - bench press, push-ups'),
('pull_vertical', 'Vertical pulling movement - pull-ups, lat pulldowns'),
('pull_horizontal', 'Horizontal pulling movement - rows'),
('carry', 'Loaded carrying movement - farmers walks, suitcase carries'),
('rotate', 'Rotational movement - wood chops, Russian twists'),
('lunge', 'Single leg movement - lunges, step-ups'),
('bridge', 'Hip extension movement - bridges, hip thrusts'),
-- Powerlifting-specific movement patterns
('pause', 'Pause variation of any movement with controlled stop'),
('tempo', 'Tempo-controlled movement with specific timing'),
('accommodating_resistance', 'Movement with variable resistance (chains/bands)'),
('partial_range', 'Partial range of motion movement (pins, blocks)'),
('isometric', 'Static holding movement at specific joint angle'),
('explosive', 'Explosive/speed movement emphasizing rate of force development'),
('unilateral', 'Single-limb movement pattern'),
('gait', 'Walking or stepping movement patterns')
ON CONFLICT (name) DO NOTHING;

-- Insert muscle groups
INSERT INTO public.muscle_groups (name, muscle_region, description) VALUES
-- Upper body - detailed breakdown for powerlifting
('chest_upper', 'upper', 'Upper pectoralis major (clavicular head)'),
('chest_middle', 'upper', 'Middle pectoralis major (sternal head)'),
('chest_lower', 'upper', 'Lower pectoralis major and minor'),
('front_delts', 'upper', 'Anterior deltoids'),
('side_delts', 'upper', 'Medial/lateral deltoids'),
('rear_delts', 'upper', 'Posterior deltoids'),
('triceps_long', 'upper', 'Triceps brachii long head'),
('triceps_lateral', 'upper', 'Triceps brachii lateral head'),
('triceps_medial', 'upper', 'Triceps brachii medial head'),
('biceps', 'upper', 'Biceps brachii'),
('brachialis', 'upper', 'Brachialis muscle'),
('forearms_flexors', 'upper', 'Forearm flexor group'),
('forearms_extensors', 'upper', 'Forearm extensor group'),
('lats', 'upper', 'Latissimus dorsi'),
('rhomboids', 'upper', 'Rhomboids major and minor'),
('mid_traps', 'upper', 'Middle trapezius'),
('upper_traps', 'upper', 'Upper trapezius'),
('lower_traps', 'upper', 'Lower trapezius'),
('serratus', 'upper', 'Serratus anterior'),
('rotator_cuff', 'upper', 'Rotator cuff complex (SITS muscles)'),
-- Lower body - powerlifting-specific breakdown
('quadriceps_vastus_lateralis', 'lower', 'Vastus lateralis'),
('quadriceps_vastus_medialis', 'lower', 'Vastus medialis'),
('quadriceps_vastus_intermedius', 'lower', 'Vastus intermedius'),
('quadriceps_rectus_femoris', 'lower', 'Rectus femoris'),
('hamstrings_biceps_femoris', 'lower', 'Biceps femoris'),
('hamstrings_semitendinosus', 'lower', 'Semitendinosus'),
('hamstrings_semimembranosus', 'lower', 'Semimembranosus'),
('glutes_maximus', 'lower', 'Gluteus maximus'),
('glutes_medius', 'lower', 'Gluteus medius'),
('glutes_minimus', 'lower', 'Gluteus minimus'),
('calves_gastrocnemius', 'lower', 'Gastrocnemius'),
('calves_soleus', 'lower', 'Soleus'),
('hip_flexors', 'lower', 'Hip flexor complex (iliopsoas)'),
('adductors', 'lower', 'Hip adductor group'),
('abductors', 'lower', 'Hip abductor group'),
('hip_external_rotators', 'lower', 'Deep hip external rotators'),
-- Core - powerlifting-specific breakdown
('rectus_abdominis', 'core', 'Rectus abdominis (six-pack)'),
('obliques_external', 'core', 'External obliques'),
('obliques_internal', 'core', 'Internal obliques'),
('transverse_abdominis', 'core', 'Transverse abdominis (deep core)'),
('erector_spinae', 'core', 'Erector spinae group'),
('multifidus', 'core', 'Multifidus stabilizers'),
('quadratus_lumborum', 'core', 'Quadratus lumborum'),
('diaphragm', 'core', 'Diaphragm for breathing and stability'),
('pelvic_floor', 'core', 'Pelvic floor muscles')
ON CONFLICT (name) DO NOTHING;

-- Insert equipment types
INSERT INTO public.equipment_types (name, category, description) VALUES
-- Free weights
('barbell', 'free_weight', 'Standard Olympic barbell'),
('dumbbell', 'free_weight', 'Dumbbells - adjustable or fixed'),
('trap_bar', 'free_weight', 'Hexagonal/trap bar for deadlifts'),
-- Powerlifting-specific barbells
('safety_squat_bar', 'free_weight', 'Safety squat bar with camber and handles'),
-- Machines
('cable_machine', 'cable', 'Cable crossover or functional trainer'),
('glute_ham_developer', 'machine', 'GHD for posterior chain development'),
-- Bodyweight/Other
('bodyweight', 'bodyweight', 'No equipment needed'),
('pull_up_bar', 'bodyweight', 'Pull-up or chin-up bar'),
('parallettes', 'bodyweight', 'Parallel bars for calisthenics')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- GYM BUDDY – Seed Data for Development
-- ============================================================
-- NOTE: Before running this, create users in Supabase Auth first.
-- This seed data assumes you have created the following users
-- in Supabase Dashboard → Authentication → Users:
--
-- 1. admin@gymbuddy.com    (password: Admin@123)
-- 2. owner@fitzone.com     (password: Owner@123)
-- 3. reception@fitzone.com (password: Reception@123)
-- 4. trainer@fitzone.com   (password: Trainer@123)
-- 5. member@fitzone.com    (password: Member@123)
--
-- After creating users, replace the UUIDs below with actual
-- user IDs from Supabase Auth dashboard.
-- ============================================================

-- !! REPLACE THESE WITH ACTUAL AUTH USER IDs !!
-- You can find user IDs in Supabase Dashboard → Authentication → Users
DO $$
DECLARE
    v_admin_id UUID := '00000000-0000-0000-0000-000000000001';  -- REPLACE
    v_owner_id UUID := '00000000-0000-0000-0000-000000000002';  -- REPLACE
    v_receptionist_id UUID := '00000000-0000-0000-0000-000000000003';  -- REPLACE
    v_trainer_id UUID := '00000000-0000-0000-0000-000000000004';  -- REPLACE
    v_member_user_id UUID := '00000000-0000-0000-0000-000000000005';  -- REPLACE
    
    v_gym_id UUID;
    v_plan_monthly UUID;
    v_plan_quarterly UUID;
    v_plan_half_yearly UUID;
    v_plan_yearly UUID;
    
    v_member_ids UUID[];
    v_membership_ids UUID[];
    v_m_id UUID;
    v_mm_id UUID;
BEGIN

-- ============================================================
-- 1. INSERT GYM
-- ============================================================
INSERT INTO public.gyms (id, name, slug, owner_id, address, city, state, phone, email, inactivity_threshold_days)
VALUES (
    gen_random_uuid(), 'FitZone Gym', 'fitzone',
    v_owner_id,
    '123, MG Road, Sector 15',
    'Mumbai', 'Maharashtra',
    '9876543210', 'info@fitzonegym.com', 15
)
RETURNING id INTO v_gym_id;

-- ============================================================
-- 2. UPDATE PROFILES (created by trigger, now update with gym_id & role)
-- ============================================================
-- Note: profiles are auto-created by the trigger. If running this
-- without the trigger, insert them manually:

INSERT INTO public.profiles (id, gym_id, role, full_name, phone, email)
VALUES
    (v_admin_id, NULL, 'admin', 'Platform Admin', '9000000001', 'admin@gymbuddy.com'),
    (v_owner_id, v_gym_id, 'owner', 'Rajesh Sharma', '9876543210', 'owner@fitzone.com'),
    (v_receptionist_id, v_gym_id, 'receptionist', 'Priya Patel', '9876543211', 'reception@fitzone.com'),
    (v_trainer_id, v_gym_id, 'trainer', 'Vikram Singh', '9876543212', 'trainer@fitzone.com'),
    (v_member_user_id, v_gym_id, 'member', 'Amit Kumar', '9876543213', 'member@fitzone.com')
ON CONFLICT (id) DO UPDATE SET
    gym_id = EXCLUDED.gym_id,
    role = EXCLUDED.role,
    full_name = EXCLUDED.full_name,
    phone = EXCLUDED.phone;

-- ============================================================
-- 3. INSERT MEMBERSHIP PLANS
-- ============================================================
INSERT INTO public.membership_plans (id, gym_id, name, duration_days, price, description, is_active)
VALUES
    (gen_random_uuid(), v_gym_id, 'Monthly', 30, 999.00, '1 Month gym access with basic equipment', true),
    (gen_random_uuid(), v_gym_id, 'Quarterly', 90, 2499.00, '3 Months gym access with all equipment', true),
    (gen_random_uuid(), v_gym_id, 'Half-Yearly', 180, 4499.00, '6 Months gym access with trainer support', true),
    (gen_random_uuid(), v_gym_id, 'Yearly', 365, 7999.00, '12 Months premium access with personal training', true)
RETURNING id INTO v_plan_monthly;

-- Get plan IDs
SELECT id INTO v_plan_monthly FROM public.membership_plans WHERE gym_id = v_gym_id AND name = 'Monthly';
SELECT id INTO v_plan_quarterly FROM public.membership_plans WHERE gym_id = v_gym_id AND name = 'Quarterly';
SELECT id INTO v_plan_half_yearly FROM public.membership_plans WHERE gym_id = v_gym_id AND name = 'Half-Yearly';
SELECT id INTO v_plan_yearly FROM public.membership_plans WHERE gym_id = v_gym_id AND name = 'Yearly';

-- ============================================================
-- 4. INSERT MEMBERS (10 realistic Indian members)
-- ============================================================
INSERT INTO public.members (id, gym_id, member_code, full_name, phone, email, age, gender, address, emergency_contact, qr_code_data, status, joined_date)
VALUES
    (gen_random_uuid(), v_gym_id, 'FIT-0001', 'Amit Kumar', '9876543213', 'amit.kumar@email.com', 28, 'Male', 'Flat 203, Sahil Apartments, Andheri West', '9876543299', 'GYMBUDDY-FIT-0001', 'active', CURRENT_DATE - INTERVAL '60 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0002', 'Sneha Reddy', '9876543214', 'sneha.r@email.com', 25, 'Female', '15, Lake View Colony, Bandra', '9876543298', 'GYMBUDDY-FIT-0002', 'active', CURRENT_DATE - INTERVAL '45 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0003', 'Rahul Verma', '9876543215', 'rahul.v@email.com', 32, 'Male', '8/2, Shanti Nagar, Powai', '9876543297', 'GYMBUDDY-FIT-0003', 'active', CURRENT_DATE - INTERVAL '90 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0004', 'Pooja Nair', '9876543216', 'pooja.n@email.com', 27, 'Female', 'B-12, Sunrise Towers, Dadar', '9876543296', 'GYMBUDDY-FIT-0004', 'active', CURRENT_DATE - INTERVAL '30 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0005', 'Arjun Mehta', '9876543217', 'arjun.m@email.com', 35, 'Male', '42, Green Park, Juhu', '9876543295', 'GYMBUDDY-FIT-0005', 'active', CURRENT_DATE - INTERVAL '120 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0006', 'Kavita Deshmukh', '9876543218', 'kavita.d@email.com', 29, 'Female', '7, Prabhat Road, Vile Parle', '9876543294', 'GYMBUDDY-FIT-0006', 'inactive', CURRENT_DATE - INTERVAL '150 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0007', 'Suresh Iyer', '9876543219', 'suresh.i@email.com', 40, 'Male', '204, Krishna Complex, Malad', '9876543293', 'GYMBUDDY-FIT-0007', 'active', CURRENT_DATE - INTERVAL '200 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0008', 'Deepika Sharma', '9876543220', 'deepika.s@email.com', 23, 'Female', '3A, Royal Heights, Goregaon', '9876543292', 'GYMBUDDY-FIT-0008', 'expired', CURRENT_DATE - INTERVAL '180 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0009', 'Manish Gupta', '9876543221', 'manish.g@email.com', 31, 'Male', '56, Nehru Enclave, Kandivali', '9876543291', 'GYMBUDDY-FIT-0009', 'active', CURRENT_DATE - INTERVAL '15 days'),
    (gen_random_uuid(), v_gym_id, 'FIT-0010', 'Ananya Singh', '9876543222', 'ananya.s@email.com', 26, 'Female', '11, Orchid Park, Borivali', '9876543290', 'GYMBUDDY-FIT-0010', 'active', CURRENT_DATE - INTERVAL '7 days');

-- Get member IDs for subsequent inserts
SELECT ARRAY_AGG(id ORDER BY member_code) INTO v_member_ids FROM public.members WHERE gym_id = v_gym_id;

-- ============================================================
-- 5. INSERT MEMBERSHIPS
-- ============================================================
-- Amit - Quarterly (active)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[1], v_plan_quarterly, CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '60 days', 'active');

-- Sneha - Monthly (expiring soon)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[2], v_plan_monthly, CURRENT_DATE - INTERVAL '25 days', CURRENT_DATE + INTERVAL '5 days', 'active');

-- Rahul - Yearly (active)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[3], v_plan_yearly, CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE + INTERVAL '275 days', 'active');

-- Pooja - Monthly (active)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[4], v_plan_monthly, CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE + INTERVAL '20 days', 'active');

-- Arjun - Half-Yearly (expiring within 15 days)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[5], v_plan_half_yearly, CURRENT_DATE - INTERVAL '170 days', CURRENT_DATE + INTERVAL '10 days', 'active');

-- Kavita - Monthly (expired)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[6], v_plan_monthly, CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE - INTERVAL '30 days', 'expired');

-- Suresh - Yearly (active)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[7], v_plan_yearly, CURRENT_DATE - INTERVAL '200 days', CURRENT_DATE + INTERVAL '165 days', 'active');

-- Deepika - Quarterly (expired)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[8], v_plan_quarterly, CURRENT_DATE - INTERVAL '120 days', CURRENT_DATE - INTERVAL '30 days', 'expired');

-- Manish - Monthly (active, new)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[9], v_plan_monthly, CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '25 days', 'active');

-- Ananya - Monthly (active, very new)
INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status)
VALUES (v_gym_id, v_member_ids[10], v_plan_monthly, CURRENT_DATE - INTERVAL '2 days', CURRENT_DATE + INTERVAL '28 days', 'active');

-- ============================================================
-- 6. INSERT PAYMENTS
-- ============================================================
INSERT INTO public.payments (gym_id, member_id, amount, payment_method, transaction_ref, payment_date, receipt_number, recorded_by)
VALUES
    (v_gym_id, v_member_ids[1], 2499.00, 'UPI', 'UPI-TXN-001234', CURRENT_DATE - INTERVAL '30 days', 'RCP-FIT-00001', v_receptionist_id),
    (v_gym_id, v_member_ids[2], 999.00, 'Cash', NULL, CURRENT_DATE - INTERVAL '25 days', 'RCP-FIT-00002', v_receptionist_id),
    (v_gym_id, v_member_ids[3], 7999.00, 'Bank Transfer', 'NEFT-REF-5678', CURRENT_DATE - INTERVAL '90 days', 'RCP-FIT-00003', v_receptionist_id),
    (v_gym_id, v_member_ids[4], 999.00, 'UPI', 'UPI-TXN-004567', CURRENT_DATE - INTERVAL '10 days', 'RCP-FIT-00004', v_receptionist_id),
    (v_gym_id, v_member_ids[5], 4499.00, 'Cash', NULL, CURRENT_DATE - INTERVAL '170 days', 'RCP-FIT-00005', v_receptionist_id),
    (v_gym_id, v_member_ids[6], 999.00, 'UPI', 'UPI-TXN-007890', CURRENT_DATE - INTERVAL '60 days', 'RCP-FIT-00006', v_receptionist_id),
    (v_gym_id, v_member_ids[7], 7999.00, 'Bank Transfer', 'NEFT-REF-1234', CURRENT_DATE - INTERVAL '200 days', 'RCP-FIT-00007', v_receptionist_id),
    (v_gym_id, v_member_ids[8], 2499.00, 'Cash', NULL, CURRENT_DATE - INTERVAL '120 days', 'RCP-FIT-00008', v_receptionist_id),
    (v_gym_id, v_member_ids[9], 999.00, 'UPI', 'UPI-TXN-009012', CURRENT_DATE - INTERVAL '5 days', 'RCP-FIT-00009', v_receptionist_id),
    (v_gym_id, v_member_ids[10], 999.00, 'Cash', NULL, CURRENT_DATE - INTERVAL '2 days', 'RCP-FIT-00010', v_receptionist_id);

-- ============================================================
-- 7. INSERT ATTENDANCE (scattered over last 30 days)
-- ============================================================
-- Active members get regular attendance, some sporadic
INSERT INTO public.attendance (gym_id, member_id, check_in_date, check_in_time)
VALUES
    -- Amit - regular (last 7 days)
    (v_gym_id, v_member_ids[1], CURRENT_DATE, '07:30:00'),
    (v_gym_id, v_member_ids[1], CURRENT_DATE - INTERVAL '1 day', '07:45:00'),
    (v_gym_id, v_member_ids[1], CURRENT_DATE - INTERVAL '2 days', '08:00:00'),
    (v_gym_id, v_member_ids[1], CURRENT_DATE - INTERVAL '3 days', '07:30:00'),
    (v_gym_id, v_member_ids[1], CURRENT_DATE - INTERVAL '5 days', '07:15:00'),
    (v_gym_id, v_member_ids[1], CURRENT_DATE - INTERVAL '7 days', '08:30:00'),
    (v_gym_id, v_member_ids[1], CURRENT_DATE - INTERVAL '10 days', '07:00:00'),
    -- Sneha - regular
    (v_gym_id, v_member_ids[2], CURRENT_DATE, '09:00:00'),
    (v_gym_id, v_member_ids[2], CURRENT_DATE - INTERVAL '1 day', '09:15:00'),
    (v_gym_id, v_member_ids[2], CURRENT_DATE - INTERVAL '3 days', '09:00:00'),
    (v_gym_id, v_member_ids[2], CURRENT_DATE - INTERVAL '5 days', '09:30:00'),
    -- Rahul - moderate
    (v_gym_id, v_member_ids[3], CURRENT_DATE - INTERVAL '1 day', '18:00:00'),
    (v_gym_id, v_member_ids[3], CURRENT_DATE - INTERVAL '4 days', '17:45:00'),
    (v_gym_id, v_member_ids[3], CURRENT_DATE - INTERVAL '8 days', '18:30:00'),
    -- Pooja - regular
    (v_gym_id, v_member_ids[4], CURRENT_DATE, '10:00:00'),
    (v_gym_id, v_member_ids[4], CURRENT_DATE - INTERVAL '2 days', '10:15:00'),
    (v_gym_id, v_member_ids[4], CURRENT_DATE - INTERVAL '4 days', '10:00:00'),
    -- Arjun - inactive (last visit 20 days ago)
    (v_gym_id, v_member_ids[5], CURRENT_DATE - INTERVAL '20 days', '06:00:00'),
    (v_gym_id, v_member_ids[5], CURRENT_DATE - INTERVAL '25 days', '06:15:00'),
    -- Kavita - very inactive (expired, last visit 45 days ago)
    (v_gym_id, v_member_ids[6], CURRENT_DATE - INTERVAL '45 days', '17:00:00'),
    -- Suresh - sporadic (last visit 18 days ago)
    (v_gym_id, v_member_ids[7], CURRENT_DATE - INTERVAL '18 days', '19:00:00'),
    (v_gym_id, v_member_ids[7], CURRENT_DATE - INTERVAL '25 days', '19:30:00'),
    -- Deepika - expired, last visit 35 days ago
    (v_gym_id, v_member_ids[8], CURRENT_DATE - INTERVAL '35 days', '16:00:00'),
    -- Manish - new, visited twice
    (v_gym_id, v_member_ids[9], CURRENT_DATE - INTERVAL '1 day', '08:00:00'),
    (v_gym_id, v_member_ids[9], CURRENT_DATE - INTERVAL '3 days', '08:15:00');
    -- Ananya (member 10) - never attended (new member, no attendance records)

-- ============================================================
-- 8. INSERT TRAINER ASSIGNMENTS
-- ============================================================
INSERT INTO public.trainer_assignments (gym_id, trainer_id, member_id)
VALUES
    (v_gym_id, v_trainer_id, v_member_ids[1]),  -- Amit
    (v_gym_id, v_trainer_id, v_member_ids[2]),  -- Sneha
    (v_gym_id, v_trainer_id, v_member_ids[3]),  -- Rahul
    (v_gym_id, v_trainer_id, v_member_ids[4]),  -- Pooja
    (v_gym_id, v_trainer_id, v_member_ids[5]);  -- Arjun

-- ============================================================
-- 9. INSERT WORKOUT PLANS (for Amit)
-- ============================================================
-- Monday - Chest & Triceps
INSERT INTO public.workout_plans (id, member_id, trainer_id, gym_id, day_of_week, is_active)
VALUES (gen_random_uuid(), v_member_ids[1], v_trainer_id, v_gym_id, 'Monday', true)
RETURNING id INTO v_m_id;

INSERT INTO public.workout_exercises (workout_plan_id, exercise_name, sets, reps, rest_seconds, instructions, trainer_notes, order_index)
VALUES
    (v_m_id, 'Flat Bench Press', 4, '12, 10, 8, 6', 90, 'Keep back flat, controlled movement', 'Increase weight gradually', 1),
    (v_m_id, 'Incline Dumbbell Press', 3, '12', 60, '30-degree incline, full range of motion', NULL, 2),
    (v_m_id, 'Cable Flyes', 3, '15', 45, 'Squeeze at the top, slow negative', 'Focus on contraction', 3),
    (v_m_id, 'Tricep Pushdowns', 3, '15', 45, 'Keep elbows locked, only forearms move', NULL, 4),
    (v_m_id, 'Overhead Tricep Extension', 3, '12', 60, 'Full stretch at bottom', NULL, 5);

-- Wednesday - Back & Biceps
INSERT INTO public.workout_plans (id, member_id, trainer_id, gym_id, day_of_week, is_active)
VALUES (gen_random_uuid(), v_member_ids[1], v_trainer_id, v_gym_id, 'Wednesday', true)
RETURNING id INTO v_m_id;

INSERT INTO public.workout_exercises (workout_plan_id, exercise_name, sets, reps, rest_seconds, instructions, trainer_notes, order_index)
VALUES
    (v_m_id, 'Deadlift', 4, '8, 6, 4, 4', 120, 'Maintain neutral spine, brace core', 'Warm up properly!', 1),
    (v_m_id, 'Lat Pulldown', 3, '12', 60, 'Wide grip, pull to upper chest', NULL, 2),
    (v_m_id, 'Seated Cable Row', 3, '12', 60, 'Squeeze shoulder blades together', NULL, 3),
    (v_m_id, 'Barbell Curl', 3, '12', 45, 'No swinging, controlled reps', NULL, 4),
    (v_m_id, 'Hammer Curls', 3, '12', 45, 'Neutral grip, alternating arms', 'Go heavy', 5);

-- Friday - Legs & Shoulders
INSERT INTO public.workout_plans (id, member_id, trainer_id, gym_id, day_of_week, is_active)
VALUES (gen_random_uuid(), v_member_ids[1], v_trainer_id, v_gym_id, 'Friday', true)
RETURNING id INTO v_m_id;

INSERT INTO public.workout_exercises (workout_plan_id, exercise_name, sets, reps, rest_seconds, instructions, trainer_notes, order_index)
VALUES
    (v_m_id, 'Barbell Squats', 4, '12, 10, 8, 6', 120, 'Below parallel, chest up', 'Most important exercise!', 1),
    (v_m_id, 'Leg Press', 3, '15', 90, 'Full range, don''t lock knees', NULL, 2),
    (v_m_id, 'Romanian Deadlift', 3, '12', 60, 'Slight knee bend, feel hamstring stretch', NULL, 3),
    (v_m_id, 'Overhead Press', 4, '10', 90, 'Strict form, no leg drive', NULL, 4),
    (v_m_id, 'Lateral Raises', 3, '15', 45, 'Light weight, controlled', 'Slow and steady', 5);

-- ============================================================
-- 10. INSERT DIET PLAN (for Amit)
-- ============================================================
INSERT INTO public.diet_plans (id, member_id, trainer_id, gym_id, title, is_active, notes)
VALUES (gen_random_uuid(), v_member_ids[1], v_trainer_id, v_gym_id, 'Muscle Building Diet', true, 'High protein diet for muscle gain. Target: 2500 calories/day, 150g protein')
RETURNING id INTO v_m_id;

INSERT INTO public.diet_meals (diet_plan_id, meal_type, food_item, quantity, timing, instructions, nutrition_notes, order_index)
VALUES
    (v_m_id, 'Breakfast', 'Oats with milk and banana', '1 bowl (200g)', '7:00 AM', 'Use low-fat milk, add honey for taste', 'Carbs: 45g, Protein: 15g', 1),
    (v_m_id, 'Breakfast', 'Boiled eggs (whole)', '4 eggs', '7:00 AM', '2 whole + 2 whites for lower fat option', 'Protein: 24g', 2),
    (v_m_id, 'Breakfast', 'Green tea', '1 cup', '7:30 AM', 'No sugar', 'Antioxidants', 3),
    (v_m_id, 'Lunch', 'Chicken breast (grilled)', '200g', '1:00 PM', 'Season with herbs, avoid heavy oil', 'Protein: 46g', 4),
    (v_m_id, 'Lunch', 'Brown rice', '1 cup cooked', '1:00 PM', 'Can substitute with roti (2 nos)', 'Carbs: 45g', 5),
    (v_m_id, 'Lunch', 'Mixed vegetable salad', '1 large bowl', '1:00 PM', 'Include cucumber, tomato, carrot, lettuce', 'Fiber & vitamins', 6),
    (v_m_id, 'Lunch', 'Dal (lentils)', '1 bowl', '1:00 PM', 'Any variety - moong, masoor, toor', 'Protein: 12g', 7),
    (v_m_id, 'Evening Snacks', 'Protein shake', '1 scoop (30g) with water', '5:00 PM', 'Take 30 min before workout', 'Protein: 24g', 8),
    (v_m_id, 'Evening Snacks', 'Mixed nuts (almonds, walnuts)', '30g', '5:00 PM', 'Unsalted, raw preferred', 'Healthy fats: 15g', 9),
    (v_m_id, 'Dinner', 'Paneer bhurji / Egg bhurji', '150g paneer or 3 eggs', '9:00 PM', 'Use minimal oil, lots of vegetables', 'Protein: 25g', 10),
    (v_m_id, 'Dinner', 'Multigrain roti', '2 rotis', '9:00 PM', 'Whole wheat or multigrain', 'Carbs: 30g', 11),
    (v_m_id, 'Dinner', 'Curd (low fat)', '1 bowl', '9:00 PM', 'Good for digestion, avoid at night if cold', 'Protein: 8g, Probiotics', 12);

-- ============================================================
-- 11. INSERT INACTIVITY FOLLOWUPS
-- ============================================================
INSERT INTO public.inactivity_followups (member_id, gym_id, contact_status, notes, followed_up_by)
VALUES
    (v_member_ids[5], v_gym_id, 'contacted', 'Called on phone, said will come next week', v_receptionist_id),
    (v_member_ids[6], v_gym_id, 'pending', 'Membership expired, needs renewal reminder', NULL),
    (v_member_ids[7], v_gym_id, 'contacted', 'WhatsApp message sent', v_trainer_id);

RAISE NOTICE 'Seed data inserted successfully!';
RAISE NOTICE 'Gym ID: %', v_gym_id;
RAISE NOTICE 'Members created: 10';
RAISE NOTICE 'Remember to replace placeholder UUIDs with actual auth user IDs!';

END $$;

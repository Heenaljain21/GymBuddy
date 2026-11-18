-- ============================================================
-- GYM BUDDY – Demo seed data (run AFTER schema.sql)
-- ============================================================
-- 1. In Supabase Dashboard → Authentication → Users → "Add user",
--    create these accounts (tick "Auto confirm"), with passwords of your choice:
--        admin@gymbuddy.io      owner@fitzone.in      reception@fitzone.in
--        vikram@fitzone.in      amit@gmail.com
-- 2. Run this file in the SQL Editor. It finds the users by email,
--    so there are no UUIDs to copy. It is safe to re-run: it does
--    nothing if the "fitzone-indiranagar" gym already exists.
-- ============================================================

DO $$
DECLARE
    v_admin UUID := (SELECT id FROM auth.users WHERE email = 'admin@gymbuddy.io');
    v_owner UUID := (SELECT id FROM auth.users WHERE email = 'owner@fitzone.in');
    v_desk UUID := (SELECT id FROM auth.users WHERE email = 'reception@fitzone.in');
    v_trainer UUID := (SELECT id FROM auth.users WHERE email = 'vikram@fitzone.in');
    v_member_user UUID := (SELECT id FROM auth.users WHERE email = 'amit@gmail.com');
    v_gym UUID;
    v_monthly UUID; v_quarterly UUID; v_half UUID; v_annual UUID;
    v_member UUID; v_plan UUID; v_start DATE; v_days INT; v_price NUMERIC;
    v_wp UUID; v_dp UUID;
    r RECORD;
    i INT := 0;
BEGIN
    IF v_owner IS NULL THEN
        RAISE EXCEPTION 'Create the auth users listed at the top of seed.sql first (owner@fitzone.in not found).';
    END IF;
    IF EXISTS (SELECT 1 FROM public.gyms WHERE slug = 'fitzone-indiranagar') THEN
        RAISE NOTICE 'Demo gym already seeded – nothing to do.';
        RETURN;
    END IF;

    INSERT INTO public.gyms (name, slug, tagline, owner_id, phone, email, address, city, state)
    VALUES ('FitZone Premium Gym', 'fitzone-indiranagar', 'Transform Your Physique', v_owner, '9876543210',
            'contact@fitzonegym.in', '12th Main Road, Indiranagar, Bengaluru, Karnataka 560038', 'Bengaluru', 'Karnataka')
    RETURNING id INTO v_gym;

    -- Profiles are auto-created by the auth trigger; set role, gym and name.
    INSERT INTO public.profiles (id, gym_id, role, full_name, email, phone) VALUES
        (v_owner, v_gym, 'owner', 'Rajesh Kumar', 'owner@fitzone.in', '9876543210')
    ON CONFLICT (id) DO UPDATE SET gym_id = EXCLUDED.gym_id, role = EXCLUDED.role, full_name = EXCLUDED.full_name, phone = EXCLUDED.phone;
    IF v_admin IS NOT NULL THEN
        INSERT INTO public.profiles (id, gym_id, role, full_name, email, phone) VALUES (v_admin, v_gym, 'admin', 'Platform Admin', 'admin@gymbuddy.io', '9999900000')
        ON CONFLICT (id) DO UPDATE SET gym_id = EXCLUDED.gym_id, role = EXCLUDED.role, full_name = EXCLUDED.full_name;
    END IF;
    IF v_desk IS NOT NULL THEN
        INSERT INTO public.profiles (id, gym_id, role, full_name, email, phone) VALUES (v_desk, v_gym, 'receptionist', 'Pooja Sharma', 'reception@fitzone.in', '9876543211')
        ON CONFLICT (id) DO UPDATE SET gym_id = EXCLUDED.gym_id, role = EXCLUDED.role, full_name = EXCLUDED.full_name;
    END IF;
    IF v_trainer IS NOT NULL THEN
        INSERT INTO public.profiles (id, gym_id, role, full_name, email, phone) VALUES (v_trainer, v_gym, 'trainer', 'Vikram Singh', 'vikram@fitzone.in', '9876543212')
        ON CONFLICT (id) DO UPDATE SET gym_id = EXCLUDED.gym_id, role = EXCLUDED.role, full_name = EXCLUDED.full_name;
    END IF;
    IF v_member_user IS NOT NULL THEN
        INSERT INTO public.profiles (id, gym_id, role, full_name, email, phone) VALUES (v_member_user, v_gym, 'member', 'Amit Sharma', 'amit@gmail.com', '9876500001')
        ON CONFLICT (id) DO UPDATE SET gym_id = EXCLUDED.gym_id, role = EXCLUDED.role, full_name = EXCLUDED.full_name;
    END IF;

    INSERT INTO public.membership_plans (gym_id, name, duration_days, price, description) VALUES
        (v_gym, 'Monthly Starter', 30, 1800, 'Standard 1 month gym access') RETURNING id INTO v_monthly;
    INSERT INTO public.membership_plans (gym_id, name, duration_days, price, description) VALUES
        (v_gym, 'Quarterly Fitness', 90, 4500, '3 months access with cardio') RETURNING id INTO v_quarterly;
    INSERT INTO public.membership_plans (gym_id, name, duration_days, price, description) VALUES
        (v_gym, 'Half-Yearly Transformation', 180, 8000, '6 months full access + steam') RETURNING id INTO v_half;
    INSERT INTO public.membership_plans (gym_id, name, duration_days, price, description) VALUES
        (v_gym, 'Annual Champion', 365, 14000, '12 months VIP access + PT session') RETURNING id INTO v_annual;

    -- name, phone, email, age, gender, area, plan, membership started N days ago, visit probability, last visit N days ago (NULL = never)
    FOR r IN SELECT * FROM (VALUES
        ('Amit Sharma',    '9876500001', 'amit@gmail.com',       28, 'Male',   'Indiranagar',  'quarterly', 30,  0.8, 0),
        ('Priya Patel',    '9876500002', 'priya.p@gmail.com',    26, 'Female', 'Koramangala',  'monthly',   26,  0.7, 0),
        ('Rahul Verma',    '9876500003', 'rahul.v@yahoo.com',    32, 'Male',   'HSR Layout',   'half',      168, 0.6, 1),
        ('Sneha Reddy',    '9876500004', 'sneha.r@gmail.com',    24, 'Female', 'Whitefield',   'monthly',   35,  0.4, 20),
        ('Rohan Gupta',    '9876500005', 'rohan.g@gmail.com',    30, 'Male',   'BTM Layout',   'annual',    100, 0.65, 1),
        ('Ananya Iyer',    '9876500006', 'ananya.i@outlook.com', 29, 'Female', 'Jayanagar',    'quarterly', 80,  0.5, 9),
        ('Karan Malhotra', '9876500007', 'karan.m@gmail.com',    35, 'Male',   'Indiranagar',  'monthly',   20,  0.5, 18),
        ('Arjun Nair',     '9876500009', 'arjun.n@gmail.com',    31, 'Male',   'Domlur',       'quarterly', 85,  0.55, 2),
        ('Meera Krishnan', '9876500010', 'meera.k@gmail.com',    23, 'Female', 'Ulsoor',       'monthly',   6,   0.0, NULL)
    ) AS t(full_name, phone, email, age, gender, area, plan_key, started_ago, prob, last_ago)
    LOOP
        i := i + 1;
        v_plan := CASE r.plan_key WHEN 'monthly' THEN v_monthly WHEN 'quarterly' THEN v_quarterly WHEN 'half' THEN v_half ELSE v_annual END;
        SELECT duration_days, price INTO v_days, v_price FROM public.membership_plans WHERE id = v_plan;
        v_start := CURRENT_DATE - r.started_ago;

        INSERT INTO public.members (gym_id, user_id, member_code, full_name, phone, email, age, gender, address,
                                    emergency_contact, qr_code_data, joined_date)
        VALUES (v_gym, CASE WHEN r.email = 'amit@gmail.com' THEN v_member_user END,
                'GMB-' || EXTRACT(YEAR FROM CURRENT_DATE) || '-' || LPAD(i::TEXT, 3, '0'),
                r.full_name, r.phone, r.email, r.age, r.gender, r.area || ', Bengaluru',
                '98450' || LPAD(i::TEXT, 5, '0'),
                'GMB-' || EXTRACT(YEAR FROM CURRENT_DATE) || '-' || LPAD(i::TEXT, 3, '0'),
                v_start)
        RETURNING id INTO v_member;

        INSERT INTO public.member_memberships (gym_id, member_id, plan_id, start_date, end_date, status, amount_paid)
        VALUES (v_gym, v_member, v_plan, v_start, v_start + v_days,
                CASE WHEN v_start + v_days >= CURRENT_DATE THEN 'active' ELSE 'expired' END, v_price);

        INSERT INTO public.payments (gym_id, member_id, amount, payment_date, payment_method, transaction_ref, receipt_no, remarks, recorded_by)
        VALUES (v_gym, v_member, v_price, v_start, (ARRAY['UPI', 'Cash', 'Bank Transfer'])[1 + (i % 3)],
                'UPI/' || EXTRACT(YEAR FROM CURRENT_DATE) || '/' || (10000 + i * 731),
                'REC-' || EXTRACT(YEAR FROM CURRENT_DATE) || '-' || LPAD(i::TEXT, 4, '0'), 'Seed data', v_owner);

        IF r.last_ago IS NOT NULL THEN
            INSERT INTO public.attendance (gym_id, member_id, check_in_date, check_in_time, method, recorded_by)
            SELECT v_gym, v_member, CURRENT_DATE - d,
                   make_time((ARRAY[6, 7, 7, 8, 18, 18, 19, 20])[1 + floor(random() * 8)::INT], floor(random() * 60)::INT, 0),
                   CASE WHEN random() < 0.7 THEN 'qr_code' ELSE 'manual' END, v_desk
            FROM generate_series(r.last_ago, LEAST(44, r.started_ago)) AS d
            WHERE d = r.last_ago OR random() < r.prob;
        END IF;

        IF v_trainer IS NOT NULL AND i <= 4 THEN
            INSERT INTO public.trainer_assignments (gym_id, trainer_id, member_id) VALUES (v_gym, v_trainer, v_member);
        END IF;

        IF r.email = 'amit@gmail.com' AND v_trainer IS NOT NULL THEN
            INSERT INTO public.workout_plans (gym_id, member_id, trainer_id, title, description)
            VALUES (v_gym, v_member, v_trainer, 'Muscle Hypertrophy & Strength', 'Push-Pull-Legs split focusing on progressive overload')
            RETURNING id INTO v_wp;
            INSERT INTO public.workout_exercises (plan_id, day_of_week, exercise_name, sets, reps, rest_seconds, instructions, trainer_notes, order_index) VALUES
                (v_wp, 'Monday', 'Barbell Bench Press', 4, '8-10', 90, 'Shoulder blades retracted, elbows at 45 degrees', 'Warm up with the empty bar', 1),
                (v_wp, 'Monday', 'Incline Dumbbell Press', 3, '10-12', 60, 'Full stretch at the bottom', '', 2),
                (v_wp, 'Tuesday', 'Barbell Deadlift', 4, '6-8', 120, 'Neutral spine, push through heels', 'Keep belt tight', 3),
                (v_wp, 'Tuesday', 'Lat Pulldown', 3, '10-12', 60, 'Pull to upper chest', '', 4),
                (v_wp, 'Wednesday', 'Barbell Back Squat', 4, '8-10', 120, 'Break parallel', 'Hit full depth', 5),
                (v_wp, 'Friday', 'Overhead Press', 4, '8-10', 90, 'Brace core', '', 6);

            INSERT INTO public.diet_plans (gym_id, member_id, trainer_id, title, notes)
            VALUES (v_gym, v_member, v_trainer, 'High Protein Muscle Building Diet', 'Target 140g protein daily. Drink 3.5L water minimum.')
            RETURNING id INTO v_dp;
            INSERT INTO public.diet_meals (diet_plan_id, meal_type, food_item, quantity, timing, instructions, nutrition_notes, order_index) VALUES
                (v_dp, 'Breakfast', 'Oatmeal with Whey Protein & Almonds', '60g oats + 1 scoop whey', '08:00 AM', 'Mix with skimmed milk', '32g protein', 1),
                (v_dp, 'Lunch', 'Grilled Paneer/Chicken with Brown Rice & Dal', '150g + 1 bowl each', '01:30 PM', '1 tsp olive oil', '38g protein', 2),
                (v_dp, 'Evening Snacks', 'Boiled Eggs or Sprouts + Black Coffee', '4 egg whites', '05:30 PM', 'Pre-workout', '15g protein', 3),
                (v_dp, 'Dinner', 'Tofu/Soya with Mixed Veg Salad', '150g tofu', '08:30 PM', 'Light on salt', '25g protein', 4);
        END IF;
    END LOOP;

    RAISE NOTICE 'Seeded gym % with % members.', v_gym, i;
END;
$$;

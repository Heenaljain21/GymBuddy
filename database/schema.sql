-- ============================================================
-- GYM BUDDY – Database schema (Supabase / PostgreSQL)
-- Your Gym. Your Goals. One Smart Buddy.
-- ============================================================
-- Run this whole file once in Supabase Dashboard → SQL Editor.
-- Column names match the Python services exactly; if you change
-- one side, change the other.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS public.gyms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE,
    tagline TEXT,
    owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    currency TEXT NOT NULL DEFAULT 'INR',
    inactivity_threshold_days INTEGER NOT NULL DEFAULT 14,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    gym_id UUID REFERENCES public.gyms(id) ON DELETE SET NULL,
    role TEXT NOT NULL DEFAULT 'member'
        CHECK (role IN ('admin', 'owner', 'receptionist', 'trainer', 'member')),
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_profiles_gym ON public.profiles(gym_id);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(lower(email));

CREATE TABLE IF NOT EXISTS public.membership_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_plans_gym ON public.membership_plans(gym_id);

CREATE TABLE IF NOT EXISTS public.members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,   -- set when the member has an app login
    member_code TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    age INTEGER CHECK (age IS NULL OR (age > 0 AND age < 120)),
    gender TEXT CHECK (gender IS NULL OR gender IN ('Male', 'Female', 'Other')),
    address TEXT,
    emergency_contact TEXT,
    qr_code_data TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    joined_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (gym_id, member_code),
    UNIQUE (gym_id, phone)
);
CREATE INDEX IF NOT EXISTS idx_members_gym ON public.members(gym_id);
CREATE INDEX IF NOT EXISTS idx_members_user ON public.members(user_id);

CREATE TABLE IF NOT EXISTS public.member_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES public.membership_plans(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
    amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS idx_memberships_gym ON public.member_memberships(gym_id);
CREATE INDEX IF NOT EXISTS idx_memberships_member ON public.member_memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_memberships_end ON public.member_memberships(end_date);

CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Cash', 'UPI', 'Bank Transfer')),
    transaction_ref TEXT,
    receipt_no TEXT NOT NULL UNIQUE,
    remarks TEXT,
    recorded_by UUID REFERENCES auth.users(id) DEFAULT auth.uid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_payments_gym_date ON public.payments(gym_id, payment_date);
CREATE INDEX IF NOT EXISTS idx_payments_member ON public.payments(member_id);

CREATE TABLE IF NOT EXISTS public.attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    check_in_date DATE NOT NULL DEFAULT CURRENT_DATE,
    check_in_time TIME NOT NULL DEFAULT LOCALTIME,
    method TEXT NOT NULL DEFAULT 'qr_code' CHECK (method IN ('qr_code', 'manual')),
    recorded_by UUID REFERENCES auth.users(id) DEFAULT auth.uid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (member_id, check_in_date)          -- one check-in per member per day
);
CREATE INDEX IF NOT EXISTS idx_attendance_gym_date ON public.attendance(gym_id, check_in_date);

CREATE TABLE IF NOT EXISTS public.trainer_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    trainer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    assigned_date DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (gym_id, member_id)                 -- one coach per member
);
CREATE INDEX IF NOT EXISTS idx_assign_trainer ON public.trainer_assignments(trainer_id);

CREATE TABLE IF NOT EXISTS public.workout_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    trainer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    title TEXT NOT NULL DEFAULT 'Workout plan',
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_workout ON public.workout_plans(member_id) WHERE is_active;

CREATE TABLE IF NOT EXISTS public.workout_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES public.workout_plans(id) ON DELETE CASCADE,
    day_of_week TEXT NOT NULL
        CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    exercise_name TEXT NOT NULL,
    sets INTEGER CHECK (sets IS NULL OR sets > 0),
    reps TEXT,
    rest_seconds INTEGER CHECK (rest_seconds IS NULL OR rest_seconds >= 0),
    instructions TEXT,
    trainer_notes TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_exercises_plan ON public.workout_exercises(plan_id);

CREATE TABLE IF NOT EXISTS public.diet_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    trainer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    title TEXT NOT NULL DEFAULT 'Diet plan',
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_diet ON public.diet_plans(member_id) WHERE is_active;

CREATE TABLE IF NOT EXISTS public.diet_meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diet_plan_id UUID NOT NULL REFERENCES public.diet_plans(id) ON DELETE CASCADE,
    meal_type TEXT NOT NULL CHECK (meal_type IN ('Breakfast', 'Lunch', 'Evening Snacks', 'Dinner')),
    food_item TEXT NOT NULL,
    quantity TEXT,
    timing TEXT,
    instructions TEXT,
    nutrition_notes TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_meals_plan ON public.diet_meals(diet_plan_id);

CREATE TABLE IF NOT EXISTS public.renewal_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    old_plan_id UUID REFERENCES public.membership_plans(id),
    new_plan_id UUID NOT NULL REFERENCES public.membership_plans(id),
    renewal_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0,
    new_end_date DATE NOT NULL,
    renewed_by UUID REFERENCES auth.users(id) DEFAULT auth.uid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_renewals_gym ON public.renewal_records(gym_id);

CREATE TABLE IF NOT EXISTS public.inactivity_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    contacted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    contact_date DATE NOT NULL DEFAULT CURRENT_DATE,
    channel TEXT NOT NULL DEFAULT 'whatsapp',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'contacted', 'responded', 'returned', 'lost')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_followups_member ON public.inactivity_followups(member_id);

-- ============================================================
-- updated_at triggers
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['gyms', 'profiles', 'membership_plans', 'members', 'member_memberships', 'workout_plans', 'diet_plans']
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS set_updated_at ON public.%I', t);
        EXECUTE format('CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at()', t);
    END LOOP;
END;
$$;

-- ============================================================
-- Auto-create a profile when someone signs up in Supabase Auth.
-- Every new login starts as a member with no gym. Role and gym are
-- never read from sign-up metadata (anyone holding the anon key
-- could otherwise sign up as an admin); an owner or admin sets them
-- by editing the profile row afterwards.
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role, gym_id)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data ->> 'full_name', split_part(NEW.email, '@', 1)),
        NEW.email,
        'member',
        NULL
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- RLS helper functions.
-- SECURITY DEFINER lets policies read the caller's profile without
-- re-triggering profile policies (which would recurse forever).
-- ============================================================
CREATE OR REPLACE FUNCTION public.current_role_name()
RETURNS TEXT LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid()
$$;

CREATE OR REPLACE FUNCTION public.current_gym_id()
RETURNS UUID LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT gym_id FROM public.profiles WHERE id = auth.uid()
$$;

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT COALESCE((SELECT role = 'admin' FROM public.profiles WHERE id = auth.uid()), false)
$$;

-- True when the caller works at `gym` in one of `roles` (admins always pass).
CREATE OR REPLACE FUNCTION public.has_gym_role(gym UUID, roles TEXT[])
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles p
        WHERE p.id = auth.uid()
          AND (p.role = 'admin' OR (p.gym_id = gym AND p.role = ANY(roles)))
    )
$$;

-- Member rows that belong to the signed-in member.
CREATE OR REPLACE FUNCTION public.my_member_ids()
RETURNS SETOF UUID LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT m.id FROM public.members m
    LEFT JOIN public.profiles p ON p.id = auth.uid()
    WHERE m.user_id = auth.uid()
       OR (m.gym_id = p.gym_id AND lower(m.email) = lower(p.email))
$$;

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['gyms', 'profiles', 'membership_plans', 'members', 'member_memberships', 'payments',
                             'attendance', 'trainer_assignments', 'workout_plans', 'workout_exercises', 'diet_plans',
                             'diet_meals', 'renewal_records', 'inactivity_followups']
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;
END;
$$;

-- Gyms ----------------------------------------------------------------------
CREATE POLICY gyms_read ON public.gyms FOR SELECT
    USING (public.is_admin() OR id = public.current_gym_id());
CREATE POLICY gyms_insert ON public.gyms FOR INSERT
    WITH CHECK (public.is_admin());
CREATE POLICY gyms_update ON public.gyms FOR UPDATE
    USING (public.has_gym_role(id, ARRAY['owner']));

-- Profiles ------------------------------------------------------------------
CREATE POLICY profiles_read ON public.profiles FOR SELECT
    USING (id = auth.uid() OR public.is_admin() OR gym_id = public.current_gym_id());
CREATE POLICY profiles_update_self ON public.profiles FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid() AND role = public.current_role_name() AND gym_id IS NOT DISTINCT FROM public.current_gym_id());
CREATE POLICY profiles_manage ON public.profiles FOR UPDATE
    USING (public.is_admin() OR public.has_gym_role(gym_id, ARRAY['owner']))
    WITH CHECK (public.is_admin() OR (public.has_gym_role(gym_id, ARRAY['owner']) AND role <> 'admin'));  -- owners can't mint admins

-- Membership plans ------------------------------------------------------------
CREATE POLICY plans_read ON public.membership_plans FOR SELECT
    USING (public.is_admin() OR gym_id = public.current_gym_id());
CREATE POLICY plans_write ON public.membership_plans FOR ALL
    USING (public.has_gym_role(gym_id, ARRAY['owner']))
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner']));

-- Members ---------------------------------------------------------------------
CREATE POLICY members_read ON public.members FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist', 'trainer']) OR id IN (SELECT public.my_member_ids()));
CREATE POLICY members_insert ON public.members FOR INSERT
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));
CREATE POLICY members_update ON public.members FOR UPDATE
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));

-- Memberships -------------------------------------------------------------------
CREATE POLICY memberships_read ON public.member_memberships FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist', 'trainer']) OR member_id IN (SELECT public.my_member_ids()));
CREATE POLICY memberships_write ON public.member_memberships FOR ALL
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']))
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));

-- Payments ----------------------------------------------------------------------
CREATE POLICY payments_read ON public.payments FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']) OR member_id IN (SELECT public.my_member_ids()));
CREATE POLICY payments_insert ON public.payments FOR INSERT
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));

-- Attendance --------------------------------------------------------------------
CREATE POLICY attendance_read ON public.attendance FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist', 'trainer']) OR member_id IN (SELECT public.my_member_ids()));
CREATE POLICY attendance_insert ON public.attendance FOR INSERT
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));

-- Trainer assignments -------------------------------------------------------------
CREATE POLICY assignments_read ON public.trainer_assignments FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist', 'trainer']));
CREATE POLICY assignments_write ON public.trainer_assignments FOR ALL
    USING (public.has_gym_role(gym_id, ARRAY['owner']))
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner']));

-- Workout plans & exercises ---------------------------------------------------------
CREATE POLICY workouts_read ON public.workout_plans FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist', 'trainer']) OR member_id IN (SELECT public.my_member_ids()));
CREATE POLICY workouts_write ON public.workout_plans FOR ALL
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'trainer']))
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'trainer']));

CREATE POLICY exercises_read ON public.workout_exercises FOR SELECT
    USING (EXISTS (SELECT 1 FROM public.workout_plans w WHERE w.id = plan_id));  -- inherits workout_plans RLS
CREATE POLICY exercises_write ON public.workout_exercises FOR ALL
    USING (EXISTS (SELECT 1 FROM public.workout_plans w WHERE w.id = plan_id AND public.has_gym_role(w.gym_id, ARRAY['owner', 'trainer'])))
    WITH CHECK (EXISTS (SELECT 1 FROM public.workout_plans w WHERE w.id = plan_id AND public.has_gym_role(w.gym_id, ARRAY['owner', 'trainer'])));

-- Diet plans & meals ------------------------------------------------------------------
CREATE POLICY diets_read ON public.diet_plans FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist', 'trainer']) OR member_id IN (SELECT public.my_member_ids()));
CREATE POLICY diets_write ON public.diet_plans FOR ALL
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'trainer']))
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'trainer']));

CREATE POLICY meals_read ON public.diet_meals FOR SELECT
    USING (EXISTS (SELECT 1 FROM public.diet_plans d WHERE d.id = diet_plan_id));  -- inherits diet_plans RLS
CREATE POLICY meals_write ON public.diet_meals FOR ALL
    USING (EXISTS (SELECT 1 FROM public.diet_plans d WHERE d.id = diet_plan_id AND public.has_gym_role(d.gym_id, ARRAY['owner', 'trainer'])))
    WITH CHECK (EXISTS (SELECT 1 FROM public.diet_plans d WHERE d.id = diet_plan_id AND public.has_gym_role(d.gym_id, ARRAY['owner', 'trainer'])));

-- Renewals & follow-ups ------------------------------------------------------------------
CREATE POLICY renewals_read ON public.renewal_records FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));
CREATE POLICY renewals_insert ON public.renewal_records FOR INSERT
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));

CREATE POLICY followups_read ON public.inactivity_followups FOR SELECT
    USING (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));
CREATE POLICY followups_insert ON public.inactivity_followups FOR INSERT
    WITH CHECK (public.has_gym_role(gym_id, ARRAY['owner', 'receptionist']));

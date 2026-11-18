-- ============================================================
-- GYM BUDDY – Complete Database Schema
-- Your Gym. Your Goals. One Smart Buddy.
-- ============================================================
-- Run this in your Supabase SQL Editor (Dashboard → SQL Editor)
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. GYMS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.gyms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE,
    owner_id UUID REFERENCES auth.users(id),
    logo_url TEXT,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(255),
    inactivity_threshold_days INTEGER DEFAULT 15,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_gyms_owner ON public.gyms(owner_id);
CREATE INDEX idx_gyms_slug ON public.gyms(slug);

-- ============================================================
-- 2. PROFILES TABLE (extends auth.users)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    gym_id UUID REFERENCES public.gyms(id),
    role VARCHAR(20) NOT NULL DEFAULT 'member'
        CHECK (role IN ('admin', 'owner', 'receptionist', 'trainer', 'member')),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_profiles_gym ON public.profiles(gym_id);
CREATE INDEX idx_profiles_role ON public.profiles(role);
CREATE INDEX idx_profiles_email ON public.profiles(email);

-- ============================================================
-- 3. MEMBERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    member_code VARCHAR(20) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(255),
    age INTEGER CHECK (age > 0 AND age < 120),
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    address TEXT,
    emergency_contact VARCHAR(15),
    qr_code_data TEXT UNIQUE,
    profile_photo_url TEXT,
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'expired')),
    joined_date DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(gym_id, member_code),
    UNIQUE(gym_id, phone)
);

CREATE INDEX idx_members_gym ON public.members(gym_id);
CREATE INDEX idx_members_status ON public.members(status);
CREATE INDEX idx_members_phone ON public.members(phone);
CREATE INDEX idx_members_qr ON public.members(qr_code_data);
CREATE INDEX idx_members_name ON public.members(full_name);

-- ============================================================
-- 4. MEMBERSHIP PLANS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.membership_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    name VARCHAR(100) NOT NULL,
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_plans_gym ON public.membership_plans(gym_id);

-- ============================================================
-- 5. MEMBER MEMBERSHIPS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.member_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES public.membership_plans(id),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'expired', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memberships_member ON public.member_memberships(member_id);
CREATE INDEX idx_memberships_gym ON public.member_memberships(gym_id);
CREATE INDEX idx_memberships_status ON public.member_memberships(status);
CREATE INDEX idx_memberships_end_date ON public.member_memberships(end_date);

-- ============================================================
-- 6. PAYMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    member_id UUID NOT NULL REFERENCES public.members(id),
    membership_id UUID REFERENCES public.member_memberships(id),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    payment_method VARCHAR(20) NOT NULL
        CHECK (payment_method IN ('Cash', 'UPI', 'Bank Transfer')),
    transaction_ref VARCHAR(100),
    remarks TEXT,
    payment_date DATE DEFAULT CURRENT_DATE,
    receipt_number VARCHAR(50) UNIQUE,
    recorded_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_gym ON public.payments(gym_id);
CREATE INDEX idx_payments_member ON public.payments(member_id);
CREATE INDEX idx_payments_date ON public.payments(payment_date);
CREATE INDEX idx_payments_receipt ON public.payments(receipt_number);

-- ============================================================
-- 7. ATTENDANCE TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    member_id UUID NOT NULL REFERENCES public.members(id),
    check_in_date DATE NOT NULL DEFAULT CURRENT_DATE,
    check_in_time TIME NOT NULL DEFAULT CURRENT_TIME,
    recorded_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(member_id, check_in_date)
);

CREATE INDEX idx_attendance_gym ON public.attendance(gym_id);
CREATE INDEX idx_attendance_member ON public.attendance(member_id);
CREATE INDEX idx_attendance_date ON public.attendance(check_in_date);
CREATE INDEX idx_attendance_gym_date ON public.attendance(gym_id, check_in_date);

-- ============================================================
-- 8. WORKOUT PLANS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.workout_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    trainer_id UUID REFERENCES auth.users(id),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    day_of_week VARCHAR(10) NOT NULL
        CHECK (day_of_week IN ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(member_id, day_of_week, is_active)
);

CREATE INDEX idx_workout_plans_member ON public.workout_plans(member_id);
CREATE INDEX idx_workout_plans_trainer ON public.workout_plans(trainer_id);
CREATE INDEX idx_workout_plans_gym ON public.workout_plans(gym_id);

-- ============================================================
-- 9. WORKOUT EXERCISES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.workout_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_plan_id UUID NOT NULL REFERENCES public.workout_plans(id) ON DELETE CASCADE,
    exercise_name VARCHAR(255) NOT NULL,
    sets INTEGER CHECK (sets > 0),
    reps VARCHAR(50),
    rest_seconds INTEGER CHECK (rest_seconds >= 0),
    instructions TEXT,
    trainer_notes TEXT,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exercises_plan ON public.workout_exercises(workout_plan_id);

-- ============================================================
-- 10. DIET PLANS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.diet_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    trainer_id UUID REFERENCES auth.users(id),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    title VARCHAR(255) DEFAULT 'Diet Plan',
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_diet_plans_member ON public.diet_plans(member_id);
CREATE INDEX idx_diet_plans_trainer ON public.diet_plans(trainer_id);
CREATE INDEX idx_diet_plans_gym ON public.diet_plans(gym_id);

-- ============================================================
-- 11. DIET MEALS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.diet_meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diet_plan_id UUID NOT NULL REFERENCES public.diet_plans(id) ON DELETE CASCADE,
    meal_type VARCHAR(20) NOT NULL
        CHECK (meal_type IN ('Breakfast', 'Lunch', 'Evening Snacks', 'Dinner')),
    food_item VARCHAR(255) NOT NULL,
    quantity VARCHAR(100),
    timing VARCHAR(50),
    instructions TEXT,
    nutrition_notes TEXT,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_diet_meals_plan ON public.diet_meals(diet_plan_id);

-- ============================================================
-- 12. TRAINER ASSIGNMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.trainer_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    trainer_id UUID NOT NULL REFERENCES auth.users(id),
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    assigned_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(gym_id, trainer_id, member_id)
);

CREATE INDEX idx_trainer_assign_gym ON public.trainer_assignments(gym_id);
CREATE INDEX idx_trainer_assign_trainer ON public.trainer_assignments(trainer_id);
CREATE INDEX idx_trainer_assign_member ON public.trainer_assignments(member_id);

-- ============================================================
-- 13. RENEWAL RECORDS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.renewal_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    old_membership_id UUID REFERENCES public.member_memberships(id),
    new_membership_id UUID REFERENCES public.member_memberships(id),
    old_end_date DATE,
    new_end_date DATE,
    payment_id UUID REFERENCES public.payments(id),
    renewed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_renewals_member ON public.renewal_records(member_id);
CREATE INDEX idx_renewals_gym ON public.renewal_records(gym_id);

-- ============================================================
-- 14. INACTIVITY FOLLOWUPS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.inactivity_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    gym_id UUID NOT NULL REFERENCES public.gyms(id),
    contact_status VARCHAR(50) DEFAULT 'pending'
        CHECK (contact_status IN ('pending', 'contacted', 'responded', 'returned', 'lost')),
    notes TEXT,
    followed_up_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_followups_member ON public.inactivity_followups(member_id);
CREATE INDEX idx_followups_gym ON public.inactivity_followups(gym_id);
CREATE INDEX idx_followups_status ON public.inactivity_followups(contact_status);

-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER set_updated_at_gyms
    BEFORE UPDATE ON public.gyms
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_updated_at_profiles
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_updated_at_members
    BEFORE UPDATE ON public.members
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_updated_at_membership_plans
    BEFORE UPDATE ON public.membership_plans
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_updated_at_member_memberships
    BEFORE UPDATE ON public.member_memberships
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_updated_at_workout_plans
    BEFORE UPDATE ON public.workout_plans
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_updated_at_diet_plans
    BEFORE UPDATE ON public.diet_plans
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'role', 'member')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Generate unique member code for a gym
CREATE OR REPLACE FUNCTION public.generate_member_code(p_gym_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    v_prefix VARCHAR;
    v_count INTEGER;
    v_code VARCHAR;
BEGIN
    SELECT UPPER(LEFT(REPLACE(name, ' ', ''), 3)) INTO v_prefix FROM public.gyms WHERE id = p_gym_id;
    IF v_prefix IS NULL THEN v_prefix := 'GYM'; END IF;
    
    SELECT COUNT(*) + 1 INTO v_count FROM public.members WHERE gym_id = p_gym_id;
    v_code := v_prefix || '-' || LPAD(v_count::TEXT, 4, '0');
    
    -- Ensure uniqueness
    WHILE EXISTS (SELECT 1 FROM public.members WHERE gym_id = p_gym_id AND member_code = v_code) LOOP
        v_count := v_count + 1;
        v_code := v_prefix || '-' || LPAD(v_count::TEXT, 4, '0');
    END LOOP;
    
    RETURN v_code;
END;
$$ LANGUAGE plpgsql;

-- Generate unique receipt number
CREATE OR REPLACE FUNCTION public.generate_receipt_number(p_gym_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    v_prefix VARCHAR;
    v_count INTEGER;
    v_receipt VARCHAR;
BEGIN
    SELECT UPPER(LEFT(REPLACE(name, ' ', ''), 3)) INTO v_prefix FROM public.gyms WHERE id = p_gym_id;
    IF v_prefix IS NULL THEN v_prefix := 'GYM'; END IF;
    
    SELECT COUNT(*) + 1 INTO v_count FROM public.payments WHERE gym_id = p_gym_id;
    v_receipt := 'RCP-' || v_prefix || '-' || LPAD(v_count::TEXT, 5, '0');
    
    WHILE EXISTS (SELECT 1 FROM public.payments WHERE receipt_number = v_receipt) LOOP
        v_count := v_count + 1;
        v_receipt := 'RCP-' || v_prefix || '-' || LPAD(v_count::TEXT, 5, '0');
    END LOOP;
    
    RETURN v_receipt;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE public.gyms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.membership_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.member_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.diet_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.diet_meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trainer_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.renewal_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inactivity_followups ENABLE ROW LEVEL SECURITY;

-- ---- GYMS ----
-- Admins can see all gyms
CREATE POLICY "Admins can view all gyms" ON public.gyms
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- Owners can view their own gym
CREATE POLICY "Owners can view own gym" ON public.gyms
    FOR SELECT USING (owner_id = auth.uid());

-- Staff and members can view their gym
CREATE POLICY "Staff can view their gym" ON public.gyms
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND gym_id = gyms.id)
    );

-- Admins can insert gyms
CREATE POLICY "Admins can create gyms" ON public.gyms
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- Owners can update their own gym
CREATE POLICY "Owners can update own gym" ON public.gyms
    FOR UPDATE USING (owner_id = auth.uid());

-- ---- PROFILES ----
-- Users can view own profile
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (id = auth.uid());

-- Users in same gym can view profiles
CREATE POLICY "Same gym can view profiles" ON public.profiles
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
    );

-- Admins can view all profiles
CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles p WHERE p.id = auth.uid() AND p.role = 'admin')
    );

-- Users can update own profile
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (id = auth.uid());

-- Admins and owners can update profiles in their gym
CREATE POLICY "Owners can update gym profiles" ON public.profiles
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
            AND p.role IN ('admin', 'owner')
            AND (p.gym_id = profiles.gym_id OR p.role = 'admin')
        )
    );

-- Allow insert for new user trigger
CREATE POLICY "Allow profile creation" ON public.profiles
    FOR INSERT WITH CHECK (true);

-- ---- MEMBERS ----
-- Gym staff can view their gym's members
CREATE POLICY "Gym staff view members" ON public.members
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- Owners and receptionists can insert members
CREATE POLICY "Staff can add members" ON public.members
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'admin')
        )
    );

-- Staff can update members in their gym
CREATE POLICY "Staff can update members" ON public.members
    FOR UPDATE USING (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'trainer', 'admin')
        )
    );

-- Allow public member registration (for online joining)
CREATE POLICY "Public member registration" ON public.members
    FOR INSERT WITH CHECK (true);

-- ---- MEMBERSHIP PLANS ----
-- Anyone can view active plans (for registration page)
CREATE POLICY "Anyone can view plans" ON public.membership_plans
    FOR SELECT USING (true);

-- Owners can manage plans
CREATE POLICY "Owners can manage plans" ON public.membership_plans
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY "Owners can update plans" ON public.membership_plans
    FOR UPDATE USING (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- ---- MEMBER MEMBERSHIPS ----
CREATE POLICY "Gym staff view memberships" ON public.member_memberships
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Staff can create memberships" ON public.member_memberships
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Staff can update memberships" ON public.member_memberships
    FOR UPDATE USING (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'admin')
        )
    );

-- ---- PAYMENTS ----
CREATE POLICY "Gym staff view payments" ON public.payments
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Staff can record payments" ON public.payments
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'admin')
        )
    );

-- ---- ATTENDANCE ----
CREATE POLICY "Gym staff view attendance" ON public.attendance
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Staff can record attendance" ON public.attendance
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'admin')
        )
        OR true  -- Allow self check-in for members
    );

-- ---- WORKOUT PLANS ----
CREATE POLICY "View workout plans" ON public.workout_plans
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Trainers can manage workouts" ON public.workout_plans
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'trainer', 'admin')
        )
    );

CREATE POLICY "Trainers can update workouts" ON public.workout_plans
    FOR UPDATE USING (
        trainer_id = auth.uid()
        OR gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY "Trainers can delete workouts" ON public.workout_plans
    FOR DELETE USING (
        trainer_id = auth.uid()
        OR gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- ---- WORKOUT EXERCISES ----
CREATE POLICY "View exercises" ON public.workout_exercises
    FOR SELECT USING (
        workout_plan_id IN (
            SELECT id FROM public.workout_plans
            WHERE gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        )
    );

CREATE POLICY "Manage exercises" ON public.workout_exercises
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Update exercises" ON public.workout_exercises
    FOR UPDATE USING (true);

CREATE POLICY "Delete exercises" ON public.workout_exercises
    FOR DELETE USING (true);

-- ---- DIET PLANS ----
CREATE POLICY "View diet plans" ON public.diet_plans
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Trainers can manage diets" ON public.diet_plans
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'trainer', 'admin')
        )
    );

CREATE POLICY "Trainers can update diets" ON public.diet_plans
    FOR UPDATE USING (
        trainer_id = auth.uid()
        OR gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY "Trainers can delete diets" ON public.diet_plans
    FOR DELETE USING (
        trainer_id = auth.uid()
        OR gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- ---- DIET MEALS ----
CREATE POLICY "View diet meals" ON public.diet_meals
    FOR SELECT USING (
        diet_plan_id IN (
            SELECT id FROM public.diet_plans
            WHERE gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        )
    );

CREATE POLICY "Manage diet meals" ON public.diet_meals
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Update diet meals" ON public.diet_meals
    FOR UPDATE USING (true);

CREATE POLICY "Delete diet meals" ON public.diet_meals
    FOR DELETE USING (true);

-- ---- TRAINER ASSIGNMENTS ----
CREATE POLICY "View trainer assignments" ON public.trainer_assignments
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Manage trainer assignments" ON public.trainer_assignments
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY "Update trainer assignments" ON public.trainer_assignments
    FOR UPDATE USING (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY "Delete trainer assignments" ON public.trainer_assignments
    FOR DELETE USING (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- ---- RENEWAL RECORDS ----
CREATE POLICY "View renewals" ON public.renewal_records
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Record renewals" ON public.renewal_records
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'admin')
        )
    );

-- ---- INACTIVITY FOLLOWUPS ----
CREATE POLICY "View followups" ON public.inactivity_followups
    FOR SELECT USING (
        gym_id IN (SELECT gym_id FROM public.profiles WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Manage followups" ON public.inactivity_followups
    FOR INSERT WITH CHECK (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'trainer', 'admin')
        )
    );

CREATE POLICY "Update followups" ON public.inactivity_followups
    FOR UPDATE USING (
        gym_id IN (
            SELECT gym_id FROM public.profiles
            WHERE id = auth.uid() AND role IN ('owner', 'receptionist', 'trainer', 'admin')
        )
    );

-- ============================================================
-- VIEWS (for convenience)
-- ============================================================

-- Active memberships with plan details
CREATE OR REPLACE VIEW public.v_active_memberships AS
SELECT
    mm.id,
    mm.member_id,
    mm.plan_id,
    mm.gym_id,
    mm.start_date,
    mm.end_date,
    mm.status,
    mp.name AS plan_name,
    mp.duration_days,
    mp.price AS plan_price,
    m.full_name AS member_name,
    m.phone AS member_phone,
    m.member_code,
    (mm.end_date - CURRENT_DATE) AS days_remaining
FROM public.member_memberships mm
JOIN public.membership_plans mp ON mm.plan_id = mp.id
JOIN public.members m ON mm.member_id = m.id;

-- Member attendance summary
CREATE OR REPLACE VIEW public.v_member_attendance_summary AS
SELECT
    m.id AS member_id,
    m.gym_id,
    m.full_name,
    m.phone,
    m.status,
    m.member_code,
    MAX(a.check_in_date) AS last_attendance_date,
    COUNT(a.id) AS total_attendance,
    CASE
        WHEN MAX(a.check_in_date) IS NULL THEN -1
        ELSE CURRENT_DATE - MAX(a.check_in_date)
    END AS days_since_last_visit
FROM public.members m
LEFT JOIN public.attendance a ON m.id = a.member_id
GROUP BY m.id, m.gym_id, m.full_name, m.phone, m.status, m.member_code;

-- ============================================================
-- DONE
-- ============================================================

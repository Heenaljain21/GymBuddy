-- ============================================================
-- GYM BUDDY – Member self sign-up
-- ============================================================
-- Members create their own login from the app's "Create account"
-- tab. Once Supabase has CONFIRMED that they own the email address,
-- the login is linked to the member record the front desk created
-- with that email. Nothing is linked for an unconfirmed email, an
-- email no gym has registered, or an email registered at more than
-- one gym. Sign-up can only ever produce a member login; staff roles
-- are still set by an owner or admin.
--
-- Safe to re-run. Included in schema.sql for new projects; run this
-- file on its own to add the feature to an existing project.
--
-- REQUIRES Authentication → Sign In / Providers → Email →
-- "Confirm email" to stay ON. Without it, anyone could sign up with
-- a member's email and see that member's data.
-- ============================================================

-- Link one confirmed login to the member record with the same email.
CREATE OR REPLACE FUNCTION public.link_member_login(p_user UUID, p_email TEXT)
RETURNS VOID LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
    v_member UUID;
    v_gym UUID;
    v_matches INT;
BEGIN
    IF p_user IS NULL OR coalesce(trim(p_email), '') = '' THEN
        RETURN;
    END IF;

    SELECT count(*) INTO v_matches
    FROM public.members WHERE lower(email) = lower(trim(p_email)) AND user_id IS NULL;
    IF v_matches <> 1 THEN
        RETURN;  -- not registered yet, already linked, or ambiguous across gyms
    END IF;

    SELECT id, gym_id INTO v_member, v_gym
    FROM public.members WHERE lower(email) = lower(trim(p_email)) AND user_id IS NULL;

    -- Only plain member logins; never touch staff or a member of another gym.
    UPDATE public.profiles SET gym_id = v_gym
    WHERE id = p_user AND role = 'member' AND (gym_id IS NULL OR gym_id = v_gym);
    IF FOUND THEN
        UPDATE public.members SET user_id = p_user WHERE id = v_member;
    END IF;
END;
$$;

-- Internal only: if the API could call it, anyone could link a login to someone else's record.
REVOKE ALL ON FUNCTION public.link_member_login(UUID, TEXT) FROM PUBLIC, anon, authenticated;

-- New logins start as members with no gym; link right away if Supabase
-- already confirmed the email (e.g. "Auto Confirm User" in the dashboard).
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role, gym_id)
    VALUES (
        NEW.id,
        COALESCE(NULLIF(trim(NEW.raw_user_meta_data ->> 'full_name'), ''), split_part(NEW.email, '@', 1)),
        NEW.email,
        'member',
        NULL
    )
    ON CONFLICT (id) DO NOTHING;
    IF NEW.email_confirmed_at IS NOT NULL THEN
        PERFORM public.link_member_login(NEW.id, NEW.email);
    END IF;
    RETURN NEW;
END;
$$;

-- When a member clicks the confirmation link.
CREATE OR REPLACE FUNCTION public.handle_user_confirmed()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF NEW.email_confirmed_at IS NOT NULL AND OLD.email_confirmed_at IS NULL THEN
        PERFORM public.link_member_login(NEW.id, NEW.email);
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_confirmed ON auth.users;
CREATE TRIGGER on_auth_user_confirmed
    AFTER UPDATE OF email_confirmed_at ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_user_confirmed();

-- When the front desk registers (or fixes the email of) a member who already has a confirmed login.
CREATE OR REPLACE FUNCTION public.handle_member_email()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE v_user UUID;
BEGIN
    IF NEW.user_id IS NULL AND coalesce(trim(NEW.email), '') <> '' THEN
        SELECT id INTO v_user FROM auth.users
        WHERE lower(email) = lower(trim(NEW.email)) AND email_confirmed_at IS NOT NULL
        LIMIT 1;
        IF v_user IS NOT NULL THEN
            PERFORM public.link_member_login(v_user, NEW.email);
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS on_member_email_set ON public.members;
CREATE TRIGGER on_member_email_set
    AFTER INSERT OR UPDATE OF email ON public.members
    FOR EACH ROW EXECUTE FUNCTION public.handle_member_email();

REVOKE ALL ON FUNCTION public.handle_user_confirmed() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.handle_member_email() FROM PUBLIC, anon, authenticated;

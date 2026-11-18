"""SCREEN 4 – WORKOUT PLAN

Weekly training schedules, day-by-day exercise routines, sets, reps, and trainer notes.
- Members: View personal assigned training regime.
- Trainers & Owners: Design, assign, and update workouts for members.
"""

from __future__ import annotations
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state
from utils.permissions import require_auth
from services.workout_service import get_member_workout, save_workout_plan
from services.member_service import get_members
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.notifications import show_success, show_error, show_info


def load_css() -> None:
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


init_session_state()
load_css()
require_auth()
render_sidebar()

gym_id = st.session_state.get("gym_id", "00000000-0000-0000-0000-000000000001")
user_role = (st.session_state.get("user_role") or "member").lower()
profile = st.session_state.get("profile") or {}
user = st.session_state.get("user") or {}
trainer_id = profile.get("id") or user.get("id", "33333333-3333-3333-3333-333333333333")

render_navbar("Workout Routine", "Custom Training Schedules & Exercise Guides")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ==========================================
# 1. MEMBER ROLE VIEW
# ==========================================
if user_role == "member":
    all_members = get_members(gym_id)
    email = user.get("email", "")
    member = next((m for m in all_members if m.get("email") == email or m.get("phone") == user.get("phone")), None)
    if not member and all_members:
        member = all_members[0]

    if not member:
        st.info("No workout plan assigned yet.")
        st.stop()

    plan = get_member_workout(member["id"])

    if not plan:
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.7); border: 1px dashed rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 3rem; text-align: center; color: #94A3B8;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🏋️</div>
                <h3 style="color: #F8FAFC;">No Workout Routine Assigned</h3>
                <p>Your fitness coach has not assigned a personalized workout plan yet. Reach out to your trainer at the gym!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.35); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.8rem; color: #06D6C9; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">ACTIVE TRAINING REGIME</div>
                        <h2 style="color: #F8FAFC; margin: 0.25rem 0 0.5rem 0;">{plan.get('title')}</h2>
                        <div style="font-size: 0.88rem; color: #94A3B8;">{plan.get('description')}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 0.8rem; color: #94A3B8;">Coach:</span>
                        <div style="font-weight: 700; color: #A78BFA; font-size: 1.05rem;">🏋️ {plan.get('trainer_name')}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        schedule = plan.get("schedule", {})
        tabs = st.tabs(DAYS)

        for i, day in enumerate(DAYS):
            with tabs[i]:
                day_exercises = schedule.get(day, [])
                if not day_exercises:
                    st.markdown(
                        f"""
                        <div style="background: rgba(23, 29, 48, 0.4); border-radius: 12px; padding: 2rem; text-align: center; color: #64748B;">
                            <div>😴 Active Recovery / Rest Day</div>
                            <div style="font-size: 0.8rem; margin-top: 4px;">Hydrate, eat well, and sleep 7-8 hours.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    for ex in day_exercises:
                        st.markdown(
                            f"""
                            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.15); border-left: 4px solid #8B5CF6; border-radius: 12px; padding: 1.25rem; margin-bottom: 0.85rem;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h4 style="color: #F8FAFC; margin: 0; font-size: 1.1rem;">{ex.get('exercise_name')}</h4>
                                    <div style="display: flex; gap: 0.5rem;">
                                        <span style="background: rgba(139, 92, 246, 0.2); color: #A78BFA; border: 1px solid #8B5CF6; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 700;">
                                            {ex.get('sets')} Sets × {ex.get('reps')} Reps
                                        </span>
                                        <span style="background: rgba(6, 214, 201, 0.15); color: #06D6C9; border: 1px solid #06D6C9; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 700;">
                                            ⏱️ {ex.get('rest_seconds')}s Rest
                                        </span>
                                    </div>
                                </div>
                                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.5rem;">
                                    💡 <b>Form Instructions:</b> {ex.get('instructions') or 'Standard range of motion.'}
                                </div>
                                {f"<div style='font-size: 0.82rem; color: #F59E0B; margin-top: 0.25rem;'>📝 <b>Coach Tip:</b> {ex.get('trainer_notes')}</div>" if ex.get('trainer_notes') else ""}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

# ==========================================
# 2. TRAINER & OWNER VIEW (CREATOR / EDITOR)
# ==========================================
else:
    all_m = get_members(gym_id)
    if not all_m:
        st.warning("No members registered yet.")
        st.stop()

    member_options = {f"{m['full_name']} ({m.get('member_code', '-')})": m for m in all_m}
    sel_label = st.selectbox("Select Athlete / Member", options=list(member_options.keys()))
    sel_member = member_options[sel_label]
    sel_mid = sel_member["id"]

    existing_plan = get_member_workout(sel_mid)

    st.markdown("---")
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        plan_title = st.text_input("Routine Title", value=existing_plan.get("title", "Strength & Conditioning Split") if existing_plan else "Strength & Conditioning Split")
    with col_t2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.markdown(f"**Member:** {sel_member['full_name']} (`{sel_member.get('member_code')}`)")

    plan_desc = st.text_area("Routine Goals & Overview", value=existing_plan.get("description", "Focus on compound movements and progressive overload.") if existing_plan else "Focus on compound movements and progressive overload.")

    st.markdown("#### Weekly Exercise Schedule")
    tab_list = st.tabs(DAYS)

    # Manage exercises state per member in session state
    state_key = f"workout_builder_{sel_mid}"
    if state_key not in st.session_state:
        if existing_plan and existing_plan.get("exercises"):
            st.session_state[state_key] = existing_plan["exercises"]
        else:
            # Default starter template
            st.session_state[state_key] = [
                {"day_of_week": "Monday", "exercise_name": "Flat Barbell Bench Press", "sets": 4, "reps": "8-10", "rest_seconds": 90, "instructions": "Tuck elbows, touch chest", "trainer_notes": "Warm up rotator cuffs"},
                {"day_of_week": "Monday", "exercise_name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12", "rest_seconds": 60, "instructions": "Full stretch at bottom", "trainer_notes": ""},
                {"day_of_week": "Tuesday", "exercise_name": "Conventional Deadlifts", "sets": 4, "reps": "6-8", "rest_seconds": 120, "instructions": "Keep spine neutral", "trainer_notes": "Wear lifting belt"},
                {"day_of_week": "Wednesday", "exercise_name": "Barbell Squats", "sets": 4, "reps": "8-10", "rest_seconds": 120, "instructions": "Break parallel, drive with quads", "trainer_notes": ""},
            ]

    exercises = st.session_state[state_key]

    for i, day in enumerate(DAYS):
        with tab_list[i]:
            day_exs = [e for e in exercises if e.get("day_of_week") == day]
            if day_exs:
                for idx, ex in enumerate(day_exs):
                    col_e1, col_e2, col_e3, col_e4 = st.columns([3, 1, 1, 1])
                    with col_e1:
                        st.markdown(f"**{ex.get('exercise_name')}** ({ex.get('sets')} sets × {ex.get('reps')} reps, {ex.get('rest_seconds')}s rest)")
                        st.caption(f"{ex.get('instructions') or 'No instructions'}")
                    with col_e4:
                        if st.button("🗑️ Remove", key=f"del_{day}_{idx}"):
                            exercises.remove(ex)
                            st.rerun()
            else:
                st.caption("No exercises scheduled for this day yet.")

            with st.expander(f"➕ Add Exercise for {day}"):
                with st.form(f"add_ex_form_{day}"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        new_name = st.text_input("Exercise Name", placeholder="e.g. Lat Pulldowns")
                    with c2:
                        new_sets = st.number_input("Sets", min_value=1, max_value=10, value=3)
                        new_reps = st.text_input("Reps", value="10-12")
                    with c3:
                        new_rest = st.number_input("Rest (secs)", min_value=15, max_value=300, value=60)
                    new_instr = st.text_input("Form Instructions", placeholder="e.g. Squeeze back at full contraction")
                    new_notes = st.text_input("Trainer Tip / Weight Target", placeholder="e.g. Aim for 50kg")
                    
                    if st.form_submit_button(f"Add to {day}"):
                        if new_name:
                            exercises.append({
                                "day_of_week": day,
                                "exercise_name": new_name,
                                "sets": new_sets,
                                "reps": new_reps,
                                "rest_seconds": new_rest,
                                "instructions": new_instr,
                                "trainer_notes": new_notes,
                            })
                            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if st.button("💾 Save & Assign Complete Routine to Member", use_container_width=True):
        with st.spinner("Saving workout regime..."):
            ok, err = save_workout_plan(
                gym_id=gym_id,
                member_id=sel_mid,
                trainer_id=trainer_id,
                title=plan_title,
                description=plan_desc,
                exercises=exercises,
            )
            if ok:
                show_success(f"Workout plan saved and published to {sel_member['full_name']}!")
                st.rerun()
            else:
                show_error(err or "Failed to save workout.")

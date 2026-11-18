"""SCREEN 4 – Weekly workout plans.

Members see their week (starting from today). Trainers and owners edit the
whole week in one spreadsheet-style table, or start from a template.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import ctx, page_header, html_block, esc, empty_state, flash, expiry_text
from services.workout_service import get_member_workout, save_workout_plan
from services.member_service import get_members, get_member, get_trainer_member_ids
from utils.date_utils import get_ist_today

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
COLUMNS = ["day_of_week", "exercise_name", "sets", "reps", "rest_seconds", "instructions", "trainer_notes"]

TEMPLATES = {
    "Push / Pull / Legs": [
        ("Monday", "Barbell Bench Press", 4, "8-10", 90, "Shoulder blades retracted", ""),
        ("Monday", "Overhead Press", 3, "8-10", 90, "Brace core, no back arch", ""),
        ("Monday", "Triceps Rope Pushdown", 3, "12-15", 45, "Elbows pinned", ""),
        ("Tuesday", "Deadlift", 4, "5-6", 150, "Neutral spine, push through heels", "Use a belt for top sets"),
        ("Tuesday", "Lat Pulldown", 3, "10-12", 60, "Pull to upper chest", ""),
        ("Tuesday", "Barbell Curl", 3, "10-12", 45, "No swinging", ""),
        ("Wednesday", "Back Squat", 4, "8-10", 120, "Break parallel", ""),
        ("Wednesday", "Romanian Deadlift", 3, "10", 90, "Hinge at hips, soft knees", ""),
        ("Wednesday", "Standing Calf Raise", 4, "15", 45, "Full stretch at bottom", ""),
        ("Thursday", "Incline Dumbbell Press", 4, "10", 75, "", ""),
        ("Friday", "Barbell Row", 4, "8-10", 90, "Pull to belly button", ""),
        ("Saturday", "Leg Press", 4, "12", 90, "", ""),
    ],
    "Full body · 3 days": [
        ("Monday", "Goblet Squat", 3, "12", 60, "Chest up", ""),
        ("Monday", "Push-ups", 3, "AMRAP", 60, "Body in a straight line", ""),
        ("Monday", "Dumbbell Row", 3, "12 each", 60, "", ""),
        ("Wednesday", "Romanian Deadlift", 3, "10", 75, "", ""),
        ("Wednesday", "Dumbbell Shoulder Press", 3, "10", 60, "", ""),
        ("Wednesday", "Plank", 3, "45s", 45, "Squeeze glutes", ""),
        ("Friday", "Walking Lunges", 3, "12 each", 60, "", ""),
        ("Friday", "Lat Pulldown", 3, "12", 60, "", ""),
        ("Friday", "Treadmill Incline Walk", 1, "20 min", 0, "Brisk pace", ""),
    ],
    "Fat loss · conditioning": [
        ("Monday", "Kettlebell Swings", 4, "20", 45, "Hips drive the bell", ""),
        ("Monday", "Rowing Machine", 1, "10 min", 0, "Steady pace", ""),
        ("Tuesday", "Treadmill Intervals", 8, "30s sprint / 60s walk", 0, "", ""),
        ("Thursday", "Circuit: Squat, Push-up, Row", 4, "12 each", 60, "Minimal rest between moves", ""),
        ("Saturday", "Cycling", 1, "30 min", 0, "Zone 2 heart rate", ""),
    ],
}

c = ctx()
today_name = get_ist_today().strftime("%A")


def exercise_card(ex: dict) -> str:
    note = f'<div class="gb-item-note">📝 Coach: {esc(ex.get("trainer_notes"))}</div>' if ex.get("trainer_notes") else ""
    rest = f" · rest {esc(ex.get('rest_seconds'))}s" if ex.get("rest_seconds") else ""
    return f"""
    <div class="gb-item">
      <div class="gb-item-head"><div class="gb-item-title">{esc(ex.get('exercise_name'))}</div>
      <span class="gb-badge brand">{esc(ex.get('sets'))} × {esc(ex.get('reps'))}{rest}</span></div>
      {f'<div class="gb-item-body">💡 {esc(ex.get("instructions"))}</div>' if ex.get("instructions") else ''}
      {note}
    </div>"""


# ===========================================================================
# Member view
# ===========================================================================
if c.role == "member":
    page_header("My workouts", "Your weekly training plan from your coach.", eyebrow="Training")
    member = get_member(c.gym_id, c.member_id) if c.member_id else None
    plan = get_member_workout(member["id"]) if member else None
    if not plan:
        empty_state("No workout plan assigned yet", "Your trainer will set one up — ask at the desk if you're waiting.", "🏋️")
        st.stop()

    html_block(
        f"""<div class="gb-hero"><div class="gb-eyebrow">Coach · {esc(plan.get('trainer_name'))}</div>
        <h2>{esc(plan.get('title'))}</h2><p>{esc(plan.get('description') or '')}</p></div>"""
    )
    start = DAYS.index(today_name)
    ordered = DAYS[start:] + DAYS[:start]
    schedule = plan.get("schedule", {})
    tabs = st.tabs([("Today · " + d[:3]) if d == today_name else d[:3] for d in ordered])
    for tab, day in zip(tabs, ordered):
        with tab:
            exs = schedule.get(day, [])
            if not exs:
                empty_state("Rest & recovery", "Hydrate, stretch, and get 7–8 hours of sleep.", "😴")
            else:
                total_sets = sum(int(e.get("sets") or 0) for e in exs)
                st.caption(f"{day} · {len(exs)} exercises · {total_sets} working sets")
                html_block("".join(exercise_card(e) for e in exs))
    st.stop()

# ===========================================================================
# Coach view (trainer / owner / admin)
# ===========================================================================
if not c.can_coach:
    empty_state("You don't have access to this page", icon="🔒")
    st.stop()

page_header("Workout plans", "Build or edit a member's weekly routine.", eyebrow="Coaching")

members = get_members(c.gym_id, active_only=True)
if c.role == "trainer":
    mine = get_trainer_member_ids(c.gym_id, c.user_id)
    members = [m for m in members if m["id"] in mine]
if not members:
    empty_state("No athletes assigned to you yet", "Ask the gym owner to assign members to you.", "👥")
    st.stop()

by_id = {m["id"]: m for m in members}
ids = list(by_id)
pre = st.session_state.get("coach_member_id")
mid = st.selectbox(
    "Athlete", ids, index=ids.index(pre) if pre in ids else 0,
    format_func=lambda i: f"{by_id[i]['full_name']} · {by_id[i]['member_code']}" + ("" if get_member_workout(i) else "  (no plan yet)"),
)
st.session_state["coach_member_id"] = mid
member = by_id[mid]
existing = get_member_workout(mid)
st.caption(f"{member['plan_name']} · {expiry_text(member.get('expiry_date'))}" + (f" · current plan by {existing.get('trainer_name')}" if existing else ""))

state_key = f"wo_rows_{mid}"
if state_key not in st.session_state:
    rows = existing.get("exercises", []) if existing else []
    st.session_state[state_key] = [{k: r.get(k) for k in COLUMNS} for r in rows]

t1, t2, t3 = st.columns([2, 1, 1], vertical_alignment="bottom")
template = t1.selectbox("Start from a template", ["—"] + list(TEMPLATES), help="Replaces the table below; nothing is saved until you click Save.")
if t2.button("Apply template", width="stretch", disabled=template == "—"):
    st.session_state[state_key] = [dict(zip(COLUMNS, row)) for row in TEMPLATES[template]]
    st.session_state.pop(f"wo_editor_{mid}", None)
    st.rerun()
if t3.button("Clear all", width="stretch"):
    st.session_state[state_key] = []
    st.session_state.pop(f"wo_editor_{mid}", None)
    st.rerun()

with st.form(f"wo_form_{mid}", border=True):
    a, b = st.columns([1.2, 2])
    title = a.text_input("Plan title", value=(existing or {}).get("title") or "Strength & Conditioning")
    desc = b.text_input("Goal / overview", value=(existing or {}).get("description") or "Compound lifts with progressive overload.")
    df = pd.DataFrame(st.session_state[state_key], columns=COLUMNS)
    if not df.empty:
        df["day_of_week"] = pd.Categorical(df["day_of_week"], categories=DAYS, ordered=True)
        df = df.sort_values("day_of_week", kind="stable").reset_index(drop=True)
        df["day_of_week"] = df["day_of_week"].astype(str)
    edited = st.data_editor(
        df, key=f"wo_editor_{mid}", num_rows="dynamic", hide_index=True, width="stretch",
        column_config={
            "day_of_week": st.column_config.SelectboxColumn("Day", options=DAYS, required=True, default="Monday", width="small"),
            "exercise_name": st.column_config.TextColumn("Exercise", required=True, width="medium"),
            "sets": st.column_config.NumberColumn("Sets", min_value=1, max_value=20, default=3, width="small"),
            "reps": st.column_config.TextColumn("Reps", default="10-12", width="small"),
            "rest_seconds": st.column_config.NumberColumn("Rest (s)", min_value=0, max_value=600, default=60, step=15, width="small"),
            "instructions": st.column_config.TextColumn("Form cues", width="large"),
            "trainer_notes": st.column_config.TextColumn("Coach notes", width="medium"),
        },
    )
    st.caption("Add rows with ➕ at the bottom of the table, delete by selecting rows and pressing Delete.")
    saved = st.form_submit_button("Save & publish to member", type="primary", width="stretch", icon=":material/publish:")

if saved:
    rows = [r for r in edited.to_dict("records") if str(r.get("exercise_name") or "").strip()]
    for r in rows:
        r["sets"] = int(r.get("sets") or 3)
        r["rest_seconds"] = int(r.get("rest_seconds") or 0)
        r["reps"] = str(r.get("reps") or "10")
        r["instructions"] = r.get("instructions") or ""
        r["trainer_notes"] = r.get("trainer_notes") or ""
    if not rows:
        st.error("Add at least one exercise before saving.")
    else:
        ok, err = save_workout_plan(c.gym_id, mid, c.user_id, title.strip() or "Workout plan", desc.strip(), rows)
        if ok:
            st.session_state[state_key] = [{k: r.get(k) for k in COLUMNS} for r in rows]
            flash(f"Workout plan published to {member['full_name']}", "🏋️")
            st.rerun()
        st.error(err or "Could not save the plan.")

if existing:
    with st.expander("Preview what the member sees"):
        tabs = st.tabs([d[:3] for d in DAYS])
        for tab, day in zip(tabs, DAYS):
            with tab:
                exs = existing["schedule"].get(day, [])
                if exs:
                    html_block("".join(exercise_card(e) for e in exs))
                else:
                    st.caption("Rest day")

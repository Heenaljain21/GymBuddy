"""SCREEN 8 – Coaching roster: a trainer's athletes (or every athlete, for owners)."""

from __future__ import annotations

import streamlit as st

from components.ui import ctx, page_header, require_role, stat_cards, esc, badge, chip, empty_state, person_row, whatsapp_button, expiry_text, flash
from services.member_service import get_members, get_trainers, get_assignments, assign_trainer
from services.workout_service import get_member_workout
from services.diet_service import get_member_diet
from utils.date_utils import format_date_display, days_since, get_ist_today

require_role("trainer", "owner")
c = ctx()
is_trainer = c.role == "trainer"
page_header("My athletes" if is_trainer else "Coaching roster",
            "Track attendance and plans for the people you coach." if is_trainer else "Who coaches whom — and who needs attention.",
            eyebrow="Coaching")

members = get_members(c.gym_id, active_only=True)
assignments = get_assignments(c.gym_id)
trainers = get_trainers(c.gym_id)
trainer_names = {t["id"]: t["full_name"] for t in trainers}

if is_trainer:
    members = [m for m in members if assignments.get(m["id"]) == c.user_id]
else:
    f = st.segmented_control("Trainer", ["All"] + list(trainer_names.values()) + ["Unassigned"], default="All", label_visibility="collapsed") or "All"
    if f == "Unassigned":
        members = [m for m in members if m["id"] not in assignments]
    elif f != "All":
        members = [m for m in members if trainer_names.get(assignments.get(m["id"])) == f]

if not members:
    empty_state("No athletes here yet", "Owners can assign members to trainers from this page or the Members directory.", "👥")
    st.stop()

today = str(get_ist_today())
enriched = []
for m in members:
    m["has_workout"] = bool(get_member_workout(m["id"]))
    m["has_diet"] = bool(get_member_diet(m["id"]))
    m["days_away"] = days_since(m.get("last_visit")) if m.get("last_visit") else 999
    enriched.append(m)

stat_cards([
    {"label": "Athletes", "value": len(enriched), "icon": "👥", "accent": "purple"},
    {"label": "Trained today", "value": sum(1 for m in enriched if m.get("last_visit") == today), "icon": "🔥", "accent": "lime"},
    {"label": "Missing 5+ days", "value": sum(1 for m in enriched if m["days_away"] >= 5), "icon": "🔔", "accent": "amber"},
    {"label": "Without a plan", "value": sum(1 for m in enriched if not m["has_workout"]), "icon": "📝", "accent": "pink"},
])

s1, s2 = st.columns([2, 1])
query = s1.text_input("Search", placeholder="Search by name or phone", label_visibility="collapsed", icon=":material/search:")
sort = s2.selectbox("Sort", ["Needs attention first", "Name A–Z", "Most recent visit"], label_visibility="collapsed")
if query:
    q = query.lower()
    enriched = [m for m in enriched if q in m["full_name"].lower() or q in (m.get("phone") or "")]
if sort == "Name A–Z":
    enriched.sort(key=lambda m: m["full_name"])
elif sort == "Most recent visit":
    enriched.sort(key=lambda m: m["days_away"])
else:
    enriched.sort(key=lambda m: (-m["days_away"], m["has_workout"]))

for m in enriched:
    with st.container(border=True):
        info, acts = st.columns([2.6, 2], vertical_alignment="center")
        last = "never" if m["days_away"] == 999 else ("today" if m["days_away"] == 0 else f"{m['days_away']}d ago ({format_date_display(m['last_visit'])})")
        flags = (badge("active", "Workout ✓") if m["has_workout"] else badge("pending", "No workout")) + " " + \
                (badge("responded", "Diet ✓") if m["has_diet"] else badge("inactive", "No diet"))
        with info:
            person_row(
                m["full_name"],
                f"{chip(m['member_code'])} · Last visit <b>{esc(last)}</b> · {esc(expiry_text(m.get('expiry_date')))}"
                + ("" if is_trainer else f" · Coach <b>{esc(trainer_names.get(assignments.get(m['id']), 'unassigned'))}</b>"),
                badge(m["membership_status"]) + " " + flags,
            )
        with acts:
            a1, a2, a3 = st.columns(3)
            with a1:
                whatsapp_button(m.get("phone"), f"Hey {m['full_name']}! Coach {c.first_name} here from {c.gym_name}. How's training and nutrition going this week? 💪", "Chat")
            if a2.button("Workout", key=f"wo_{m['id']}", icon=":material/fitness_center:", width="stretch"):
                st.session_state["coach_member_id"] = m["id"]
                st.switch_page("views/workout.py")
            if a3.button("Diet", key=f"dt_{m['id']}", icon=":material/restaurant:", width="stretch"):
                st.session_state["coach_member_id"] = m["id"]
                st.switch_page("views/diet.py")
            if not is_trainer and trainers:
                options = ["unassigned"] + [t["id"] for t in trainers]
                current = assignments.get(m["id"], "unassigned")
                new = st.selectbox("Coach", options, index=options.index(current) if current in options else 0,
                                   format_func=lambda v: "Unassigned" if v == "unassigned" else trainer_names[v],
                                   key=f"coach_{m['id']}", label_visibility="collapsed")
                if new != current:
                    ok, err = assign_trainer(c.gym_id, m["id"], None if new == "unassigned" else new)
                    if ok:
                        flash(f"{m['full_name']} → {trainer_names.get(new, 'unassigned')}")
                        st.rerun()
                    st.error(err)

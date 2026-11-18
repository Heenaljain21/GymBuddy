"""SCREEN 9 – Diet plans organised into Breakfast, Lunch, Evening Snacks and Dinner."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import ctx, page_header, html_block, esc, empty_state, flash
from services.diet_service import get_member_diet, save_diet_plan
from services.member_service import get_members, get_member, get_trainer_member_ids

MEALS = ["Breakfast", "Lunch", "Evening Snacks", "Dinner"]
MEAL_ICONS = {"Breakfast": "🍳", "Lunch": "🍛", "Evening Snacks": "🥜", "Dinner": "🥗"}
COLUMNS = ["meal_type", "food_item", "quantity", "timing", "instructions", "nutrition_notes"]

TEMPLATES = {
    "High protein · veg": [
        ("Breakfast", "Paneer bhurji with 2 multigrain rotis", "100g paneer", "08:00 AM", "Minimal oil", "25g protein"),
        ("Breakfast", "Whey shake", "1 scoop in water", "08:15 AM", "", "24g protein"),
        ("Lunch", "Rajma / chole with brown rice + curd", "1 bowl each", "01:30 PM", "", "20g protein"),
        ("Evening Snacks", "Roasted chana + green tea", "1 handful", "05:30 PM", "", "8g protein"),
        ("Dinner", "Tofu stir-fry with vegetables", "150g tofu", "08:30 PM", "Light on salt", "18g protein"),
    ],
    "High protein · non-veg": [
        ("Breakfast", "4 egg-white omelette + 2 toast", "4 whites + 1 whole egg", "08:00 AM", "", "22g protein"),
        ("Lunch", "Grilled chicken, rice and dal", "150g chicken", "01:30 PM", "1 tsp oil", "40g protein"),
        ("Evening Snacks", "Greek yogurt with fruit", "200g", "05:30 PM", "", "15g protein"),
        ("Dinner", "Fish curry with salad", "150g fish", "08:30 PM", "Skip rice at night", "30g protein"),
    ],
    "Weight loss · 1600 kcal": [
        ("Breakfast", "Vegetable poha + sprouts", "1 plate", "08:00 AM", "", "~350 kcal"),
        ("Lunch", "2 rotis, dal, sabzi, salad", "1 plate", "01:00 PM", "", "~500 kcal"),
        ("Evening Snacks", "Buttermilk + fruit", "1 glass + 1 apple", "05:00 PM", "", "~150 kcal"),
        ("Dinner", "Moong dal chilla + mint chutney", "2 chillas", "07:30 PM", "Finish dinner 2–3h before bed", "~400 kcal"),
    ],
}

c = ctx()


def meal_card(it: dict) -> str:
    macros = f'<div class="gb-item-note" style="color:var(--gb-purple-soft)">⚡ {esc(it.get("nutrition_notes"))}</div>' if it.get("nutrition_notes") else ""
    return f"""
    <div class="gb-item" style="--accent: var(--gb-cyan)">
      <div class="gb-item-head"><div class="gb-item-title">{esc(it.get('food_item'))}</div>
      <span class="gb-badge info">⏰ {esc(it.get('timing') or 'Flexible')}</span></div>
      <div class="gb-item-body"><b style="color:var(--gb-lime)">{esc(it.get('quantity') or '')}</b>
      {f' · {esc(it.get("instructions"))}' if it.get('instructions') else ''}</div>
      {macros}
    </div>"""


# ===========================================================================
# Member view
# ===========================================================================
if c.role == "member":
    page_header("My diet", "Your daily nutrition plan from your coach.", eyebrow="Nutrition")
    member = get_member(c.gym_id, c.member_id) if c.member_id else None
    diet = get_member_diet(member["id"]) if member else None
    if not diet:
        empty_state("No diet plan assigned yet", "Your coach will share one soon.", "🥗")
        st.stop()
    html_block(
        f"""<div class="gb-hero"><div class="gb-eyebrow">Coach · {esc(diet.get('trainer_name'))}</div>
        <h2>{esc(diet.get('title'))}</h2><p>💡 {esc(diet.get('notes') or '')}</p></div>"""
    )
    cols = st.columns(2, gap="medium")
    for i, meal in enumerate(MEALS):
        with cols[i % 2]:
            st.markdown(f"#### {MEAL_ICONS[meal]} {meal}")
            items = diet["meals"].get(meal, [])
            if items:
                html_block("".join(meal_card(it) for it in items))
            else:
                st.caption("Nothing specific — keep it light and balanced.")
    st.stop()

# ===========================================================================
# Coach view
# ===========================================================================
if not c.can_coach:
    empty_state("You don't have access to this page", icon="🔒")
    st.stop()

page_header("Diet plans", "Create a 4-meal plan your athlete can follow from their phone.", eyebrow="Coaching")

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
    format_func=lambda i: f"{by_id[i]['full_name']} · {by_id[i]['member_code']}" + ("" if get_member_diet(i) else "  (no diet yet)"),
)
st.session_state["coach_member_id"] = mid
member = by_id[mid]
existing = get_member_diet(mid)

state_key = f"diet_rows_{mid}"
if state_key not in st.session_state:
    rows = existing.get("all_items", []) if existing else []
    st.session_state[state_key] = [{k: r.get(k) for k in COLUMNS} for r in rows]

t1, t2, t3 = st.columns([2, 1, 1], vertical_alignment="bottom")
template = t1.selectbox("Start from a template", ["—"] + list(TEMPLATES), help="Replaces the table below; nothing is saved until you click Save.")
if t2.button("Apply template", width="stretch", disabled=template == "—"):
    st.session_state[state_key] = [dict(zip(COLUMNS, row)) for row in TEMPLATES[template]]
    st.session_state.pop(f"diet_editor_{mid}", None)
    st.rerun()
if t3.button("Clear all", width="stretch"):
    st.session_state[state_key] = []
    st.session_state.pop(f"diet_editor_{mid}", None)
    st.rerun()

with st.form(f"diet_form_{mid}", border=True):
    a, b = st.columns([1.2, 2])
    title = a.text_input("Plan title", value=(existing or {}).get("title") or "Balanced nutrition plan")
    notes = b.text_input("Guidelines & hydration", value=(existing or {}).get("notes") or "Drink 3L water daily. Prioritise protein at every meal.")
    df = pd.DataFrame(st.session_state[state_key], columns=COLUMNS)
    if not df.empty:
        df["meal_type"] = pd.Categorical(df["meal_type"], categories=MEALS, ordered=True)
        df = df.sort_values("meal_type", kind="stable").reset_index(drop=True)
        df["meal_type"] = df["meal_type"].astype(str)
    edited = st.data_editor(
        df, key=f"diet_editor_{mid}", num_rows="dynamic", hide_index=True, width="stretch",
        column_config={
            "meal_type": st.column_config.SelectboxColumn("Meal", options=MEALS, required=True, default="Breakfast", width="small"),
            "food_item": st.column_config.TextColumn("Food", required=True, width="large"),
            "quantity": st.column_config.TextColumn("Quantity", width="medium"),
            "timing": st.column_config.TextColumn("Time", width="small"),
            "instructions": st.column_config.TextColumn("Preparation", width="medium"),
            "nutrition_notes": st.column_config.TextColumn("Macros", width="small"),
        },
    )
    st.caption("Add rows with ➕ at the bottom of the table, delete by selecting rows and pressing Delete.")
    saved = st.form_submit_button("Save & publish to member", type="primary", width="stretch", icon=":material/publish:")

if saved:
    rows = [{k: (r.get(k) or "") for k in COLUMNS} for r in edited.to_dict("records") if str(r.get("food_item") or "").strip()]
    if not rows:
        st.error("Add at least one food item before saving.")
    else:
        ok, err = save_diet_plan(c.gym_id, mid, c.user_id, title.strip() or "Diet plan", notes.strip(), rows)
        if ok:
            st.session_state[state_key] = rows
            flash(f"Diet plan published to {member['full_name']}", "🥗")
            st.rerun()
        st.error(err or "Could not save the plan.")

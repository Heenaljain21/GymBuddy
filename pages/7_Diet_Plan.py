"""SCREEN 9 – DIET PLAN

Comprehensive nutrition and meal management system.
Supports 4 structured meals: Breakfast, Lunch, Evening Snacks, and Dinner.
- Members: View personalized nutrition guide.
- Trainers: Formulate, customize, and assign nutrition regimes.
"""

from __future__ import annotations
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state
from utils.permissions import require_auth
from services.diet_service import get_member_diet, save_diet_plan
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

render_navbar("Nutritional Diet Plan", "Targeted Macros, Meal Timings & Dietary Advice")

MEALS = ["Breakfast", "Lunch", "Evening Snacks", "Dinner"]
MEAL_ICONS = {"Breakfast": "🍳", "Lunch": "🍛", "Evening Snacks": "🍪", "Dinner": "🍝"}

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
        st.info("No diet plan assigned yet.")
        st.stop()

    diet = get_member_diet(member["id"])

    if not diet:
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.7); border: 1px dashed rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 3rem; text-align: center; color: #94A3B8;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🥗</div>
                <h3 style="color: #F8FAFC;">No Personalized Diet Plan Assigned</h3>
                <p>Your fitness coach has not assigned a nutritional diet plan yet. Inquire with your coach at the gym!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background: rgba(6, 214, 201, 0.12); border: 1px solid rgba(6, 214, 201, 0.35); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.8rem; color: #06D6C9; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">ACTIVE NUTRITION REGIME</div>
                        <h2 style="color: #F8FAFC; margin: 0.25rem 0 0.5rem 0;">{diet.get('title')}</h2>
                        <div style="font-size: 0.88rem; color: #94A3B8;">💡 {diet.get('notes')}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 0.8rem; color: #94A3B8;">Nutritionist / Coach:</span>
                        <div style="font-weight: 700; color: #06D6C9; font-size: 1.05rem;">🥗 {diet.get('trainer_name')}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        meals_by_type = diet.get("meals", {})
        tab_list = st.tabs([f"{MEAL_ICONS[m]} {m}" for m in MEALS])

        for i, meal_type in enumerate(MEALS):
            with tab_list[i]:
                items = meals_by_type.get(meal_type, [])
                if not items:
                    st.caption("No specific items listed for this meal.")
                else:
                    for it in items:
                        st.markdown(
                            f"""
                            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.15); border-left: 4px solid #06D6C9; border-radius: 12px; padding: 1.25rem; margin-bottom: 0.85rem;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h4 style="color: #F8FAFC; margin: 0; font-size: 1.1rem;">{it.get('food_item')}</h4>
                                    <span style="background: rgba(6, 214, 201, 0.15); color: #06D6C9; border: 1px solid #06D6C9; padding: 2px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700;">
                                        ⏰ {it.get('timing') or 'Flexible'}
                                    </span>
                                </div>
                                <div style="font-size: 0.88rem; color: #A3FF5C; font-weight: 600; margin-top: 0.35rem;">
                                    Portion / Quantity: {it.get('quantity')}
                                </div>
                                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.25rem;">
                                    📝 <b>Preparation:</b> {it.get('instructions') or 'Standard cooking'}
                                </div>
                                {f"<div style='font-size: 0.82rem; color: #A78BFA; margin-top: 0.25rem;'>⚡ <b>Macro Profile:</b> {it.get('nutrition_notes')}</div>" if it.get('nutrition_notes') else ""}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

# ==========================================
# 2. TRAINER & OWNER VIEW (EDITOR)
# ==========================================
else:
    all_m = get_members(gym_id)
    if not all_m:
        st.warning("No members registered yet.")
        st.stop()

    member_options = {f"{m['full_name']} ({m.get('member_code', '-')})": m for m in all_m}
    sel_label = st.selectbox("Select Member for Diet Management", options=list(member_options.keys()))
    sel_member = member_options[sel_label]
    sel_mid = sel_member["id"]

    existing_diet = get_member_diet(sel_mid)

    st.markdown("---")
    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        diet_title = st.text_input("Diet Plan Title", value=existing_diet.get("title", "High Protein Muscle Building Diet") if existing_diet else "High Protein Muscle Building Diet")
    with col_d2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.markdown(f"**Target Member:** {sel_member['full_name']}")

    diet_notes = st.text_area("Diet Guidelines & Hydration Targets", value=existing_diet.get("notes", "Target 140g protein daily. Drink 3.5L water minimum.") if existing_diet else "Target 140g protein daily. Drink 3.5L water minimum.")

    state_key = f"diet_builder_{sel_mid}"
    if state_key not in st.session_state:
        if existing_diet and existing_diet.get("all_items"):
            st.session_state[state_key] = existing_diet["all_items"]
        else:
            st.session_state[state_key] = [
                {"meal_type": "Breakfast", "food_item": "Oatmeal with Whey Protein & Almonds", "quantity": "60g oats + 1 scoop whey + 10 almonds", "timing": "08:00 AM", "instructions": "Mix with warm water or skimmed milk", "nutrition_notes": "32g Protein, 45g Carbs"},
                {"meal_type": "Lunch", "food_item": "Grilled Paneer/Chicken with Brown Rice & Dal", "quantity": "150g Paneer/Chicken + 1 bowl Rice + 1 bowl Dal", "timing": "01:30 PM", "instructions": "Cook in 1 tsp olive oil", "nutrition_notes": "38g Protein, 55g Carbs"},
                {"meal_type": "Evening Snacks", "food_item": "Boiled Eggs or Sprouts Salad + Black Coffee", "quantity": "4 egg whites or 1 cup sprouts", "timing": "05:30 PM", "instructions": "Pre-workout energy booster", "nutrition_notes": "15g Protein"},
                {"meal_type": "Dinner", "food_item": "Tofu/Soya Chunks with Mixed Vegetable Salad", "quantity": "150g Tofu + Green Salad", "timing": "08:30 PM", "instructions": "Light salt, low carb dinner", "nutrition_notes": "25g Protein, low carb"},
            ]

    items = st.session_state[state_key]

    tab_list = st.tabs([f"{MEAL_ICONS[m]} {m}" for m in MEALS])

    for i, m_type in enumerate(MEALS):
        with tab_list[i]:
            m_items = [it for it in items if it.get("meal_type") == m_type]
            if m_items:
                for idx, it in enumerate(m_items):
                    col_i1, col_i2 = st.columns([3, 1])
                    with col_i1:
                        st.markdown(f"**{it.get('food_item')}** — `{it.get('quantity')}` ({it.get('timing', 'Anytime')})")
                        st.caption(f"Prep: {it.get('instructions') or 'Standard'} | Notes: {it.get('nutrition_notes') or '-'}")
                    with col_i2:
                        if st.button("🗑️ Remove", key=f"del_m_{m_type}_{idx}"):
                            items.remove(it)
                            st.rerun()
            else:
                st.caption("No food items added for this meal section yet.")

            with st.expander(f"➕ Add Food Item to {m_type}"):
                with st.form(f"add_food_{m_type}"):
                    f_name = st.text_input("Food Item Name", placeholder="e.g. Scrambled Eggs on Whole Wheat Toast")
                    f_qty = st.text_input("Quantity / Portion", placeholder="e.g. 3 eggs + 2 slices")
                    f_time = st.text_input("Recommended Timing", placeholder="e.g. 08:30 AM")
                    f_prep = st.text_input("Preparation / Recipe Instructions", placeholder="e.g. No butter, salt & pepper to taste")
                    f_macros = st.text_input("Nutrition / Macro Notes", placeholder="e.g. 22g Protein, 28g Carbs")

                    if st.form_submit_button(f"Add to {m_type}"):
                        if f_name:
                            items.append({
                                "meal_type": m_type,
                                "food_item": f_name,
                                "quantity": f_qty,
                                "timing": f_time,
                                "instructions": f_prep,
                                "nutrition_notes": f_macros,
                            })
                            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if st.button("💾 Save & Assign Complete Diet Plan", use_container_width=True):
        with st.spinner("Saving nutritional plan..."):
            ok, err = save_diet_plan(
                gym_id=gym_id,
                member_id=sel_mid,
                trainer_id=trainer_id,
                title=diet_title,
                notes=diet_notes,
                meals=items,
            )
            if ok:
                show_success(f"Diet plan saved and assigned to {sel_member['full_name']}!")
                st.rerun()
            else:
                show_error(err or "Failed to save diet plan.")

"""Platform console (super-admin): gym tenants, provisioning and the global user directory."""

from __future__ import annotations
import re
import uuid

import pandas as pd
import streamlit as st

from components.ui import ctx, page_header, require_role, stat_cards, html_block, esc, badge, empty_state, flash
from services.gym_service import get_all_gyms, create_gym, create_membership_plan
from utils.security import get_supabase_client
from utils.validators import validate_phone, validate_email

require_role("admin")
c = ctx()
page_header("Platform console", "Every gym on GYM BUDDY, in one place.", eyebrow="Super admin")

client = get_supabase_client()
gyms = get_all_gyms()
try:
    profiles = client.table("profiles").select("*").execute().data or []
    members = client.table("members").select("id, gym_id").execute().data or []
except Exception:
    profiles, members = [], []

stat_cards([
    {"label": "Gyms", "value": len(gyms), "icon": "🏢", "accent": "purple"},
    {"label": "Staff accounts", "value": sum(1 for p in profiles if p.get("role") in ("owner", "receptionist", "trainer")), "icon": "🧑‍💼", "accent": "cyan"},
    {"label": "Members", "value": len(members), "icon": "👥", "accent": "lime"},
])

tab_gyms, tab_new, tab_users = st.tabs([":material/apartment: Gyms", ":material/add_business: Add a gym", ":material/group: Users"])

with tab_gyms:
    if not gyms:
        empty_state("No gyms yet", "Provision your first gym in the next tab.", "🏢")
    cols = st.columns(2)
    for i, g in enumerate(gyms):
        count = sum(1 for m in members if m.get("gym_id") == g["id"])
        staff = sum(1 for p in profiles if p.get("gym_id") == g["id"] and p.get("role") != "member")
        with cols[i % 2]:
            with st.container(border=True):
                html_block(
                    f"""<div class="gb-row-title" style="font-size:1.1rem">{esc(g.get('name'))} {badge('active' if g.get('is_active', True) else 'inactive')}</div>
                    <div class="gb-row-meta">📍 {esc(g.get('city') or '—')}, {esc(g.get('state') or '—')} · 📞 {esc(g.get('phone') or '—')}</div>
                    <div class="gb-row-meta">{esc(g.get('address') or '')}</div>
                    <div class="gb-row-meta" style="margin-top:.5rem"><b>{count}</b> members · <b>{staff}</b> staff</div>"""
                )

with tab_new:
    with st.form("new_gym_form", clear_on_submit=True):
        a, b = st.columns(2)
        name = a.text_input("Gym name *", placeholder="e.g. Iron Fitness Hub")
        slug = b.text_input("URL slug", placeholder="auto-generated from name")
        phone = a.text_input("Contact phone *", placeholder="10-digit mobile")
        email = b.text_input("Business email", placeholder="contact@ironfitness.in")
        city = a.text_input("City *", placeholder="e.g. Mumbai")
        state = b.text_input("State", placeholder="e.g. Maharashtra")
        address = st.text_input("Full address", placeholder="Street, locality, PIN code")
        seed_plans = st.checkbox("Create the 4 standard plans (Monthly / Quarterly / Half-yearly / Annual)", value=True)
        submitted = st.form_submit_button("Create gym", type="primary", icon=":material/rocket_launch:", width="stretch")
    if submitted:
        errors = []
        if not name.strip():
            errors.append("Gym name is required.")
        if not city.strip():
            errors.append("City is required.")
        if not validate_phone(phone):
            errors.append("Enter a valid 10-digit phone number.")
        if email and not validate_email(email):
            errors.append("Enter a valid email address.")
        slug_val = re.sub(r"[^a-z0-9]+", "-", (slug or name).lower()).strip("-")
        if any(g.get("slug") == slug_val for g in gyms):
            errors.append(f"The slug '{slug_val}' is already taken.")
        if errors:
            st.error("\n".join(f"- {e}" for e in errors))
        else:
            gym_id = str(uuid.uuid4())
            ok, err, _ = create_gym({
                "id": gym_id, "name": name.strip(), "slug": slug_val, "phone": phone.strip(), "email": email.strip() or None,
                "city": city.strip(), "state": state.strip(), "address": address.strip(), "is_active": True,
                "inactivity_threshold_days": 14,
            })
            if ok and seed_plans:
                for pname, days, price, desc in [
                    ("Monthly", 30, 1500, "1 month access"), ("Quarterly", 90, 4000, "3 months access"),
                    ("Half-Yearly", 180, 7000, "6 months access"), ("Annual", 365, 12000, "12 months access"),
                ]:
                    create_membership_plan({"id": str(uuid.uuid4()), "gym_id": gym_id, "name": pname, "duration_days": days,
                                            "price": price, "description": desc, "is_active": True})
            if ok:
                flash(f"{name} is live on GYM BUDDY", "🚀")
                st.rerun()
            st.error(f"Could not create the gym: {err}")

with tab_users:
    if not profiles:
        empty_state("No users found", icon="👤")
    else:
        gym_names = {g["id"]: g["name"] for g in gyms}
        role_filter = st.segmented_control("Role", ["All", "owner", "receptionist", "trainer", "member", "admin"], default="All",
                                           format_func=str.title, label_visibility="collapsed") or "All"
        rows = [p for p in profiles if role_filter == "All" or p.get("role") == role_filter]
        st.dataframe(pd.DataFrame([{
            "Name": p.get("full_name"), "Email": p.get("email"), "Role": (p.get("role") or "").title(),
            "Phone": p.get("phone"), "Gym": gym_names.get(p.get("gym_id"), "—"),
        } for p in rows]), hide_index=True, width="stretch")
        st.caption("New staff accounts are created in Supabase Auth; their profile row sets the role and gym.")

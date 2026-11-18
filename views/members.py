"""Member directory: search, filter, inspect and manage any member."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import (
    ctx, page_header, require_role, stat_cards, html_block, esc, badge, chip, empty_state,
    whatsapp_button, kv_table, expiry_text, flash, STATUS_LABELS,
)
from components.qr_components import render_member_pass
from services.member_service import get_members, update_member, get_trainers, get_assignments, assign_trainer
from services.attendance_service import get_member_attendance
from services.payment_service import get_member_payments
from utils.helpers import format_currency, format_phone
from utils.date_utils import format_date_display, format_time_display
from utils.validators import validate_phone, validate_email

require_role("owner", "receptionist")
c = ctx()
page_header("Members", f"Everyone registered at {c.gym_name}", eyebrow="Directory")

members = get_members(c.gym_id)
trainers = get_trainers(c.gym_id)
trainer_names = {t["id"]: t["full_name"] for t in trainers}
assignments = get_assignments(c.gym_id)

counts = {k: sum(1 for m in members if m["membership_status"] == k) for k in STATUS_LABELS}
stat_cards([
    {"label": "Total", "value": len(members), "icon": "👥", "accent": "purple"},
    {"label": "Active", "value": counts["active"], "icon": "⚡", "accent": "lime"},
    {"label": "Expiring soon", "value": counts["expiring"], "icon": "⏳", "accent": "amber"},
    {"label": "Expired", "value": counts["expired"], "icon": "⛔", "accent": "red"},
])

f1, f2, f3 = st.columns([1.5, 2.4, 1.1])
query = f1.text_input("Search", placeholder="Name, phone or member ID", label_visibility="collapsed", icon=":material/search:")
status_filter = f2.segmented_control(
    "Status", ["All", "Active", "Expiring", "Expired", "Inactive"], default="All", label_visibility="collapsed",
)
trainer_filter = f3.selectbox("Trainer", ["Any trainer", "Unassigned"] + list(trainer_names.values()), label_visibility="collapsed")

rows = members
if query:
    q = query.strip().lower()
    rows = [m for m in rows if q in m["full_name"].lower() or q in (m.get("phone") or "") or q in (m.get("member_code") or "").lower()]
if status_filter and status_filter != "All":
    rows = [m for m in rows if m["membership_status"] == status_filter.lower()]
if trainer_filter == "Unassigned":
    rows = [m for m in rows if m["id"] not in assignments]
elif trainer_filter != "Any trainer":
    rows = [m for m in rows if trainer_names.get(assignments.get(m["id"])) == trainer_filter]

if not rows:
    empty_state("No members match your filters", "Try clearing the search or status filter.", "🔍")
    st.stop()

df = pd.DataFrame([{
    "Member": m["full_name"],
    "ID": m["member_code"],
    "Phone": format_phone(m.get("phone")),
    "Plan": m["plan_name"],
    "Status": STATUS_LABELS.get(m["membership_status"], m["membership_status"]),
    "Expires": pd.to_datetime(m.get("expiry_date")) if m.get("expiry_date") else pd.NaT,
    "Last visit": pd.to_datetime(m.get("last_visit")) if m.get("last_visit") else pd.NaT,
    "Trainer": trainer_names.get(assignments.get(m["id"]), "—"),
} for m in rows])

st.caption(f"Showing {len(rows)} of {len(members)} members · click a row to open the profile")
event = st.dataframe(
    df, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", key="members_table",
    column_config={
        "Expires": st.column_config.DateColumn(format="DD MMM YYYY"),
        "Last visit": st.column_config.DateColumn(format="DD MMM YYYY"),
    },
)
st.download_button("Export CSV", df.to_csv(index=False).encode(), file_name="members.csv", mime="text/csv", icon=":material/download:")

selected = event.selection.rows if event and event.selection else []
if not selected:
    st.stop()

m = rows[selected[0]]
st.divider()

head_l, head_r = st.columns([3, 2], vertical_alignment="center")
with head_l:
    html_block(
        f"""<div class="gb-person"><div class="gb-avatar" style="width:54px;height:54px;font-size:1.2rem">{esc(''.join(p[0] for p in m['full_name'].split()[:2]))}</div>
        <div><div class="gb-row-title" style="font-size:1.35rem">{esc(m['full_name'])} {badge(m['membership_status'])}</div>
        <div class="gb-row-meta">{chip(m['member_code'])} · {esc(m['plan_name'])} · {esc(expiry_text(m.get('expiry_date')))}</div></div></div>"""
    )
with head_r:
    b1, b2, b3 = st.columns(3)
    with b1:
        whatsapp_button(m.get("phone"), f"Hi {m['full_name']}! Greetings from {c.gym_name}.", "Chat")
    if b2.button("Renew", icon=":material/autorenew:", width="stretch"):
        st.session_state["renew_member_id"] = m["id"]
        st.switch_page("views/renewals.py")
    if b3.button("Collect fee", icon=":material/payments:", width="stretch"):
        st.session_state["fee_member_id"] = m["id"]
        st.switch_page("views/fees.py")

tab_profile, tab_activity, tab_pass = st.tabs(["Profile", "Visits & payments", "QR pass"])

with tab_profile:
    info, edit = st.columns([1, 1.2], gap="large")
    with info:
        kv_table([
            ("Phone", format_phone(m.get("phone"))),
            ("Email", m.get("email") or "—"),
            ("Gender / age", f"{m.get('gender') or '—'} · {m.get('age') or '—'}"),
            ("Address", m.get("address") or "—"),
            ("Emergency contact", format_phone(m.get("emergency_contact")) if m.get("emergency_contact") else "—"),
            ("Joined", format_date_display(m.get("joined_date"))),
            ("Trainer", trainer_names.get(assignments.get(m["id"]), "Not assigned")),
        ])
    with edit:
        with st.form(f"edit_{m['id']}"):
            st.markdown("**Edit details**")
            e1, e2 = st.columns(2)
            phone = e1.text_input("Phone", value=m.get("phone") or "")
            email = e2.text_input("Email", value=m.get("email") or "")
            address = st.text_input("Address", value=m.get("address") or "")
            emergency = st.text_input("Emergency contact", value=m.get("emergency_contact") or "")
            trainer_choice = None
            if c.role in ("owner", "admin") and trainers:
                options = ["Not assigned"] + [t["id"] for t in trainers]
                current = assignments.get(m["id"], "Not assigned")
                trainer_choice = st.selectbox(
                    "Trainer", options, index=options.index(current) if current in options else 0,
                    format_func=lambda v: trainer_names.get(v, v),
                )
            active = st.toggle("Member is active", value=m.get("is_active", True), help="Inactive members are hidden from win-back campaigns.")
            if st.form_submit_button("Save changes", type="primary", width="stretch"):
                errors = []
                if not validate_phone(phone):
                    errors.append("Enter a valid 10-digit mobile number.")
                if email and not validate_email(email):
                    errors.append("Enter a valid email address.")
                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    ok, err = update_member(m["id"], {
                        "phone": "".join(ch for ch in phone if ch.isdigit())[-10:],
                        "email": email.strip() or None,
                        "address": address.strip(),
                        "emergency_contact": "".join(ch for ch in emergency if ch.isdigit())[-10:] or None,
                        "is_active": active,
                    })
                    if ok and trainer_choice is not None and trainer_choice != assignments.get(m["id"], "Not assigned"):
                        ok, err = assign_trainer(c.gym_id, m["id"], None if trainer_choice == "Not assigned" else trainer_choice)
                    if ok:
                        flash(f"Saved {m['full_name']}'s profile")
                        st.rerun()
                    st.error(err or "Could not save changes.")

with tab_activity:
    v, p = st.columns(2, gap="large")
    with v:
        st.markdown("**Recent visits**")
        visits = get_member_attendance(c.gym_id, m["id"], limit=20)
        if visits:
            st.dataframe(pd.DataFrame([{
                "Date": format_date_display(a.get("check_in_date")),
                "Time": format_time_display(a.get("check_in_time")),
                "Method": (a.get("method") or "qr_code").replace("_", " ").title(),
            } for a in visits]), hide_index=True, width="stretch")
        else:
            empty_state("No visits yet", icon="📭")
    with p:
        st.markdown("**Payments**")
        pays = get_member_payments(c.gym_id, m["id"])
        if pays:
            st.dataframe(pd.DataFrame([{
                "Date": format_date_display(x.get("payment_date")),
                "Amount": format_currency(x.get("amount")),
                "Mode": x.get("payment_method"),
                "Receipt": x.get("receipt_no"),
            } for x in pays]), hide_index=True, width="stretch")
        else:
            empty_state("No payments recorded", icon="📭")

with tab_pass:
    render_member_pass(m["member_code"], m["full_name"], c.gym_name, key="dir")

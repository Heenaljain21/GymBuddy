"""SCREEN 7 – Renewal management: who is due, remind them on WhatsApp, renew in place."""

from __future__ import annotations

import streamlit as st

from components.ui import ctx, page_header, require_role, stat_cards, esc, badge, chip, empty_state, person_row, whatsapp_button, expiry_text, flash
from services.renewal_service import get_expiring_memberships, renew_membership
from services.gym_service import get_membership_plans
from utils.helpers import format_currency
from utils.date_utils import get_ist_today, format_date_display
from datetime import date, timedelta

require_role("owner", "receptionist")
c = ctx()
page_header("Renewals", "Members whose plans are ending — remind, renew, repeat.", eyebrow="Front desk")

cats = get_expiring_memberships(c.gym_id)
plans = get_membership_plans(c.gym_id, active_only=True)
by_member = {it["member_id"]: it for it in cats["all"]}


@st.dialog("Renew membership")
def renew_dialog(item: dict) -> None:
    st.markdown(f"**{item['member_name']}** · {item['member_code']}")
    st.caption(f"Current: {item['plan_name']} · {expiry_text(item['expiry_date'])}")
    if not plans:
        st.error("No active plans are configured.")
        return
    names = [p["name"] for p in plans]
    default = names.index(item["plan_name"]) if item["plan_name"] in names else 0
    plan_name = st.selectbox("New plan", names, index=default)
    plan = plans[names.index(plan_name)]

    today = get_ist_today()
    try:
        cur_end = date.fromisoformat(str(item["expiry_date"])[:10])
    except (TypeError, ValueError):
        cur_end = today
    starts = cur_end if cur_end > today else today
    new_end = starts + timedelta(days=int(plan["duration_days"]))
    st.info(f"New expiry: **{format_date_display(new_end)}** ({plan['duration_days']} days from {format_date_display(starts)})", icon=":material/event:")

    a, b = st.columns(2)
    amount = a.number_input("Amount (₹)", value=float(plan["price"]), min_value=0.0, step=100.0, key=f"ra_{plan['id']}")
    method = b.selectbox("Payment method", ["UPI", "Cash", "Bank Transfer"])
    ref = st.text_input("UPI / transaction ref", placeholder="optional")
    if st.button("Confirm renewal", type="primary", width="stretch", icon=":material/check_circle:"):
        ok, err = renew_membership(c.gym_id, item["member_id"], plan["id"], amount, method, ref)
        if ok:
            flash(f"{item['member_name']} renewed till {format_date_display(new_end)}", "🔄")
            st.rerun()
        st.error(err or "Renewal failed.")


pre = st.session_state.pop("renew_member_id", None)
if pre and pre in by_member:
    renew_dialog(by_member[pre])
elif pre:
    st.info("That member has no membership on record yet — pick a plan for them via **New member** or record a fee.")

soon = cats["within_7_days"]
stat_cards([
    {"label": "Due in 7 days", "value": len(soon), "icon": "⏳", "accent": "amber"},
    {"label": "Due in 8–15 days", "value": len(cats["within_15_days"]), "icon": "📅", "accent": "blue"},
    {"label": "Due in 16–30 days", "value": len(cats["within_30_days"]), "icon": "🗓️", "accent": "cyan"},
    {"label": "Already expired", "value": len(cats["expired"]), "icon": "⛔", "accent": "red",
     "sub": format_currency(sum(i["plan_price"] for i in cats["expired"])).replace(".00", "") + " to recover"},
])

buckets = {
    f"≤ 7 days ({len(soon)})": soon,
    f"8–15 days ({len(cats['within_15_days'])})": cats["within_15_days"],
    f"16–30 days ({len(cats['within_30_days'])})": cats["within_30_days"],
    f"Expired ({len(cats['expired'])})": cats["expired"],
    f"All ({len(cats['all'])})": cats["all"],
}
f1, f2 = st.columns([2.2, 1])
choice = f1.segmented_control("Bucket", list(buckets), default=list(buckets)[0], label_visibility="collapsed") or list(buckets)[0]
search = f2.text_input("Search", placeholder="Search name or ID", label_visibility="collapsed", icon=":material/search:")
items = buckets[choice]
if search:
    q = search.lower()
    items = [i for i in items if q in i["member_name"].lower() or q in i["member_code"].lower()]

if not items:
    empty_state("Nobody in this bucket", "Nice — nothing to chase here.", "🎉")

for it in items:
    rem = it["days_remaining"]
    kind = "expired" if rem < 0 else ("expiring" if rem <= 7 else "active")
    with st.container(border=True):
        info, wa, act = st.columns([3.2, 1.2, 1], vertical_alignment="center")
        with info:
            person_row(
                it["member_name"],
                f"{chip(it['member_code'])} · {esc(it['plan_name'])} · <b>{esc(expiry_text(it['expiry_date']))}</b>",
                badge(kind, "Expired" if rem < 0 else ("Due today" if rem == 0 else f"{rem}d left")),
            )
        with wa:
            when = "has expired" if rem < 0 else ("ends today" if rem == 0 else f"ends on {format_date_display(it['expiry_date'])}")
            whatsapp_button(
                it["phone"],
                f"Hi {it['member_name']}! Your {it['plan_name']} membership at {c.gym_name} {when}. "
                f"Renew now to keep training without a break 💪 Reply to this message or visit the front desk.",
                "Remind",
            )
        with act:
            if st.button("Renew", key=f"renew_{it['member_id']}", type="primary", width="stretch", icon=":material/autorenew:"):
                renew_dialog(it)

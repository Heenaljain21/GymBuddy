"""SCREEN 11 – Win-back: find members who stopped coming and bring them back on WhatsApp."""

from __future__ import annotations

import streamlit as st

from components.ui import ctx, page_header, require_role, stat_cards, esc, badge, chip, empty_state, person_row, whatsapp_button, flash
from services.inactivity_service import get_inactive_members, log_followup, NEVER
from utils.date_utils import format_date_display

STATUSES = ["pending", "contacted", "responded", "returned", "lost"]

require_role("owner", "receptionist")
c = ctx()
page_header("Win-back", "Members who've gone quiet — reach out before they cancel.", eyebrow="Retention")

t1, t2 = st.columns([2, 1.2], vertical_alignment="bottom")
threshold = t1.slider("Show members absent for at least", min_value=7, max_value=60, value=7, step=1, format="%d days")
status_filter = t2.multiselect("Outreach status", STATUSES, placeholder="Any status", format_func=str.title)

cats = get_inactive_members(c.gym_id, threshold_days=threshold)
stat_cards([
    {"label": "7–14 days away", "value": len(cats["7_to_14_days"]), "icon": "⚠️", "accent": "amber", "sub": "Early warning"},
    {"label": "15–30 days away", "value": len(cats["15_to_30_days"]), "icon": "⏳", "accent": "pink", "sub": "High dropout risk"},
    {"label": "30+ days away", "value": len(cats["over_30_days"]), "icon": "🚨", "accent": "red", "sub": "Critical"},
    {"label": "Never visited", "value": len(cats["never_attended"]), "icon": "⭕", "accent": "purple", "sub": "Joined, never came"},
])

buckets = {
    f"All ({len(cats['all_inactive'])})": cats["all_inactive"],
    f"7–14 days ({len(cats['7_to_14_days'])})": cats["7_to_14_days"],
    f"15–30 days ({len(cats['15_to_30_days'])})": cats["15_to_30_days"],
    f"30+ days ({len(cats['over_30_days'])})": cats["over_30_days"],
    f"Never visited ({len(cats['never_attended'])})": cats["never_attended"],
}
choice = st.segmented_control("Bucket", list(buckets), default=list(buckets)[0], label_visibility="collapsed") or list(buckets)[0]
items = buckets[choice]
if status_filter:
    items = [i for i in items if i["contact_status"] in status_filter]

if not items:
    empty_state("Nobody here", "Everyone in this group is showing up. 💪", "🎉")

for it in items:
    never = it["days_inactive"] == NEVER
    away = "Never visited" if never else f"{it['days_inactive']} days away"
    last = "—" if never else format_date_display(it["last_visit"])
    note = f" · “{esc(it['last_note'])}”" if it.get("last_note") else ""
    if never:
        msg = (f"Hi {it['member_name']}! 👋 You joined {c.gym_name} but we haven't seen you yet. "
               "Our coaches would love to give you a free orientation this week — reply with a time that suits you!")
    else:
        msg = (f"Hey {it['member_name']}! We've missed you at {c.gym_name} — it's been {it['days_inactive']} days. "
               "Consistency is everything, and we're here to help you get back on track. Shall we book your next session? 🏋️")

    with st.container(border=True):
        info, wa, log = st.columns([3.2, 1.2, 1], vertical_alignment="center")
        with info:
            person_row(
                it["member_name"],
                f"{chip(it['member_code'])} · Last seen <b>{esc(last)}</b>{note}",
                badge("expired" if it["days_inactive"] > 30 else "expiring", away) + " " + badge(it["contact_status"]),
            )
        with wa:
            whatsapp_button(it["phone"], msg, "Message")
        with log:
            with st.popover("Log outreach", icon=":material/edit_note:", width="stretch"):
                with st.form(f"follow_{it['member_id']}", border=False):
                    cur = it["contact_status"] if it["contact_status"] in STATUSES else "pending"
                    status = st.selectbox("Status", STATUSES, index=STATUSES.index(cur) if cur != "pending" else 1, format_func=str.title)
                    notes = st.text_area("Note", value=it.get("last_note") or "", placeholder="e.g. Was travelling, back on Monday")
                    if st.form_submit_button("Save", type="primary", width="stretch"):
                        ok, err = log_followup(c.gym_id, it["member_id"], c.user_id, status, notes.strip())
                        if ok:
                            flash(f"Outreach logged for {it['member_name']}", "📝")
                            st.rerun()
                        st.error(err)

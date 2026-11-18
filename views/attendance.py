"""SCREEN 3 & 5 – Member QR pass and front-desk check-in.

Members see their pass and history. Staff get a scanner (camera / image / typed
ID, phone or name) that checks members in instantly, blocks duplicates, and
flags lapsed memberships.
"""

from __future__ import annotations
from datetime import timedelta

import pandas as pd
import streamlit as st

from components.ui import (
    ctx, page_header, stat_cards, empty_state, result_banner, expiry_text,
)
from components.qr_components import render_member_pass, decode_qr_image
from services.attendance_service import check_in, get_today_attendance, get_member_attendance, get_monthly_attendance_count, is_already_checked_in
from services.member_service import get_member, get_member_by_qr, get_members, search_members
from utils.date_utils import get_ist_today, format_date_display, format_time_display

c = ctx()

# ===========================================================================
# Member: my pass
# ===========================================================================
if c.role == "member":
    page_header("My QR pass", "Show this at the front desk to check in.", eyebrow="Attendance")
    member = get_member(c.gym_id, c.member_id) if c.member_id else None
    if not member:
        empty_state("Your member profile isn't linked yet", "Ask the front desk to link your account.", "🔗")
        st.stop()

    left, right = st.columns([1, 1.15], gap="large")
    with left:
        render_member_pass(member["member_code"], member["full_name"], c.gym_name, key="me")
    with right:
        checked = is_already_checked_in(c.gym_id, member["id"])
        if checked:
            result_banner("ok", "You're checked in today", "Have a great session! 💪")
        else:
            result_banner("warn", "Not checked in yet today", "Show your pass at the desk when you arrive.")
        stat_cards([
            {"label": "Visits this month", "value": get_monthly_attendance_count(c.gym_id, member["id"]), "icon": "📅", "accent": "cyan"},
            {"label": "Membership", "value": member["plan_name"], "icon": "🎫", "accent": "purple", "sub": expiry_text(member.get("expiry_date"))},
        ])
        st.markdown("#### Recent check-ins")
        history = get_member_attendance(c.gym_id, member["id"], limit=15)
        if history:
            st.dataframe(pd.DataFrame([{
                "Date": format_date_display(h.get("check_in_date")),
                "Time": format_time_display(h.get("check_in_time")),
                "Method": (h.get("method") or "qr_code").replace("_", " ").title(),
            } for h in history]), hide_index=True, width="stretch")
        else:
            empty_state("No check-ins yet", "Your first visit will show up here.", "🌱")
    st.stop()

# ===========================================================================
# Staff: check-in desk
# ===========================================================================
page_header("Check-in desk", "Scan a pass or type an ID, phone or name.", eyebrow="Front desk")
today = get_ist_today()


def do_check_in(member: dict, method: str) -> None:
    """Check a member in and remember the outcome for the result banner."""
    ok, msg, rec = check_in(c.gym_id, member["id"], method=method)
    st.session_state["last_checkin"] = {
        "ok": ok, "name": member["full_name"], "code": member["member_code"], "plan": member["plan_name"],
        "status": member["membership_status"], "expiry": member.get("expiry_date"),
        "time": format_time_display((rec or {}).get("check_in_time")) if ok else "",
        "msg": msg,
    }


def resolve_and_check_in(raw: str, method: str) -> None:
    st.session_state.pop("checkin_matches", None)
    member = get_member_by_qr(c.gym_id, raw)
    if member:
        do_check_in(member, method)
        return
    matches = search_members(c.gym_id, raw)
    if len(matches) == 1:
        do_check_in(matches[0], method)
    elif matches:
        st.session_state["checkin_matches"] = [m["id"] for m in matches[:8]]
        st.session_state.pop("last_checkin", None)
    else:
        st.session_state["last_checkin"] = {"ok": False, "name": raw, "msg": "No member matches that ID, phone or name.", "notfound": True}


scan_col, list_col = st.columns([1, 1.25], gap="large")

with scan_col:
    with st.container(border=True):
        mode = st.segmented_control("Input", ["Type / search", "Camera", "Upload image"], default="Type / search", label_visibility="collapsed")

        if mode == "Camera":
            shot = st.camera_input("Point the member's QR pass at the camera", key="cam")
            if shot is not None and st.session_state.get("_last_shot") != shot.file_id:
                st.session_state["_last_shot"] = shot.file_id
                code = decode_qr_image(shot)
                if code:
                    resolve_and_check_in(code, "qr_code")
                else:
                    st.session_state["last_checkin"] = {"ok": False, "name": "", "msg": "Couldn't read a QR code — hold the pass steady and closer, or type the ID.", "notfound": True}
        elif mode == "Upload image":
            up = st.file_uploader("Upload a photo/screenshot of the pass", type=["png", "jpg", "jpeg"], key="qr_upload")
            if up is not None and st.session_state.get("_last_upload") != up.file_id:
                st.session_state["_last_upload"] = up.file_id
                code = decode_qr_image(up)
                if code:
                    resolve_and_check_in(code, "qr_code")
                else:
                    st.session_state["last_checkin"] = {"ok": False, "name": "", "msg": "No QR code found in that image.", "notfound": True}
        else:
            with st.form("manual_checkin", clear_on_submit=True, border=False):
                raw = st.text_input("Member ID, phone or name", placeholder="e.g. GMB-2026-001, 98765 00002 or Priya", label_visibility="collapsed")
                if st.form_submit_button("Check in", type="primary", width="stretch", icon=":material/login:") and raw.strip():
                    resolve_and_check_in(raw.strip(), "manual")

        matches = st.session_state.get("checkin_matches")
        if matches:
            st.caption("Several members match — pick one:")
            for mid in matches:
                m = get_member(c.gym_id, mid)
                if m and st.button(f"{m['full_name']} · {m['member_code']}", key=f"pick_{mid}", width="stretch"):
                    do_check_in(m, "manual")
                    st.session_state.pop("checkin_matches", None)
                    st.rerun()

        res = st.session_state.get("last_checkin")
        if res:
            if res.get("notfound"):
                result_banner("err", "Not found", res["msg"])
            elif res["ok"] and res["status"] in ("expired", "inactive", "no_plan"):
                result_banner("warn", f"{res['name']} checked in · membership {res['status'].replace('_', ' ')}",
                              f"{res['code']} · {expiry_text(res.get('expiry'))}. Please collect the renewal fee.")
            elif res["ok"]:
                extra = f" · {expiry_text(res.get('expiry'))}" if res["status"] == "expiring" else ""
                result_banner("ok", f"Welcome, {res['name']}!", f"{res['code']} · {res['plan']} · checked in at {res['time']}{extra}")
            else:
                result_banner("warn", f"{res['name']} is already checked in", f"{res.get('code', '')} · duplicate check-ins are blocked.")

# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------
with list_col:
    d1, d2 = st.columns([1.3, 1])
    when = d1.segmented_control("Day", ["Today", "Yesterday", "Pick date"], default="Today", label_visibility="collapsed") or "Today"
    if when == "Pick date":
        target = d2.date_input("Date", value=today, max_value=today, label_visibility="collapsed", format="DD/MM/YYYY")
    else:
        target = today if when == "Today" else today - timedelta(days=1)

    records = get_today_attendance(c.gym_id, filter_date=target)
    total_active = sum(1 for m in get_members(c.gym_id) if m["membership_status"] in ("active", "expiring"))
    morning = sum(1 for r in records if str(r.get("check_in_time", "")) < "12")
    stat_cards([
        {"label": f"Check-ins · {format_date_display(target)}", "value": len(records), "icon": "📋", "accent": "cyan"},
        {"label": "Turnout", "value": f"{(len(records) / total_active * 100) if total_active else 0:.0f}%", "icon": "📈", "accent": "purple", "sub": f"of {total_active} active members"},
        {"label": "Morning / evening", "value": f"{morning} / {len(records) - morning}", "icon": "🌗", "accent": "lime"},
    ])

    search = st.text_input("Filter", placeholder="Filter by name or phone", label_visibility="collapsed", icon=":material/filter_list:")
    if search:
        q = search.strip().lower()
        records = [r for r in records if q in r["member_name"].lower() or q in (r.get("member_phone") or "")]
    if records:
        st.dataframe(pd.DataFrame([{
            "Time": format_time_display(r.get("check_in_time")),
            "Member": r["member_name"],
            "ID": r["member_code"],
            "Method": (r.get("method") or "qr_code").replace("_", " ").title(),
        } for r in records]), hide_index=True, width="stretch", height=min(38 + 35 * len(records), 420))
    else:
        empty_state("No check-ins for this day", "Scan a pass or search a member to record one.", "📋")

"""Role-aware home dashboard: owner/desk KPIs, trainer roster health, member progress."""

from __future__ import annotations
from datetime import timedelta

import streamlit as st

from components.ui import (
    unlinked_member_notice,
    ctx, page_header, stat_cards, html_block, esc, badge, chip, empty_state, person_row,
    whatsapp_button, expiry_text, greeting,
)
from components.charts import line_chart
from services.member_service import get_members, get_trainer_member_ids
from services.attendance_service import get_today_attendance, get_member_attendance, get_monthly_attendance_count
from services.renewal_service import get_expiring_memberships
from services.report_service import get_dashboard_stats, get_attendance_trends
from services.workout_service import get_member_workout
from services.diet_service import get_member_diet
from utils.helpers import format_currency
from utils.date_utils import get_ist_today, format_date_display, format_time_display, days_since

c = ctx()


def staff_home() -> None:
    page_header(f"{greeting()}, {c.first_name}", f"Here's what's happening at {c.gym_name} today.", eyebrow=c.role)
    stats = get_dashboard_stats(c.gym_id)

    cards = [
        {"label": "Check-ins today", "value": stats["today_attendance"], "icon": "📋", "accent": "cyan", "sub": "Front desk footfall"},
        {"label": "Active members", "value": stats["active_members"], "icon": "⚡", "accent": "purple", "sub": f"of {stats['total_members']} registered"},
        {"label": "Expiring ≤ 7 days", "value": stats["expiring_7_days"], "icon": "⏳", "accent": "amber", "sub": "Renewals to chase"},
        {"label": "Need a nudge", "value": stats["inactive_members"], "icon": "🔔", "accent": "pink", "sub": "Absent 7+ days"},
    ]
    if c.role in ("owner", "admin"):
        cards.insert(2, {"label": "Revenue this month", "value": format_currency(stats["monthly_revenue"]).replace(".00", ""), "icon": "💰", "accent": "lime",
                         "sub": f"{format_currency(stats['today_revenue']).replace('.00', '')} collected today"})
    stat_cards(cards)

    a1, a2, a3, a4 = st.columns(4)
    a1.page_link("views/attendance.py", label="Check in a member", icon=":material/qr_code_scanner:")
    a2.page_link("views/register.py", label="Register new member", icon=":material/person_add:")
    a3.page_link("views/fees.py", label="Record a payment", icon=":material/payments:")
    a4.page_link("views/renewals.py", label="Renewals", icon=":material/autorenew:")
    st.write("")

    left, right = st.columns([1.15, 1])
    with left:
        with st.container(border=True):
            st.markdown("#### ⏳ Renewals due this week")
            due = get_expiring_memberships(c.gym_id)
            items = due["within_7_days"] + due["expired"][:3]
            if not items:
                empty_state("Nothing due this week", "All memberships are comfortably active.", "🎉")
            for it in items[:6]:
                row, act = st.columns([3, 1.3], vertical_alignment="center")
                with row:
                    kind = "expired" if it["days_remaining"] < 0 else "expiring"
                    person_row(it["member_name"], f"{esc(it['plan_name'])} · {esc(expiry_text(it['expiry_date']))}", badge(kind))
                with act:
                    whatsapp_button(
                        it["phone"],
                        f"Hi {it['member_name']}! Your {it['plan_name']} membership at {c.gym_name} "
                        f"{'has expired' if kind == 'expired' else 'ends on ' + format_date_display(it['expiry_date'])}. "
                        "Renew today to keep your streak going! 💪",
                        "Remind",
                    )
            if items:
                st.page_link("views/renewals.py", label="Open renewals", icon=":material/arrow_forward:")

    with right:
        with st.container(border=True):
            st.markdown("#### 📋 Latest check-ins")
            today = get_today_attendance(c.gym_id)
            if not today:
                empty_state("No check-ins yet today", "They'll show up here as members arrive.", "🌅")
            for r in today[:6]:
                person_row(r["member_name"], f"{chip(r['member_code'])} · {esc(format_time_display(r.get('check_in_time')))}")
                st.write("")

    if c.role in ("owner", "admin"):
        line_chart(get_attendance_trends(c.gym_id, days=14), "date", "count", "Daily check-ins · last 14 days", height=260)


def trainer_home() -> None:
    page_header(f"{greeting()}, Coach {c.first_name}", "Your athletes at a glance.", eyebrow="Trainer")
    my_ids = get_trainer_member_ids(c.gym_id, c.user_id)
    athletes = [m for m in get_members(c.gym_id) if m["id"] in my_ids]
    trained_today = sum(1 for m in athletes if m.get("last_visit") == str(get_ist_today()))
    no_plan = [m for m in athletes if not get_member_workout(m["id"])]
    slipping = [m for m in athletes if days_since(m.get("last_visit")) >= 5]

    stat_cards([
        {"label": "My athletes", "value": len(athletes), "icon": "👥", "accent": "purple"},
        {"label": "Trained today", "value": trained_today, "icon": "🔥", "accent": "lime"},
        {"label": "Without workout plan", "value": len(no_plan), "icon": "📝", "accent": "amber"},
        {"label": "Missing 5+ days", "value": len(slipping), "icon": "🔔", "accent": "pink"},
    ])

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("#### 📝 Needs a workout plan")
            if not no_plan:
                empty_state("Every athlete has a plan", icon="✅")
            for m in no_plan:
                row, act = st.columns([3, 1.2], vertical_alignment="center")
                with row:
                    person_row(m["full_name"], f"{chip(m['member_code'])} · {esc(m['plan_name'])}")
                with act:
                    if st.button("Build plan", key=f"plan_{m['id']}", width="stretch"):
                        st.session_state["coach_member_id"] = m["id"]
                        st.switch_page("views/workout.py")
    with right:
        with st.container(border=True):
            st.markdown("#### 🔔 Haven't trained in a while")
            if not slipping:
                empty_state("Everyone's showing up", icon="💪")
            for m in slipping:
                row, act = st.columns([3, 1.2], vertical_alignment="center")
                last = format_date_display(m["last_visit"]) if m.get("last_visit") else "never"
                with row:
                    person_row(m["full_name"], f"Last visit: <b>{esc(last)}</b>")
                with act:
                    whatsapp_button(m["phone"], f"Hey {m['full_name']}! Coach {c.first_name} here. Missed you at the gym — everything okay? Let's get back on track this week 💪", "Nudge")
    st.page_link("views/my_members.py", label="See all my athletes", icon=":material/arrow_forward:")


def member_home() -> None:
    from services.member_service import get_member
    member = get_member(c.gym_id, c.member_id) if c.member_id else None
    page_header(f"{greeting()}, {c.first_name}", f"Welcome back to {c.gym_name}.", eyebrow="Member")
    if not member:
        unlinked_member_notice()
        return

    history = get_member_attendance(c.gym_id, member["id"], limit=120)
    visit_days = {str(h.get("check_in_date")) for h in history}
    today = get_ist_today()

    streak = 0
    cursor = today if str(today) in visit_days else today - timedelta(days=1)
    while str(cursor) in visit_days:
        streak += 1
        cursor -= timedelta(days=1)

    status = member["membership_status"]
    progress = 0
    if member.get("start_date") and member.get("expiry_date"):
        from datetime import date
        start = date.fromisoformat(str(member["start_date"])[:10])
        end = date.fromisoformat(str(member["expiry_date"])[:10])
        total = max((end - start).days, 1)
        progress = min(max((today - start).days / total, 0), 1) * 100

    html_block(
        f"""
        <div class="gb-hero">
          <div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:flex-start">
            <div>
              <div class="gb-eyebrow">Your membership</div>
              <h2>{esc(member['plan_name'])}</h2>
              <p>{esc(expiry_text(member.get('expiry_date')))}</p>
            </div>
            <div style="text-align:right">{badge(status)}<div style="margin-top:.5rem">{chip(member['member_code'])}</div></div>
          </div>
          <div class="gb-progress"><span style="width:{progress:.0f}%"></span></div>
        </div>
        """
    )
    if status in ("expired", "expiring"):
        st.warning("Your membership needs renewing soon — renew at the front desk to keep access.", icon=":material/schedule:")

    checked_today = str(today) in visit_days
    stat_cards([
        {"label": "Today", "value": "Checked in ✓" if checked_today else "Not yet", "icon": "📍", "accent": "lime" if checked_today else "amber"},
        {"label": "Current streak", "value": f"{streak} day{'s' if streak != 1 else ''}", "icon": "🔥", "accent": "pink"},
        {"label": "Visits this month", "value": get_monthly_attendance_count(c.gym_id, member["id"]), "icon": "📅", "accent": "cyan"},
        {"label": "Total visits", "value": len(history), "icon": "🏆", "accent": "purple"},
    ])

    cells = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        cls = ("on " if str(d) in visit_days else "") + ("today" if i == 0 else "")
        cells.append(f'<span class="{cls}" title="{d.strftime("%d %b")}"></span>')

    left, right = st.columns([1, 1])
    with left:
        with st.container(border=True):
            st.markdown("#### Last 30 days")
            html_block(f'<div class="gb-heat">{"".join(cells)}</div>')
            st.caption("Each square is a day — lit squares are days you trained.")
        st.page_link("views/attendance.py", label="Open my QR pass", icon=":material/qr_code_2:")

    with right:
        with st.container(border=True):
            day = today.strftime("%A")
            st.markdown(f"#### Today's workout · {day}")
            plan = get_member_workout(member["id"])
            todays = (plan or {}).get("schedule", {}).get(day, [])
            if not plan:
                empty_state("No workout plan yet", "Your trainer will assign one soon.", "🏋️")
            elif not todays:
                empty_state("Rest & recovery day", "Hydrate, stretch and sleep well.", "😴")
            else:
                for ex in todays:
                    st.markdown(f"**{ex.get('exercise_name')}** · {ex.get('sets')} × {ex.get('reps')} · rest {ex.get('rest_seconds')}s")
        p1, p2 = st.columns(2)
        p1.page_link("views/workout.py", label="Full week plan", icon=":material/fitness_center:")
        if get_member_diet(member["id"]):
            p2.page_link("views/diet.py", label="My diet plan", icon=":material/restaurant:")


if c.role == "member":
    member_home()
elif c.role == "trainer":
    trainer_home()
else:
    staff_home()

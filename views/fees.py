"""SCREEN 6 – Fee collection, PDF receipts and payment history."""

from __future__ import annotations
from datetime import timedelta

import pandas as pd
import streamlit as st

from components.ui import ctx, page_header, require_role, stat_cards, html_block, esc, badge, chip, empty_state, whatsapp_button, expiry_text, flash
from components.pdf_receipt import generate_receipt_pdf
from services.payment_service import record_payment, get_payments, get_revenue_stats
from services.member_service import get_members
from services.gym_service import get_gym_details
from utils.helpers import format_currency
from utils.date_utils import get_ist_today, format_date_display

require_role("owner", "receptionist")
c = ctx()
page_header("Fees & receipts", "Record payments in seconds and hand out a PDF receipt.", eyebrow="Front desk")
gym = get_gym_details(c.gym_id) or {}


def receipt_bytes(p: dict) -> bytes:
    return generate_receipt_pdf({
        "gym_name": c.gym_name, "gym_address": gym.get("address", ""),
        "receipt_no": p.get("receipt_no"), "payment_date": format_date_display(p.get("payment_date")),
        "member_name": p.get("member_name"), "member_code": p.get("member_code"),
        "plan_name": p.get("plan_name") or "Gym membership", "amount": float(p.get("amount") or 0),
        "payment_method": p.get("payment_method"), "transaction_ref": p.get("transaction_ref"),
        "remarks": p.get("remarks"),
    })


stats = get_revenue_stats(c.gym_id)
stat_cards([
    {"label": "Collected today", "value": format_currency(stats["today"]).replace(".00", ""), "icon": "💵", "accent": "lime"},
    {"label": "This month", "value": format_currency(stats["month"]).replace(".00", ""), "icon": "📈", "accent": "cyan"},
    {"label": "All time", "value": format_currency(stats["total"]).replace(".00", ""), "icon": "💰", "accent": "purple"},
])

tab_record, tab_history = st.tabs([":material/add_card: Record payment", ":material/history: Payment history"])

with tab_record:
    members = get_members(c.gym_id)
    if not members:
        empty_state("No members yet", "Register a member before recording fees.", "👥")
    else:
        by_id = {m["id"]: m for m in members}
        ids = list(by_id)
        preselect = st.session_state.pop("fee_member_id", None)
        pick_l, pick_r = st.columns([1, 1.3], gap="large")
        with pick_l:
            mid = st.selectbox(
                "Member", ids, index=ids.index(preselect) if preselect in ids else None,
                format_func=lambda i: f"{by_id[i]['full_name']} · {by_id[i]['member_code']} · {by_id[i]['phone']}",
                placeholder="Search by name, ID or phone…", key="fee_member",
            )
            if mid:
                m = by_id[mid]
                with st.container(border=True):
                    html_block(
                        f"""<div class="gb-row-title">{esc(m['full_name'])} {badge(m['membership_status'])}</div>
                        <div class="gb-row-meta">{chip(m['member_code'])} · {esc(m['plan_name'])}<br>{esc(expiry_text(m.get('expiry_date')))}</div>"""
                    )
                if m["membership_status"] in ("expired", "expiring"):
                    st.info("This membership is due — use **Renewals** to extend the plan and collect the fee together.", icon=":material/lightbulb:")
                    if st.button("Renew instead", icon=":material/autorenew:"):
                        st.session_state["renew_member_id"] = mid
                        st.switch_page("views/renewals.py")

        with pick_r:
            if not mid:
                empty_state("Pick a member to start", "Use the search box on the left.", "👈")
            else:
                m = by_id[mid]
                with st.form("fee_entry_form", clear_on_submit=True):
                    f1, f2 = st.columns(2)
                    amount = f1.number_input("Amount (₹) *", min_value=1.0, value=1000.0, step=100.0)
                    method = f2.selectbox("Payment method *", ["UPI", "Cash", "Bank Transfer"])
                    f3, f4 = st.columns(2)
                    pay_date = f3.date_input("Payment date", value=get_ist_today(), max_value=get_ist_today(), format="DD/MM/YYYY")
                    ref = f4.text_input("UPI / transaction ref", placeholder="optional")
                    remarks = st.text_input("Remarks", placeholder="e.g. Locker + personal training")
                    submitted = st.form_submit_button("Record payment & create receipt", type="primary", width="stretch", icon=":material/receipt_long:")
                if submitted:
                    ok, err, rec = record_payment(c.gym_id, {
                        "member_id": mid, "amount": amount, "payment_date": pay_date,
                        "payment_method": method, "transaction_ref": ref, "remarks": remarks,
                    })
                    if ok and rec:
                        rec.update({"member_name": m["full_name"], "member_code": m["member_code"], "plan_name": m["plan_name"], "member_phone": m["phone"]})
                        st.session_state["last_receipt"] = rec
                        flash(f"{format_currency(amount)} recorded for {m['full_name']}", "💰")
                        st.rerun()
                    st.error(err or "Could not record the payment.")

    rec = st.session_state.get("last_receipt")
    if rec:
        with st.container(border=True):
            st.markdown(f"**Last receipt · {rec['receipt_no']}** — {format_currency(rec['amount'])} from {rec['member_name']} via {rec['payment_method']}")
            r1, r2, r3 = st.columns(3)
            r1.download_button("Download PDF", receipt_bytes(rec), file_name=f"Receipt_{rec['receipt_no']}.pdf",
                               mime="application/pdf", icon=":material/download:", width="stretch", type="primary")
            with r2:
                whatsapp_button(rec.get("member_phone"),
                                f"Hi {rec['member_name']}, we've received {format_currency(rec['amount'])} via {rec['payment_method']} "
                                f"at {c.gym_name}. Receipt no. {rec['receipt_no']}. Thank you! 🙏", "Send on WhatsApp")
            if r3.button("Dismiss", width="stretch"):
                st.session_state.pop("last_receipt", None)
                st.rerun()

with tab_history:
    h1, h2 = st.columns([2, 1])
    period = h1.segmented_control("Period", ["Last 7 days", "This month", "Last 90 days", "All time"], default="This month", label_visibility="collapsed") or "This month"
    method_filter = h2.multiselect("Method", ["UPI", "Cash", "Bank Transfer"], placeholder="All methods", label_visibility="collapsed")

    today = get_ist_today()
    start = {"Last 7 days": today - timedelta(days=6), "This month": today.replace(day=1), "Last 90 days": today - timedelta(days=89)}.get(period)
    payments = get_payments(c.gym_id, start_date=start)
    if method_filter:
        payments = [p for p in payments if p.get("payment_method") in method_filter]

    if not payments:
        empty_state("No payments in this period", icon="🧾")
    else:
        total = sum(float(p.get("amount") or 0) for p in payments)
        by_method = {}
        for p in payments:
            by_method[p.get("payment_method")] = by_method.get(p.get("payment_method"), 0) + float(p.get("amount") or 0)
        st.caption(f"**{len(payments)} payments · {format_currency(total)}** — " + " · ".join(f"{k}: {format_currency(v)}" for k, v in sorted(by_method.items())))

        df = pd.DataFrame([{
            "Date": pd.to_datetime(p.get("payment_date")),
            "Receipt": p.get("receipt_no"),
            "Member": p.get("member_name"),
            "Amount": float(p.get("amount") or 0),
            "Method": p.get("payment_method"),
            "Reference": p.get("transaction_ref") or "—",
        } for p in payments])
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            "Date": st.column_config.DateColumn(format="DD MMM YYYY"),
            "Amount": st.column_config.NumberColumn(format="₹%d"),
        })

        e1, e2 = st.columns([2, 1], vertical_alignment="bottom")
        options = {p["id"]: p for p in payments}
        pick = e1.selectbox("Re-issue a receipt", list(options), format_func=lambda i: f"{options[i]['receipt_no']} · {options[i]['member_name']} · {format_currency(options[i]['amount'])}")
        e2.download_button("Download receipt", receipt_bytes(options[pick]), file_name=f"Receipt_{options[pick]['receipt_no']}.pdf",
                           mime="application/pdf", icon=":material/download:", width="stretch")
        st.download_button("Export CSV", df.to_csv(index=False).encode(), file_name=f"payments_{period.lower().replace(' ', '_')}.csv", mime="text/csv", icon=":material/table_view:")

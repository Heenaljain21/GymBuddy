"""SCREEN 6 – FEES ENTRY & RECEIPT GENERATOR

Enables front desk and owners to record fee payments in Indian Rupees (₹),
generate official PDF receipts, and audit historical financial transactions.
"""

from __future__ import annotations
import os
import sys
from datetime import date, timedelta
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state
from utils.permissions import require_role
from utils.helpers import format_currency
from utils.date_utils import get_ist_today, format_date_display
from services.payment_service import record_payment, get_payments, get_revenue_stats
from services.member_service import get_members, search_members
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.dashboard_cards import render_stat_cards_row
from components.pdf_receipt import generate_receipt_pdf
from components.notifications import show_success, show_error, show_info


def load_css() -> None:
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


init_session_state()
load_css()
require_role(["owner", "receptionist", "admin"])
render_sidebar()

gym_id = st.session_state.get("gym_id", "00000000-0000-0000-0000-000000000001")
gym_name = st.session_state.get("gym_name", "FitZone Premium Gym")

render_navbar("Fees Entry & Receipts", "Record Member Collections & Issue Tax Invoices")

# Revenue stats
stats = get_revenue_stats(gym_id)
cards = [
    {"title": "Today's Collections", "value": format_currency(stats["today"]), "icon": "💵", "color": "lime"},
    {"title": "Monthly Collections", "value": format_currency(stats["month"]), "icon": "📈", "color": "cyan"},
    {"title": "Total Platform Fees", "value": format_currency(stats["total"]), "icon": "💰", "color": "purple"},
]
render_stat_cards_row(cards)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

tab_record, tab_history = st.tabs(["💳 Record Fee Payment", "📜 Payment History & Audit"])

# ==========================================
# 1. RECORD PAYMENT TAB
# ==========================================
with tab_record:
    col_search, col_form = st.columns([1, 1.4])

    with col_search:
        st.markdown("#### 1. Select Member")
        all_m = get_members(gym_id)
        search_query = st.text_input("🔍 Search member by name, phone or code", placeholder="e.g. Priya or 9876500002")
        filtered_m = search_members(gym_id, search_query) if search_query else all_m

        selected_member = None
        if filtered_m:
            member_dict = {f"{m['full_name']} | {m.get('member_code', '-')} | {m.get('phone')}": m for m in filtered_m}
            sel_key = st.selectbox("Choose Member", options=list(member_dict.keys()))
            selected_member = member_dict[sel_key]
        else:
            st.warning("No member found matching query.")

        if selected_member:
            st.markdown(
                f"""
                <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 14px; padding: 1.25rem; margin-top: 1rem;">
                    <div style="font-size: 0.78rem; color: #06D6C9; font-weight: 700;">CURRENT MEMBERSHIP</div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #F8FAFC; margin-top: 2px;">{selected_member['full_name']}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">
                        Plan: <b>{selected_member.get('plan_name', 'Standard')}</b><br>
                        Status: <b>{selected_member.get('membership_status', 'Active').upper()}</b><br>
                        Expires on: <b>{format_date_display(selected_member.get('expiry_date'))}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_form:
        st.markdown("#### 2. Payment Transaction Details")
        if not selected_member:
            st.info("Select a member on the left to proceed with fee entry.")
        else:
            with st.form("fee_entry_form"):
                amount = st.number_input("Fee Amount (₹) *", min_value=100.0, value=2000.0, step=100.0)
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    pay_method = st.selectbox("Payment Method *", options=["UPI", "Cash", "Bank Transfer"])
                with col_m2:
                    pay_date = st.date_input("Payment Date", value=get_ist_today(), max_value=get_ist_today())

                txn_ref = st.text_input("Transaction Reference / UTR Number", placeholder="e.g. UPI/2026/99812")
                remarks = st.text_area("Remarks / Notes", placeholder="e.g. Renewal fee + locker charges")

                submitted = st.form_submit_button("💰 Record Payment & Issue Receipt", use_container_width=True)

                if submitted:
                    payment_data = {
                        "member_id": selected_member["id"],
                        "amount": amount,
                        "payment_date": pay_date,
                        "payment_method": pay_method,
                        "transaction_ref": txn_ref,
                        "remarks": remarks,
                    }
                    with st.spinner("Recording transaction..."):
                        ok, err, new_payment = record_payment(gym_id, payment_data)
                        if ok and new_payment:
                            show_success(
                                f"Payment of {format_currency(amount)} recorded successfully!",
                                f"Receipt Number: {new_payment.get('receipt_no')}"
                            )

                            # Generate PDF
                            pdf_payload = {
                                "gym_name": gym_name,
                                "receipt_no": new_payment.get("receipt_no"),
                                "payment_date": format_date_display(pay_date),
                                "member_name": selected_member.get("full_name"),
                                "member_code": selected_member.get("member_code"),
                                "plan_name": selected_member.get("plan_name", "Gym Membership"),
                                "amount": amount,
                                "payment_method": pay_method,
                                "transaction_ref": txn_ref,
                            }
                            pdf_bytes = generate_receipt_pdf(pdf_payload)

                            st.download_button(
                                label="📄 Download Official PDF Receipt",
                                data=pdf_bytes,
                                file_name=f"Receipt_{new_payment.get('receipt_no')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )
                        else:
                            show_error(err or "Failed to record payment.")

# ==========================================
# 2. PAYMENT HISTORY & AUDIT TAB
# ==========================================
with tab_history:
    col_hf1, col_hf2 = st.columns([2, 1])
    with col_hf1:
        hist_filter = st.radio(
            "Filter Period",
            options=["All Time", "This Month", "Last 7 Days"],
            horizontal=True,
        )

    today = get_ist_today()
    if hist_filter == "This Month":
        start_d = today.replace(day=1)
    elif hist_filter == "Last 7 Days":
        start_d = today - timedelta(days=7)
    else:
        start_d = None

    all_payments = get_payments(gym_id, start_date=start_d)

    if all_payments:
        display_rows = []
        for p in all_payments:
            display_rows.append({
                "Receipt No": p.get("receipt_no", "-"),
                "Date": format_date_display(p.get("payment_date")),
                "Member": p.get("member_name"),
                "Amount": format_currency(p.get("amount")),
                "Method": p.get("payment_method"),
                "Reference": p.get("transaction_ref") or "-",
            })

        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        # Download individual receipt selector
        with st.expander("📥 Generate / Re-download PDF Receipt for Any Transaction"):
            receipt_options = {f"{p.get('receipt_no')} - {p.get('member_name')} ({format_currency(p.get('amount'))})": p for p in all_payments}
            sel_rec_label = st.selectbox("Select Transaction", options=list(receipt_options.keys()))
            sel_rec = receipt_options[sel_rec_label]

            pdf_payload = {
                "gym_name": gym_name,
                "receipt_no": sel_rec.get("receipt_no"),
                "payment_date": format_date_display(sel_rec.get("payment_date")),
                "member_name": sel_rec.get("member_name"),
                "member_code": sel_rec.get("member_code"),
                "plan_name": "Gym Membership",
                "amount": float(sel_rec.get("amount", 0.0)),
                "payment_method": sel_rec.get("payment_method"),
                "transaction_ref": sel_rec.get("transaction_ref"),
            }
            pdf_bytes = generate_receipt_pdf(pdf_payload)
            st.download_button(
                label=f"📄 Download PDF for {sel_rec.get('receipt_no')}",
                data=pdf_bytes,
                file_name=f"Receipt_{sel_rec.get('receipt_no')}.pdf",
                mime="application/pdf",
            )
    else:
        st.info("No payment records found.")

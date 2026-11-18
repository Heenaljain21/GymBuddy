"""SCREEN 2 – Online joining: enroll a member, pick a plan, take the first fee, issue a QR pass."""

from __future__ import annotations
from datetime import timedelta

import streamlit as st

from components.ui import ctx, page_header, require_role, html_block, esc, empty_state, whatsapp_button, kv_table, flash
from components.qr_components import render_member_pass
from components.pdf_receipt import generate_receipt_pdf
from services.gym_service import get_membership_plans
from services.member_service import register_member
from services.payment_service import get_member_payments
from utils.helpers import format_currency, format_phone
from utils.date_utils import get_ist_today, format_date_display
from utils.validators import validate_member_form

require_role("owner", "receptionist")
c = ctx()
page_header("New member", "Enroll a member and hand them a QR pass in under a minute.", eyebrow="Front desk")

plans = get_membership_plans(c.gym_id, active_only=True)
if not plans:
    empty_state("No membership plans configured", "Ask the platform admin or gym owner to add plans first.", "📦")
    st.stop()

# ---------------------------------------------------------------------------
# Success screen
# ---------------------------------------------------------------------------
new_member = st.session_state.get("registered_member")
if new_member:
    st.success(f"**{new_member['full_name']}** is now a member! Member ID **{new_member['member_code']}**.", icon=":material/celebration:")
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        render_member_pass(new_member["member_code"], new_member["full_name"], c.gym_name, key="new")
    with right:
        with st.container(border=True):
            st.markdown("#### Member summary")
            kv_table([
                ("Member ID", new_member["member_code"]),
                ("Phone", format_phone(new_member.get("phone"))),
                ("Email", new_member.get("email") or "—"),
                ("Plan", new_member.get("plan_name", "—")),
                ("Valid until", format_date_display(new_member.get("expiry_date"))),
                ("Paid", format_currency(new_member.get("amount_paid", 0))),
            ])
        pays = get_member_payments(c.gym_id, new_member["id"])
        if pays:
            p = pays[0]
            st.download_button(
                "Download receipt (PDF)",
                data=generate_receipt_pdf({
                    "gym_name": c.gym_name, "receipt_no": p.get("receipt_no"),
                    "payment_date": format_date_display(p.get("payment_date")),
                    "member_name": new_member["full_name"], "member_code": new_member["member_code"],
                    "plan_name": new_member.get("plan_name"), "amount": p.get("amount"),
                    "payment_method": p.get("payment_method"), "transaction_ref": p.get("transaction_ref"),
                    "remarks": p.get("remarks"),
                }),
                file_name=f"Receipt_{p.get('receipt_no')}.pdf", mime="application/pdf",
                icon=":material/receipt_long:", width="stretch",
            )
        whatsapp_button(
            new_member.get("phone"),
            f"Welcome to {c.gym_name}, {new_member['full_name']}! 🎉 Your member ID is {new_member['member_code']}. "
            f"Your {new_member.get('plan_name')} plan is valid till {format_date_display(new_member.get('expiry_date'))}. "
            "Show your QR pass at the desk to check in. See you on the floor! 💪",
            "Send welcome message",
        )
        st.write("")
        if st.button("Register another member", icon=":material/person_add:", type="primary", width="stretch"):
            st.session_state.pop("registered_member", None)
            st.rerun()
    st.stop()

# ---------------------------------------------------------------------------
# Step 1 – plan
# ---------------------------------------------------------------------------
st.markdown("##### 1 · Choose a plan")
plan_by_name = {p["name"]: p for p in plans}
chosen = st.segmented_control(
    "Plan", list(plan_by_name), default=list(plan_by_name)[0], label_visibility="collapsed", key="reg_plan",
) or list(plan_by_name)[0]
plan = plan_by_name[chosen]
start = get_ist_today()
end = start + timedelta(days=int(plan["duration_days"]))
per_month = float(plan["price"]) / max(int(plan["duration_days"]) / 30, 1)
html_block(
    f"""
    <div class="gb-hero" style="padding:1rem 1.25rem">
      <div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:center">
        <div><div class="gb-eyebrow">{int(plan['duration_days'])} days</div>
          <h2 style="margin:.1rem 0">{esc(plan['name'])}</h2>
          <p>{esc(plan.get('description') or '')}</p></div>
        <div style="text-align:right"><div class="gb-display" style="font-size:1.9rem;font-weight:800;color:#fff">{esc(format_currency(plan['price']).replace('.00', ''))}</div>
          <div style="color:var(--gb-muted);font-size:.82rem">≈ {esc(format_currency(per_month).replace('.00', ''))}/month · valid {esc(format_date_display(start))} → {esc(format_date_display(end))}</div></div>
      </div>
    </div>
    """
)

# ---------------------------------------------------------------------------
# Step 2 – details & payment
# ---------------------------------------------------------------------------
st.markdown("##### 2 · Member details & first payment")
with st.form("member_registration_form", clear_on_submit=False):
    a, b = st.columns(2)
    full_name = a.text_input("Full name *", placeholder="e.g. Vikram Malhotra")
    phone = b.text_input("Mobile number *", placeholder="10-digit mobile", max_chars=14)
    email = a.text_input("Email", placeholder="optional")
    emergency_contact = b.text_input("Emergency contact", placeholder="optional", max_chars=14)
    g1, g2 = a.columns(2)
    gender = g1.selectbox("Gender", ["Male", "Female", "Other"])
    age = g2.number_input("Age", min_value=12, max_value=90, value=25)
    address = b.text_input("Area / address", placeholder="e.g. Indiranagar, Bengaluru")

    st.markdown("**Payment**")
    p1, p2, p3 = st.columns(3)
    amount = p1.number_input("Amount collected (₹)", value=float(plan["price"]), min_value=0.0, step=100.0, key=f"amt_{plan['id']}")
    method = p2.selectbox("Payment method", ["UPI", "Cash", "Bank Transfer"])
    ref = p3.text_input("UPI / transaction ref", placeholder="optional")

    submit = st.form_submit_button("Complete registration & issue pass", type="primary", width="stretch", icon=":material/how_to_reg:")

if submit:
    payload = {
        "full_name": full_name, "phone": phone, "email": email, "age": age, "gender": gender,
        "address": address, "emergency_contact": emergency_contact,
        "plan_id": plan["id"], "duration_days": plan["duration_days"], "amount_paid": amount,
        "payment_method": method, "transaction_ref": ref, "start_date": start,
    }
    valid, errors = validate_member_form(payload)
    if not valid:
        st.error("Please fix the following:\n\n" + "\n".join(f"- {e}" for e in errors), icon=":material/error:")
    else:
        with st.spinner("Registering member…"):
            ok, err, created = register_member(c.gym_id, payload)
        if ok and created:
            created.update({"plan_name": plan["name"], "amount_paid": amount})
            st.session_state["registered_member"] = created
            flash(f"{created['full_name']} registered", "🎉")
            st.rerun()
        st.error(err or "Registration failed.", icon=":material/error:")

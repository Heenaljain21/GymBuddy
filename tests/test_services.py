"""Integration and domain service tests for GYM BUDDY using unittest."""

import sys
import os
from datetime import date
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import get_supabase_client, init_session_state
from services.auth_service import sign_in, is_authenticated
from services.gym_service import get_all_gyms, get_membership_plans
from services.member_service import get_members, register_member, get_member_by_qr
from services.attendance_service import check_in, is_already_checked_in, get_today_attendance
from services.payment_service import record_payment, get_payments, get_revenue_stats
from services.renewal_service import get_expiring_memberships, renew_membership
from services.workout_service import get_member_workout, save_workout_plan
from services.diet_service import get_member_diet, save_diet_plan
from services.inactivity_service import get_inactive_members
from services.report_service import get_dashboard_stats


GYM_ID = "00000000-0000-0000-0000-000000000001"


class TestServices(unittest.TestCase):

    def setUp(self):
        init_session_state()

    def test_auth_service(self):
        ok, err = sign_in("owner@fitzone.in", "owner123")
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(is_authenticated())

    def test_auth_rejects_bad_credentials(self):
        ok, err = sign_in("owner@fitzone.in", "wrong-password")
        self.assertFalse(ok)
        self.assertIn("invalid", err.lower())
        ok, _ = sign_in("nobody@example.com", "owner123")
        self.assertFalse(ok)

    def test_sign_up_validation(self):
        from services.auth_service import sign_up
        self.assertFalse(sign_up("A", "x@example.com", "longenough", "longenough")[0])
        self.assertFalse(sign_up("New Member", "not-an-email", "longenough", "longenough")[0])
        self.assertFalse(sign_up("New Member", "x@example.com", "short", "short")[0])
        ok, msg = sign_up("New Member", "x@example.com", "longenough", "different1")
        self.assertFalse(ok)
        self.assertIn("match", msg)
        ok, msg = sign_up("New Member", "x@example.com", "longenough", "longenough")
        self.assertFalse(ok)  # demo mode never creates accounts
        self.assertIn("demo", msg.lower())

    def test_member_login_links_own_member_record(self):
        import streamlit as st
        ok, _ = sign_in("amit@gmail.com", "member123")
        self.assertTrue(ok)
        self.assertEqual(st.session_state["user_role"], "member")
        self.assertEqual(st.session_state["member_id"], "bbbb0001-0000-0000-0000-000000000001")

    def test_gym_and_plans(self):
        gyms = get_all_gyms()
        self.assertGreaterEqual(len(gyms), 1)
        self.assertEqual(gyms[0]["name"], "FitZone Premium Gym")

        plans = get_membership_plans(GYM_ID)
        self.assertGreaterEqual(len(plans), 4)
        plan_names = [p["name"] for p in plans]
        self.assertIn("Monthly Starter", plan_names)
        self.assertIn("Annual Champion", plan_names)

    def test_member_registration_and_search(self):
        payload = {
            "full_name": "Test Athlete Sharma",
            "phone": "9811122233",
            "email": "test.athlete@gmail.com",
            "age": 27,
            "gender": "Male",
            "plan_id": "aaaa0001-0000-0000-0000-000000000001",
            "duration_days": 30,
            "amount_paid": 1800.0,
            "payment_method": "UPI",
            "transaction_ref": "UPI/TEST/001",
        }
        ok, err, new_m = register_member(GYM_ID, payload)
        self.assertTrue(ok)
        self.assertIsNotNone(new_m)
        self.assertTrue(new_m["member_code"].startswith("GMB-"))

        # Resolve by QR
        resolved = get_member_by_qr(GYM_ID, new_m["member_code"])
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["full_name"], "Test Athlete Sharma")

    def test_attendance_and_duplicate_prevention(self):
        members = get_members(GYM_ID)
        test_member = members[0]
        mid = test_member["id"]

        # First check-in or verify status
        already = is_already_checked_in(GYM_ID, mid)
        if not already:
            ok, msg, rec = check_in(GYM_ID, mid, method="qr_code")
            self.assertTrue(ok)
            self.assertIsNotNone(rec)

        # Duplicate check-in on same day should be prevented
        dup_ok, dup_msg, _ = check_in(GYM_ID, mid, method="qr_code")
        self.assertFalse(dup_ok)
        self.assertIn("already checked in", dup_msg.lower())

    def test_payment_service(self):
        members = get_members(GYM_ID)
        mid = members[0]["id"]
        p_data = {
            "member_id": mid,
            "amount": 2500.0,
            "payment_date": str(date.today()),
            "payment_method": "UPI",
            "transaction_ref": "UTR9991122",
            "remarks": "Test fee entry",
        }
        ok, err, p_rec = record_payment(GYM_ID, p_data)
        self.assertTrue(ok)
        self.assertTrue(p_rec["receipt_no"].startswith("REC-"))

        stats = get_revenue_stats(GYM_ID)
        self.assertGreater(stats["total"], 0)

    def test_renewal_service(self):
        members = get_members(GYM_ID)
        mid = members[0]["id"]
        plans = get_membership_plans(GYM_ID)
        new_plan = plans[1]

        ok, err = renew_membership(
            gym_id=GYM_ID,
            member_id=mid,
            new_plan_id=new_plan["id"],
            amount_paid=new_plan["price"],
            payment_method="UPI",
            transaction_ref="RENEW-TEST",
        )
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_workout_and_diet(self):
        m1_id = "bbbb0001-0000-0000-0000-000000000001"

        wp = get_member_workout(m1_id)
        self.assertIsNotNone(wp)
        self.assertIn("schedule", wp)
        self.assertGreater(len(wp["exercises"]), 0)

        dp = get_member_diet(m1_id)
        self.assertIsNotNone(dp)
        self.assertIn("meals", dp)
        self.assertIn("Breakfast", dp["meals"])

    def test_inactivity_threshold_is_respected(self):
        loose = get_inactive_members(GYM_ID, threshold_days=7)["all_inactive"]
        strict = get_inactive_members(GYM_ID, threshold_days=30)["all_inactive"]
        self.assertGreater(len(loose), len(strict))
        self.assertTrue(all(m["days_inactive"] >= 30 for m in strict))

    def test_renewal_extends_from_current_end_date(self):
        from datetime import timedelta
        member = next(m for m in get_members(GYM_ID) if m["full_name"] == "Rohan Gupta")  # annual plan, far from expiry
        old_end = date.fromisoformat(member["expiry_date"])
        monthly = next(p for p in get_membership_plans(GYM_ID) if p["duration_days"] == 30)
        ok, err = renew_membership(GYM_ID, member["id"], monthly["id"], monthly["price"])
        self.assertTrue(ok, err)
        renewed = next(m for m in get_members(GYM_ID) if m["id"] == member["id"])
        self.assertEqual(date.fromisoformat(renewed["expiry_date"]), old_end + timedelta(days=30))

    def test_plans_sorted_by_price(self):
        prices = [p["price"] for p in get_membership_plans(GYM_ID)]
        self.assertEqual(prices, sorted(prices))

    def test_qr_pass_round_trip(self):
        import io
        from components.qr_components import generate_qr_png, decode_qr_image
        self.assertEqual(decode_qr_image(io.BytesIO(generate_qr_png("GMB-2026-004"))), "GMB-2026-004")
        self.assertEqual(get_member_by_qr(GYM_ID, "gmb-2026-004")["full_name"], "Sneha Reddy")

    def test_inactivity_and_reporting(self):
        inactives = get_inactive_members(GYM_ID)
        self.assertIn("7_to_14_days", inactives)
        self.assertIn("never_attended", inactives)

        report = get_dashboard_stats(GYM_ID)
        self.assertGreater(report["total_members"], 0)
        self.assertIn("monthly_revenue", report)


if __name__ == "__main__":
    unittest.main()

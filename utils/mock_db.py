"""Local high-fidelity database simulator for GYM BUDDY.

Provides an in-memory Supabase-compatible interface mimicking query chaining:
.table().select().eq().execute()
Pre-seeded with realistic Indian demo data for out-of-the-box demonstration.
"""

from __future__ import annotations
import copy
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
import uuid

# In-memory storage dictionary
_GLOBAL_STORE: Dict[str, List[Dict[str, Any]]] = {}


def _init_seed_data():
    global _GLOBAL_STORE
    if _GLOBAL_STORE:
        return

    today = date.today()
    gym_id = "00000000-0000-0000-0000-000000000001"
    owner_id = "11111111-1111-1111-1111-111111111111"
    receptionist_id = "22222222-2222-2222-2222-222222222222"
    trainer_id = "33333333-3333-3333-3333-333333333333"
    member_user_id = "44444444-4444-4444-4444-444444444444"

    _GLOBAL_STORE["gyms"] = [
        {
            "id": gym_id,
            "name": "FitZone Premium Gym",
            "slug": "fitzone-indiranagar",
            "tagline": "Transform Your Physique",
            "phone": "9876543210",
            "email": "contact@fitzonegym.in",
            "address": "12th Main Road, Indiranagar, Bengaluru, Karnataka 560038",
            "city": "Bengaluru",
            "state": "Karnataka",
            "currency": "INR",
            "inactivity_threshold_days": 14,
            "is_active": True,
        }
    ]

    _GLOBAL_STORE["profiles"] = [
        {"id": "00000000-0000-0000-0000-000000000000", "gym_id": gym_id, "role": "admin", "full_name": "Platform Admin", "email": "admin@gymbuddy.io", "phone": "9999900000"},
        {"id": owner_id, "gym_id": gym_id, "role": "owner", "full_name": "Rajesh Kumar", "email": "owner@fitzone.in", "phone": "9876543210"},
        {"id": receptionist_id, "gym_id": gym_id, "role": "receptionist", "full_name": "Pooja Sharma", "email": "reception@fitzone.in", "phone": "9876543211"},
        {"id": trainer_id, "gym_id": gym_id, "role": "trainer", "full_name": "Vikram Singh", "email": "vikram@fitzone.in", "phone": "9876543212"},
        {"id": member_user_id, "gym_id": gym_id, "role": "member", "full_name": "Amit Sharma", "email": "amit@gmail.com", "phone": "9876500001"},
    ]

    plan_monthly = "aaaa0001-0000-0000-0000-000000000001"
    plan_quarterly = "aaaa0002-0000-0000-0000-000000000002"
    plan_half_yearly = "aaaa0003-0000-0000-0000-000000000003"
    plan_yearly = "aaaa0004-0000-0000-0000-000000000004"

    _GLOBAL_STORE["membership_plans"] = [
        {"id": plan_monthly, "gym_id": gym_id, "name": "Monthly Starter", "duration_days": 30, "price": 1800.0, "description": "Standard 1 month gym access", "is_active": True},
        {"id": plan_quarterly, "gym_id": gym_id, "name": "Quarterly Fitness", "duration_days": 90, "price": 4500.0, "description": "3 months access with cardio", "is_active": True},
        {"id": plan_half_yearly, "gym_id": gym_id, "name": "Half-Yearly Transformation", "duration_days": 180, "price": 8000.0, "description": "6 months full access + steam", "is_active": True},
        {"id": plan_yearly, "gym_id": gym_id, "name": "Annual Champion", "duration_days": 365, "price": 14000.0, "description": "12 months VIP access + personal trainer session", "is_active": True},
    ]

    m1_id = "bbbb0001-0000-0000-0000-000000000001"
    m2_id = "bbbb0002-0000-0000-0000-000000000002"
    m3_id = "bbbb0003-0000-0000-0000-000000000003"
    m4_id = "bbbb0004-0000-0000-0000-000000000004"
    m5_id = "bbbb0005-0000-0000-0000-000000000005"
    m6_id = "bbbb0006-0000-0000-0000-000000000006"
    m7_id = "bbbb0007-0000-0000-0000-000000000007"
    m8_id = "bbbb0008-0000-0000-0000-000000000008"

    _GLOBAL_STORE["members"] = [
        {"id": m1_id, "gym_id": gym_id, "user_id": member_user_id, "member_code": "GMB-2026-001", "full_name": "Amit Sharma", "phone": "9876500001", "email": "amit@gmail.com", "age": 28, "gender": "Male", "address": "Indiranagar, Bengaluru", "qr_code_data": "GMB-2026-001", "is_active": True},
        {"id": m2_id, "gym_id": gym_id, "user_id": None, "member_code": "GMB-2026-002", "full_name": "Priya Patel", "phone": "9876500002", "email": "priya.p@gmail.com", "age": 26, "gender": "Female", "address": "Koramangala, Bengaluru", "qr_code_data": "GMB-2026-002", "is_active": True},
        {"id": m3_id, "gym_id": gym_id, "user_id": None, "member_code": "GMB-2026-003", "full_name": "Rahul Verma", "phone": "9876500003", "email": "rahul.v@yahoo.com", "age": 32, "gender": "Male", "address": "HSR Layout, Bengaluru", "qr_code_data": "GMB-2026-003", "is_active": True},
        {"id": m4_id, "gym_id": gym_id, "user_id": None, "member_code": "GMB-2026-004", "full_name": "Sneha Reddy", "phone": "9876500004", "email": "sneha.r@gmail.com", "age": 24, "gender": "Female", "address": "Whitefield, Bengaluru", "qr_code_data": "GMB-2026-004", "is_active": True},
        {"id": m5_id, "gym_id": gym_id, "user_id": None, "member_code": "GMB-2026-005", "full_name": "Rohan Gupta", "phone": "9876500005", "email": "rohan.g@gmail.com", "age": 30, "gender": "Male", "address": "BTM Layout, Bengaluru", "qr_code_data": "GMB-2026-005", "is_active": True},
        {"id": m6_id, "gym_id": gym_id, "user_id": None, "member_code": "GMB-2026-006", "full_name": "Ananya Iyer", "phone": "9876500006", "email": "ananya.i@outlook.com", "age": 29, "gender": "Female", "address": "Jayanagar, Bengaluru", "qr_code_data": "GMB-2026-006", "is_active": True},
        {"id": m7_id, "gym_id": gym_id, "user_id": None, "member_code": "GMB-2026-007", "full_name": "Karan Malhotra", "phone": "9876500007", "email": "karan.m@gmail.com", "age": 35, "gender": "Male", "address": "Indiranagar, Bengaluru", "qr_code_data": "GMB-2026-007", "is_active": True},
        {"id": m8_id, "gym_id": gym_id, "user_id": None, "member_code": "GMB-2026-008", "full_name": "Deepika Joshi", "phone": "9876500008", "email": "deepika.j@gmail.com", "age": 27, "gender": "Female", "address": "Marathahalli, Bengaluru", "qr_code_data": "GMB-2026-008", "is_active": False},
    ]

    _GLOBAL_STORE["member_memberships"] = [
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m1_id, "plan_id": plan_quarterly, "start_date": str(today - timedelta(days=30)), "end_date": str(today + timedelta(days=60)), "status": "active", "amount_paid": 4500.0},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m2_id, "plan_id": plan_monthly, "start_date": str(today - timedelta(days=26)), "end_date": str(today + timedelta(days=4)), "status": "active", "amount_paid": 1800.0},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m3_id, "plan_id": plan_half_yearly, "start_date": str(today - timedelta(days=168)), "end_date": str(today + timedelta(days=12)), "status": "active", "amount_paid": 8000.0},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m4_id, "plan_id": plan_monthly, "start_date": str(today - timedelta(days=35)), "end_date": str(today - timedelta(days=5)), "status": "expired", "amount_paid": 1800.0},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m5_id, "plan_id": plan_yearly, "start_date": str(today - timedelta(days=100)), "end_date": str(today + timedelta(days=265)), "status": "active", "amount_paid": 14000.0},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m6_id, "plan_id": plan_quarterly, "start_date": str(today - timedelta(days=80)), "end_date": str(today + timedelta(days=10)), "status": "active", "amount_paid": 4500.0},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m7_id, "plan_id": plan_monthly, "start_date": str(today - timedelta(days=20)), "end_date": str(today + timedelta(days=10)), "status": "active", "amount_paid": 1800.0},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m8_id, "plan_id": plan_monthly, "start_date": str(today - timedelta(days=45)), "end_date": str(today - timedelta(days=15)), "status": "expired", "amount_paid": 1800.0},
    ]

    _GLOBAL_STORE["attendance"] = [
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m1_id, "check_in_date": str(today), "check_in_time": "06:45:00", "method": "qr_code"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m2_id, "check_in_date": str(today), "check_in_time": "07:15:00", "method": "qr_code"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m3_id, "check_in_date": str(today), "check_in_time": "08:00:00", "method": "manual"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m1_id, "check_in_date": str(today - timedelta(days=1)), "check_in_time": "06:50:00", "method": "qr_code"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m2_id, "check_in_date": str(today - timedelta(days=1)), "check_in_time": "07:10:00", "method": "qr_code"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m3_id, "check_in_date": str(today - timedelta(days=2)), "check_in_time": "08:15:00", "method": "qr_code"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m7_id, "check_in_date": str(today - timedelta(days=18)), "check_in_time": "18:30:00", "method": "qr_code"},
    ]

    _GLOBAL_STORE["payments"] = [
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m1_id, "amount": 4500.0, "payment_date": str(today - timedelta(days=30)), "payment_method": "UPI", "transaction_ref": "UPI/2026/09871", "receipt_no": "REC-2026-0001"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m2_id, "amount": 1800.0, "payment_date": str(today - timedelta(days=26)), "payment_method": "UPI", "transaction_ref": "UPI/2026/09942", "receipt_no": "REC-2026-0002"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m3_id, "amount": 8000.0, "payment_date": str(today - timedelta(days=168)), "payment_method": "Bank Transfer", "transaction_ref": "NEFT9823145", "receipt_no": "REC-2026-0003"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m5_id, "amount": 14000.0, "payment_date": str(today - timedelta(days=100)), "payment_method": "Cash", "transaction_ref": "", "receipt_no": "REC-2026-0004"},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m1_id, "amount": 1500.0, "payment_date": str(today), "payment_method": "UPI", "transaction_ref": "UPI/2026/11883", "receipt_no": "REC-2026-0005"},
    ]

    _GLOBAL_STORE["trainer_assignments"] = [
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "trainer_id": trainer_id, "member_id": m1_id, "assigned_date": str(today - timedelta(days=30))},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "trainer_id": trainer_id, "member_id": m2_id, "assigned_date": str(today - timedelta(days=25))},
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "trainer_id": trainer_id, "member_id": m3_id, "assigned_date": str(today - timedelta(days=20))},
    ]

    wp_id = "cccc0001-0000-0000-0000-000000000001"
    _GLOBAL_STORE["workout_plans"] = [
        {"id": wp_id, "gym_id": gym_id, "member_id": m1_id, "trainer_id": trainer_id, "title": "Muscle Hypertrophy & Strength", "description": "Push-Pull-Legs 6-day split focusing on progressive overload", "is_active": True}
    ]

    _GLOBAL_STORE["workout_exercises"] = [
        {"id": str(uuid.uuid4()), "plan_id": wp_id, "day_of_week": "Monday", "exercise_name": "Barbell Bench Press", "sets": 4, "reps": "8-10", "rest_seconds": 90, "instructions": "Keep shoulder blades retracted and elbows tucked at 45 degrees", "trainer_notes": "Warm up with 20kg bar first"},
        {"id": str(uuid.uuid4()), "plan_id": wp_id, "day_of_week": "Monday", "exercise_name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12", "rest_seconds": 60, "instructions": "Full stretch at bottom, squeeze chest at peak", "trainer_notes": "Use 18kg dumbbells"},
        {"id": str(uuid.uuid4()), "plan_id": wp_id, "day_of_week": "Tuesday", "exercise_name": "Barbell Deadlift", "sets": 4, "reps": "6-8", "rest_seconds": 120, "instructions": "Neutral spine, push through heels", "trainer_notes": "Keep belt tight"},
        {"id": str(uuid.uuid4()), "plan_id": wp_id, "day_of_week": "Wednesday", "exercise_name": "Barbell Back Squats", "sets": 4, "reps": "8-10", "rest_seconds": 120, "instructions": "Break parallel, drive up explosively", "trainer_notes": "Hit full depth"},
    ]

    dp_id = "dddd0001-0000-0000-0000-000000000001"
    _GLOBAL_STORE["diet_plans"] = [
        {"id": dp_id, "gym_id": gym_id, "member_id": m1_id, "trainer_id": trainer_id, "title": "High Protein Muscle Building Diet", "notes": "Target 140g protein daily. Drink 3.5L water minimum.", "is_active": True}
    ]

    _GLOBAL_STORE["diet_meals"] = [
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Breakfast", "food_item": "Oatmeal with Whey Protein & Almonds", "quantity": "60g oats + 1 scoop whey + 10 almonds", "timing": "08:00 AM", "instructions": "Mix with warm water or skimmed milk", "nutrition_notes": "32g Protein, 45g Carbs"},
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Lunch", "food_item": "Grilled Paneer/Chicken with Brown Rice & Dal", "quantity": "150g Paneer/Chicken + 1 bowl Rice + 1 bowl Dal", "timing": "01:30 PM", "instructions": "Cook in 1 tsp olive oil", "nutrition_notes": "38g Protein, 55g Carbs"},
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Evening Snacks", "food_item": "Boiled Eggs or Sprouts Salad + Black Coffee", "quantity": "4 egg whites (or 1 bowl sprouts)", "timing": "05:30 PM", "instructions": "Pre-workout energy booster", "nutrition_notes": "15g Protein"},
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Dinner", "food_item": "Tofu/Soya Chunks with Mixed Vegetable Salad", "quantity": "150g Tofu + Green Salad", "timing": "08:30 PM", "instructions": "Light salt, no carbs after 9 PM", "nutrition_notes": "25g Protein, low carb"},
    ]

    _GLOBAL_STORE["inactivity_followups"] = [
        {"id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": m7_id, "contacted_by": receptionist_id, "contact_date": str(today - timedelta(days=2)), "channel": "whatsapp", "status": "contacted", "notes": "Member was out of station, will resume Monday"}
    ]
    _GLOBAL_STORE["renewal_records"] = []


class MockQueryBuilder:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.filters = []
        self.select_fields = "*"
        self.order_field = None
        self.order_desc = False
        self.limit_val = None

    def select(self, fields: str = "*"):
        self.select_fields = fields
        return self

    def eq(self, column: str, value: Any):
        self.filters.append(("eq", column, value))
        return self

    def neq(self, column: str, value: Any):
        self.filters.append(("neq", column, value))
        return self

    def in_(self, column: str, values: List[Any]):
        self.filters.append(("in", column, values))
        return self

    def gte(self, column: str, value: Any):
        self.filters.append(("gte", column, value))
        return self

    def lte(self, column: str, value: Any):
        self.filters.append(("lte", column, value))
        return self

    def ilike(self, column: str, pattern: str):
        self.filters.append(("ilike", column, pattern))
        return self

    def order(self, column: str, desc: bool = False):
        self.order_field = column
        self.order_desc = desc
        return self

    def limit(self, count: int):
        self.limit_val = count
        return self

    def execute(self):
        _init_seed_data()
        records = _GLOBAL_STORE.get(self.table_name, [])
        filtered = []

        for row in records:
            match = True
            for ftype, col, val in self.filters:
                r_val = row.get(col)
                if ftype == "eq" and str(r_val) != str(val):
                    match = False
                    break
                elif ftype == "neq" and str(r_val) == str(val):
                    match = False
                    break
                elif ftype == "in" and (r_val not in val and str(r_val) not in [str(v) for v in val]):
                    match = False
                    break
                elif ftype == "gte" and (r_val is None or str(r_val) < str(val)):
                    match = False
                    break
                elif ftype == "lte" and (r_val is None or str(r_val) > str(val)):
                    match = False
                    break
                elif ftype == "ilike":
                    p = str(val).replace("%", "").lower()
                    if p not in str(r_val or "").lower():
                        match = False
                        break
            if match:
                filtered.append(copy.deepcopy(row))

        if self.order_field:
            filtered.sort(
                key=lambda x: str(x.get(self.order_field, "") or ""),
                reverse=self.order_desc,
            )

        if self.limit_val is not None:
            filtered = filtered[: self.limit_val]

        class QueryResponse:
            def __init__(self, data):
                self.data = data

        return QueryResponse(filtered)

    def insert(self, payload: Any):
        _init_seed_data()
        table_rows = _GLOBAL_STORE.setdefault(self.table_name, [])
        items = payload if isinstance(payload, list) else [payload]
        inserted = []
        for it in items:
            row = copy.deepcopy(it)
            if "id" not in row or not row["id"]:
                row["id"] = str(uuid.uuid4())
            table_rows.append(row)
            inserted.append(row)

        class InsertBuilder:
            def __init__(self, data):
                self.data = data
            def execute(self):
                class R:
                    def __init__(self, d): self.data = d
                return R(self.data)

        return InsertBuilder(inserted)

    def update(self, payload: Dict[str, Any]):
        class UpdateBuilder:
            def __init__(self, tbl, payload, parent_filters):
                self.tbl = tbl
                self.payload = payload
                self.filters = list(parent_filters)
            def eq(self, column, value):
                self.filters.append(("eq", column, value))
                return self
            def execute(self):
                _init_seed_data()
                updated = []
                for row in _GLOBAL_STORE.get(self.tbl, []):
                    match = True
                    for _, col, val in self.filters:
                        if str(row.get(col)) != str(val):
                            match = False
                            break
                    if match:
                        row.update(self.payload)
                        updated.append(copy.deepcopy(row))
                class R:
                    def __init__(self, d): self.data = d
                return R(updated)
        return UpdateBuilder(self.table_name, payload, self.filters)

    def delete(self):
        class DeleteBuilder:
            def __init__(self, tbl, parent_filters):
                self.tbl = tbl
                self.filters = list(parent_filters)
            def eq(self, column, value):
                self.filters.append(("eq", column, value))
                return self
            def execute(self):
                _init_seed_data()
                remaining = []
                deleted = []
                for row in _GLOBAL_STORE.get(self.tbl, []):
                    match = True
                    for _, col, val in self.filters:
                        if str(row.get(col)) != str(val):
                            match = False
                            break
                    if match:
                        deleted.append(row)
                    else:
                        remaining.append(row)
                _GLOBAL_STORE[self.tbl] = remaining
                class R:
                    def __init__(self, d): self.data = d
                return R(deleted)
        return DeleteBuilder(self.table_name, self.filters)


class MockAuth:
    def sign_in_with_password(self, credentials: Dict[str, str]):
        _init_seed_data()
        email = credentials.get("email", "").strip().lower()
        pwd = credentials.get("password", "")

        # Match profiles
        for p in _GLOBAL_STORE.get("profiles", []):
            if p.get("email", "").lower() == email:
                class Session:
                    access_token = "mock-jwt-token"
                class AuthResponse:
                    def __init__(self, p):
                        self.user = type("U", (), {"id": p["id"], "email": p["email"]})()
                        self.session = Session()
                return AuthResponse(p)

        # Fallback for demo
        class Session:
            access_token = "mock-jwt-token"
        class FallbackAuthResponse:
            def __init__(self):
                self.user = type("U", (), {"id": "11111111-1111-1111-1111-111111111111", "email": email})()
                self.session = Session()
        return FallbackAuthResponse()

    def sign_out(self):
        return True


class MockClient:
    def __init__(self):
        self.auth = MockAuth()

    def table(self, table_name: str):
        return MockQueryBuilder(table_name)


_LOCAL_DB_INSTANCE = None

def get_local_db() -> MockClient:
    global _LOCAL_DB_INSTANCE
    if _LOCAL_DB_INSTANCE is None:
        _LOCAL_DB_INSTANCE = MockClient()
    return _LOCAL_DB_INSTANCE

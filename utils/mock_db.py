"""Local high-fidelity database simulator for GYM BUDDY.

Provides an in-memory Supabase-compatible interface mimicking query chaining:
.table().select().eq().execute()
Pre-seeded with realistic Indian demo data for out-of-the-box demonstration.

Every MockClient owns its own store, so each browser session on a deployed
demo gets an isolated sandbox instead of sharing one global dataset with
every other visitor.
"""

from __future__ import annotations
import copy
import random
from datetime import timedelta
from typing import Any, Dict, List
import uuid

from .date_utils import get_ist_today, get_ist_now

GYM_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_ID = "00000000-0000-0000-0000-000000000000"
OWNER_ID = "11111111-1111-1111-1111-111111111111"
RECEPTIONIST_ID = "22222222-2222-2222-2222-222222222222"
TRAINER_ID = "33333333-3333-3333-3333-333333333333"
TRAINER2_ID = "33333333-3333-3333-3333-333333333334"
MEMBER_USER_ID = "44444444-4444-4444-4444-444444444444"

# Demo credentials (offline mode only). Live deployments authenticate via Supabase Auth.
DEMO_PASSWORDS = {
    "admin@gymbuddy.io": "admin123",
    "owner@fitzone.in": "owner123",
    "reception@fitzone.in": "reception123",
    "vikram@fitzone.in": "trainer123",
    "neha@fitzone.in": "trainer123",
    "amit@gmail.com": "member123",
}


def _member_uuid(i: int) -> str:
    return f"bbbb{i:04d}-0000-0000-0000-{i:012d}"


def _seed_data() -> Dict[str, List[Dict[str, Any]]]:
    store: Dict[str, List[Dict[str, Any]]] = {}
    today = get_ist_today()
    now_minutes = get_ist_now().hour * 60 + get_ist_now().minute
    rng = random.Random(42)

    def d(days_ago: int) -> str:
        return str(today - timedelta(days=days_ago))

    store["gyms"] = [
        {
            "id": GYM_ID,
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

    store["profiles"] = [
        {"id": ADMIN_ID, "gym_id": GYM_ID, "role": "admin", "full_name": "Platform Admin", "email": "admin@gymbuddy.io", "phone": "9999900000"},
        {"id": OWNER_ID, "gym_id": GYM_ID, "role": "owner", "full_name": "Rajesh Kumar", "email": "owner@fitzone.in", "phone": "9876543210"},
        {"id": RECEPTIONIST_ID, "gym_id": GYM_ID, "role": "receptionist", "full_name": "Pooja Sharma", "email": "reception@fitzone.in", "phone": "9876543211"},
        {"id": TRAINER_ID, "gym_id": GYM_ID, "role": "trainer", "full_name": "Vikram Singh", "email": "vikram@fitzone.in", "phone": "9876543212"},
        {"id": TRAINER2_ID, "gym_id": GYM_ID, "role": "trainer", "full_name": "Neha Kapoor", "email": "neha@fitzone.in", "phone": "9876543213"},
        {"id": MEMBER_USER_ID, "gym_id": GYM_ID, "role": "member", "full_name": "Amit Sharma", "email": "amit@gmail.com", "phone": "9876500001"},
    ]

    plan_monthly = "aaaa0001-0000-0000-0000-000000000001"
    plan_quarterly = "aaaa0002-0000-0000-0000-000000000002"
    plan_half_yearly = "aaaa0003-0000-0000-0000-000000000003"
    plan_yearly = "aaaa0004-0000-0000-0000-000000000004"

    store["membership_plans"] = [
        {"id": plan_monthly, "gym_id": GYM_ID, "name": "Monthly Starter", "duration_days": 30, "price": 1800.0, "description": "Standard 1 month gym access", "is_active": True},
        {"id": plan_quarterly, "gym_id": GYM_ID, "name": "Quarterly Fitness", "duration_days": 90, "price": 4500.0, "description": "3 months access with cardio", "is_active": True},
        {"id": plan_half_yearly, "gym_id": GYM_ID, "name": "Half-Yearly Transformation", "duration_days": 180, "price": 8000.0, "description": "6 months full access + steam", "is_active": True},
        {"id": plan_yearly, "gym_id": GYM_ID, "name": "Annual Champion", "duration_days": 365, "price": 14000.0, "description": "12 months VIP access + PT session", "is_active": True},
    ]
    plan_by_id = {p["id"]: p for p in store["membership_plans"]}

    # name, phone, email, age, gender, area, plan, membership_start_days_ago, joined_days_ago, is_active, visit_prob, last_visit_days_ago
    roster = [
        ("Amit Sharma", "9876500001", "amit@gmail.com", 28, "Male", "Indiranagar", plan_quarterly, 30, 120, True, 0.8, 0),
        ("Priya Patel", "9876500002", "priya.p@gmail.com", 26, "Female", "Koramangala", plan_monthly, 26, 146, True, 0.7, 0),
        ("Rahul Verma", "9876500003", "rahul.v@yahoo.com", 32, "Male", "HSR Layout", plan_half_yearly, 168, 168, True, 0.6, 0),
        ("Sneha Reddy", "9876500004", "sneha.r@gmail.com", 24, "Female", "Whitefield", plan_monthly, 35, 95, True, 0.4, 20),
        ("Rohan Gupta", "9876500005", "rohan.g@gmail.com", 30, "Male", "BTM Layout", plan_yearly, 100, 100, True, 0.65, 1),
        ("Ananya Iyer", "9876500006", "ananya.i@outlook.com", 29, "Female", "Jayanagar", plan_quarterly, 80, 80, True, 0.5, 9),
        ("Karan Malhotra", "9876500007", "karan.m@gmail.com", 35, "Male", "Indiranagar", plan_monthly, 20, 50, True, 0.5, 18),
        ("Deepika Joshi", "9876500008", "deepika.j@gmail.com", 27, "Female", "Marathahalli", plan_monthly, 45, 75, False, 0.3, 40),
        ("Arjun Nair", "9876500009", "arjun.n@gmail.com", 31, "Male", "Domlur", plan_quarterly, 85, 85, True, 0.55, 2),
        ("Meera Krishnan", "9876500010", "meera.k@gmail.com", 23, "Female", "Ulsoor", plan_monthly, 6, 6, True, 0.0, None),
    ]

    store["members"] = []
    store["member_memberships"] = []
    store["payments"] = []
    store["attendance"] = []
    receipt_seq = 1

    for idx, (name, phone, email, age, gender, area, plan_id, start_ago, joined_ago, active, prob, last_ago) in enumerate(roster, start=1):
        mid = _member_uuid(idx)
        code = f"GMB-{today.year}-{idx:03d}"
        plan = plan_by_id[plan_id]
        store["members"].append({
            "id": mid, "gym_id": GYM_ID, "user_id": MEMBER_USER_ID if idx == 1 else None,
            "member_code": code, "full_name": name, "phone": phone, "email": email,
            "age": age, "gender": gender, "address": f"{area}, Bengaluru",
            "emergency_contact": f"98450{idx:05d}", "qr_code_data": code,
            "is_active": active, "joined_date": d(joined_ago),
        })

        start = today - timedelta(days=start_ago)
        end = start + timedelta(days=plan["duration_days"])
        store["member_memberships"].append({
            "id": str(uuid.uuid4()), "gym_id": GYM_ID, "member_id": mid, "plan_id": plan_id,
            "start_date": str(start), "end_date": str(end),
            "status": "active" if end >= today else "expired", "amount_paid": plan["price"],
        })

        # One payment per plan cycle since joining, so revenue charts have real shape.
        cycle_ago = start_ago
        while cycle_ago <= joined_ago:
            store["payments"].append({
                "id": str(uuid.uuid4()), "gym_id": GYM_ID, "member_id": mid, "amount": plan["price"],
                "payment_date": d(cycle_ago), "payment_method": rng.choice(["UPI", "UPI", "Cash", "Bank Transfer"]),
                "transaction_ref": f"UPI/{today.year}/{rng.randint(10000, 99999)}",
                "receipt_no": f"REC-{today.year}-{receipt_seq:04d}", "remarks": "",
            })
            receipt_seq += 1
            cycle_ago += plan["duration_days"]

        # Attendance history for the last 45 days.
        if last_ago is not None:
            for days_ago in range(last_ago, min(45, joined_ago + 1)):
                if days_ago == last_ago or rng.random() < prob:
                    minutes = rng.choice([6, 6, 7, 7, 8, 18, 18, 19, 20]) * 60 + rng.randint(0, 59)
                    if days_ago == 0 and minutes > now_minutes:
                        # Never seed a check-in "later today" than the current time.
                        if now_minutes < 30:
                            continue
                        minutes = rng.randint(max(now_minutes - 240, 0), now_minutes - 1)
                    store["attendance"].append({
                        "id": str(uuid.uuid4()), "gym_id": GYM_ID, "member_id": mid,
                        "check_in_date": d(days_ago), "check_in_time": f"{minutes // 60:02d}:{minutes % 60:02d}:00",
                        "method": rng.choice(["qr_code", "qr_code", "manual"]),
                    })

    m = {i: _member_uuid(i) for i in range(1, 11)}

    store["trainer_assignments"] = [
        {"id": str(uuid.uuid4()), "gym_id": GYM_ID, "trainer_id": TRAINER_ID, "member_id": m[i], "assigned_date": d(25), "is_active": True}
        for i in (1, 2, 3, 7)
    ] + [
        {"id": str(uuid.uuid4()), "gym_id": GYM_ID, "trainer_id": TRAINER2_ID, "member_id": m[i], "assigned_date": d(25), "is_active": True}
        for i in (4, 5, 6, 9)
    ]

    wp_id = "cccc0001-0000-0000-0000-000000000001"
    store["workout_plans"] = [
        {"id": wp_id, "gym_id": GYM_ID, "member_id": m[1], "trainer_id": TRAINER_ID, "title": "Muscle Hypertrophy & Strength", "description": "Push-Pull-Legs split focusing on progressive overload", "is_active": True}
    ]
    exercises = [
        ("Monday", "Barbell Bench Press", 4, "8-10", 90, "Keep shoulder blades retracted and elbows tucked at 45 degrees", "Warm up with 20kg bar first"),
        ("Monday", "Incline Dumbbell Press", 3, "10-12", 60, "Full stretch at bottom, squeeze chest at peak", "Use 18kg dumbbells"),
        ("Monday", "Cable Triceps Pushdown", 3, "12-15", 45, "Elbows pinned to your sides", ""),
        ("Tuesday", "Barbell Deadlift", 4, "6-8", 120, "Neutral spine, push through heels", "Keep belt tight"),
        ("Tuesday", "Lat Pulldown", 3, "10-12", 60, "Pull to upper chest, control the return", ""),
        ("Wednesday", "Barbell Back Squats", 4, "8-10", 120, "Break parallel, drive up explosively", "Hit full depth"),
        ("Wednesday", "Walking Lunges", 3, "12 each leg", 60, "Knee tracks over toes", ""),
        ("Friday", "Overhead Press", 4, "8-10", 90, "Brace core, no back arch", ""),
        ("Friday", "Barbell Rows", 4, "8-10", 90, "Hinge to 45 degrees, pull to belly button", ""),
    ]
    store["workout_exercises"] = [
        {"id": str(uuid.uuid4()), "plan_id": wp_id, "day_of_week": day, "exercise_name": name, "sets": sets,
         "reps": reps, "rest_seconds": rest, "instructions": instr, "trainer_notes": notes, "order_index": i}
        for i, (day, name, sets, reps, rest, instr, notes) in enumerate(exercises)
    ]

    dp_id = "dddd0001-0000-0000-0000-000000000001"
    store["diet_plans"] = [
        {"id": dp_id, "gym_id": GYM_ID, "member_id": m[1], "trainer_id": TRAINER_ID, "title": "High Protein Muscle Building Diet", "notes": "Target 140g protein daily. Drink 3.5L water minimum.", "is_active": True}
    ]
    store["diet_meals"] = [
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Breakfast", "food_item": "Oatmeal with Whey Protein & Almonds", "quantity": "60g oats + 1 scoop whey + 10 almonds", "timing": "08:00 AM", "instructions": "Mix with warm water or skimmed milk", "nutrition_notes": "32g Protein, 45g Carbs"},
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Lunch", "food_item": "Grilled Paneer/Chicken with Brown Rice & Dal", "quantity": "150g Paneer/Chicken + 1 bowl Rice + 1 bowl Dal", "timing": "01:30 PM", "instructions": "Cook in 1 tsp olive oil", "nutrition_notes": "38g Protein, 55g Carbs"},
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Evening Snacks", "food_item": "Boiled Eggs or Sprouts Salad + Black Coffee", "quantity": "4 egg whites (or 1 bowl sprouts)", "timing": "05:30 PM", "instructions": "Pre-workout energy booster", "nutrition_notes": "15g Protein"},
        {"id": str(uuid.uuid4()), "diet_plan_id": dp_id, "meal_type": "Dinner", "food_item": "Tofu/Soya Chunks with Mixed Vegetable Salad", "quantity": "150g Tofu + Green Salad", "timing": "08:30 PM", "instructions": "Light salt, no carbs after 9 PM", "nutrition_notes": "25g Protein, low carb"},
    ]

    store["inactivity_followups"] = [
        {"id": str(uuid.uuid4()), "gym_id": GYM_ID, "member_id": m[7], "contacted_by": RECEPTIONIST_ID, "contact_date": d(2), "channel": "whatsapp", "status": "contacted", "notes": "Member was out of station, will resume Monday"}
    ]
    store["renewal_records"] = []
    return store


class _Result:
    def __init__(self, data):
        self.data = data


def _matches(row: Dict[str, Any], filters) -> bool:
    for ftype, col, val in filters:
        r_val = row.get(col)
        if ftype == "eq" and str(r_val) != str(val):
            return False
        if ftype == "neq" and str(r_val) == str(val):
            return False
        if ftype == "in" and str(r_val) not in [str(v) for v in val]:
            return False
        if ftype == "gte" and (r_val is None or str(r_val) < str(val)):
            return False
        if ftype == "lte" and (r_val is None or str(r_val) > str(val)):
            return False
        if ftype == "ilike" and str(val).replace("%", "").lower() not in str(r_val or "").lower():
            return False
    return True


class MockQueryBuilder:
    """Chainable query builder supporting select / insert / update / delete."""

    def __init__(self, store: Dict[str, List[Dict[str, Any]]], table_name: str):
        self.store = store
        self.table_name = table_name
        self.filters = []
        self.order_field = None
        self.order_desc = False
        self.limit_val = None
        self._mode = "select"
        self._payload = None

    def select(self, fields: str = "*"):
        self._mode = "select"
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

    def insert(self, payload: Any):
        self._mode = "insert"
        self._payload = payload
        return self

    def update(self, payload: Dict[str, Any]):
        self._mode = "update"
        self._payload = payload
        return self

    def delete(self):
        self._mode = "delete"
        return self

    def execute(self):
        rows = self.store.setdefault(self.table_name, [])

        if self._mode == "insert":
            items = self._payload if isinstance(self._payload, list) else [self._payload]
            inserted = []
            for it in items:
                row = copy.deepcopy(it)
                if not row.get("id"):
                    row["id"] = str(uuid.uuid4())
                rows.append(row)
                inserted.append(copy.deepcopy(row))
            return _Result(inserted)

        if self._mode == "update":
            updated = []
            for row in rows:
                if _matches(row, self.filters):
                    row.update(copy.deepcopy(self._payload))
                    updated.append(copy.deepcopy(row))
            return _Result(updated)

        if self._mode == "delete":
            keep, deleted = [], []
            for row in rows:
                (deleted if _matches(row, self.filters) else keep).append(row)
            self.store[self.table_name] = keep
            return _Result(deleted)

        filtered = [copy.deepcopy(r) for r in rows if _matches(r, self.filters)]
        if self.order_field:
            def sort_key(row):
                v = row.get(self.order_field)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    return (0, float(v), "")
                return (1, 0.0, str(v or ""))
            filtered.sort(key=sort_key, reverse=self.order_desc)
        if self.limit_val is not None:
            filtered = filtered[: self.limit_val]
        return _Result(filtered)


class _MockUser:
    def __init__(self, uid: str, email: str):
        self.id = uid
        self.email = email


class _MockSession:
    access_token = "mock-jwt-token"


class _MockAuthResponse:
    def __init__(self, uid: str, email: str):
        self.user = _MockUser(uid, email)
        self.session = _MockSession()


class MockAuth:
    def __init__(self, store: Dict[str, List[Dict[str, Any]]]):
        self.store = store

    def sign_in_with_password(self, credentials: Dict[str, str]):
        email = (credentials.get("email") or "").strip().lower()
        pwd = credentials.get("password") or ""
        if DEMO_PASSWORDS.get(email) != pwd or not pwd:
            raise ValueError("Invalid login credentials")
        for p in self.store.get("profiles", []):
            if (p.get("email") or "").lower() == email:
                return _MockAuthResponse(p["id"], p["email"])
        raise ValueError("Invalid login credentials")

    def sign_out(self):
        return True


class MockClient:
    is_mock = True

    def __init__(self):
        self.store = _seed_data()
        self.auth = MockAuth(self.store)

    def table(self, table_name: str):
        return MockQueryBuilder(self.store, table_name)


def get_local_db() -> MockClient:
    """Return a fresh, independently seeded in-memory database."""
    return MockClient()

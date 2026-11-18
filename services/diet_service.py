"""Diet plan management service for GYM BUDDY.

Handles meal categorization (Breakfast, Lunch, Evening Snacks, Dinner),
food items, timing, nutritional instructions, and trainer edits.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client


def get_member_diet(member_id: str) -> Optional[Dict[str, Any]]:
    """Fetch active diet plan with all meal items organized by meal type."""
    client = get_supabase_client()
    try:
        dp_res = (
            client.table("diet_plans")
            .select("*")
            .eq("member_id", member_id)
            .eq("is_active", True)
            .execute()
        )
        if not dp_res.data or len(dp_res.data) == 0:
            return None

        plan = dp_res.data[0]
        plan_id = plan["id"]

        # Fetch meal items
        meals_res = (
            client.table("diet_meals")
            .select("*")
            .eq("diet_plan_id", plan_id)
            .execute()
        )
        meals = meals_res.data or []

        # Group by meal type
        categories = ["Breakfast", "Lunch", "Evening Snacks", "Dinner"]
        meals_by_type = {c: [] for c in categories}
        for m in meals:
            m_type = m.get("meal_type", "Breakfast")
            if m_type in meals_by_type:
                meals_by_type[m_type].append(m)
            else:
                meals_by_type.setdefault(m_type, []).append(m)

        plan["meals"] = meals_by_type
        plan["all_items"] = meals

        # Fetch trainer name
        trainer_id = plan.get("trainer_id")
        if trainer_id:
            t_res = client.table("profiles").select("full_name").eq("id", trainer_id).execute()
            plan["trainer_name"] = t_res.data[0].get("full_name", "Nutrition Coach") if t_res.data else "Nutrition Coach"
        else:
            plan["trainer_name"] = "Gym Staff"

        return plan
    except Exception:
        return None


def save_diet_plan(
    gym_id: str,
    member_id: str,
    trainer_id: str,
    title: str,
    notes: str,
    meals: List[Dict[str, Any]],
) -> Tuple[bool, Optional[str]]:
    """Create or update diet plan and replace meal items."""
    client = get_supabase_client()
    try:
        existing_res = (
            client.table("diet_plans")
            .select("id")
            .eq("member_id", member_id)
            .eq("is_active", True)
            .execute()
        )

        if existing_res.data and len(existing_res.data) > 0:
            plan_id = existing_res.data[0]["id"]
            client.table("diet_plans").update({
                "title": title,
                "notes": notes,
                "trainer_id": trainer_id,
            }).eq("id", plan_id).execute()
            client.table("diet_meals").delete().eq("diet_plan_id", plan_id).execute()
        else:
            plan_id = str(uuid.uuid4())
            client.table("diet_plans").insert({
                "id": plan_id,
                "gym_id": gym_id,
                "member_id": member_id,
                "trainer_id": trainer_id,
                "title": title,
                "notes": notes,
                "is_active": True,
            }).execute()

        # Insert meal items
        to_insert = []
        for m in meals:
            to_insert.append({
                "id": str(uuid.uuid4()),
                "diet_plan_id": plan_id,
                "meal_type": m.get("meal_type", "Breakfast"),
                "food_item": m.get("food_item"),
                "quantity": m.get("quantity", ""),
                "timing": m.get("timing", ""),
                "instructions": m.get("instructions", ""),
                "nutrition_notes": m.get("nutrition_notes", ""),
            })

        if to_insert:
            client.table("diet_meals").insert(to_insert).execute()

        return True, None
    except Exception as e:
        return False, f"Failed to save diet plan: {str(e)}"

"""Workout plan management service for GYM BUDDY.

Handles weekly workout schedules, exercise lists, trainer assignment,
and member workout view.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client


def get_member_workout(member_id: str) -> Optional[Dict[str, Any]]:
    """Fetch active workout plan with all daily exercises for a member."""
    client = get_supabase_client()
    try:
        wp_res = (
            client.table("workout_plans")
            .select("*")
            .eq("member_id", member_id)
            .eq("is_active", True)
            .execute()
        )
        if not wp_res.data or len(wp_res.data) == 0:
            return None

        plan = wp_res.data[0]
        plan_id = plan["id"]

        # Fetch exercises
        ex_res = (
            client.table("workout_exercises")
            .select("*")
            .eq("plan_id", plan_id)
            .execute()
        )
        exercises = ex_res.data or []

        # Group by day
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        schedule = {d: [] for d in days_order}
        for ex in exercises:
            day = ex.get("day_of_week", "Monday")
            if day in schedule:
                schedule[day].append(ex)
            else:
                schedule.setdefault(day, []).append(ex)

        plan["schedule"] = schedule
        plan["exercises"] = exercises

        # Fetch trainer name
        trainer_id = plan.get("trainer_id")
        if trainer_id:
            t_res = client.table("profiles").select("full_name").eq("id", trainer_id).execute()
            plan["trainer_name"] = t_res.data[0].get("full_name", "Assigned Trainer") if t_res.data else "Assigned Trainer"
        else:
            plan["trainer_name"] = "Gym Staff"

        return plan
    except Exception:
        return None


def save_workout_plan(
    gym_id: str,
    member_id: str,
    trainer_id: str,
    title: str,
    description: str,
    exercises: List[Dict[str, Any]],
) -> Tuple[bool, Optional[str]]:
    """Create or update workout plan and replace exercises."""
    client = get_supabase_client()
    try:
        # Check existing active plan
        existing_res = (
            client.table("workout_plans")
            .select("id")
            .eq("member_id", member_id)
            .eq("is_active", True)
            .execute()
        )
        
        if existing_res.data and len(existing_res.data) > 0:
            plan_id = existing_res.data[0]["id"]
            client.table("workout_plans").update({
                "title": title,
                "description": description,
                "trainer_id": trainer_id,
            }).eq("id", plan_id).execute()
            # Delete old exercises
            client.table("workout_exercises").delete().eq("plan_id", plan_id).execute()
        else:
            plan_id = str(uuid.uuid4())
            client.table("workout_plans").insert({
                "id": plan_id,
                "gym_id": gym_id,
                "member_id": member_id,
                "trainer_id": trainer_id,
                "title": title,
                "description": description,
                "is_active": True,
            }).execute()

        # Insert new exercises
        to_insert = []
        for ex in exercises:
            to_insert.append({
                "id": str(uuid.uuid4()),
                "plan_id": plan_id,
                "day_of_week": ex.get("day_of_week", "Monday"),
                "exercise_name": ex.get("exercise_name"),
                "sets": int(ex.get("sets", 3)),
                "reps": str(ex.get("reps", "10-12")),
                "rest_seconds": int(ex.get("rest_seconds", 60)),
                "instructions": ex.get("instructions", ""),
                "trainer_notes": ex.get("trainer_notes", ""),
            })

        if to_insert:
            client.table("workout_exercises").insert(to_insert).execute()

        return True, None
    except Exception as e:
        return False, f"Failed to save workout plan: {str(e)}"

"""Gym management and membership plan service for GYM BUDDY.

Handles multi-gym facilities, membership plan catalog, and tenant settings.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from utils.security import get_supabase_client


def get_gym_details(gym_id: str) -> Optional[Dict[str, Any]]:
    """Fetch facility details for a specific gym."""
    client = get_supabase_client()
    try:
        res = client.table("gyms").select("*").eq("id", gym_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception:
        pass
    return None


def get_all_gyms() -> List[Dict[str, Any]]:
    """Fetch list of all gym facilities (Platform Admin)."""
    client = get_supabase_client()
    try:
        res = client.table("gyms").select("*").order("name").execute()
        return res.data or []
    except Exception:
        return []


def create_gym(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Create a new gym facility in the platform."""
    client = get_supabase_client()
    try:
        res = client.table("gyms").insert(data).execute()
        if res.data and len(res.data) > 0:
            return True, None, res.data[0]
        return False, "Failed to create gym.", None
    except Exception as e:
        return False, str(e), None


def get_membership_plans(gym_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Fetch configured membership plans for a gym."""
    client = get_supabase_client()
    try:
        q = client.table("membership_plans").select("*").eq("gym_id", gym_id)
        if active_only:
            q = q.eq("is_active", True)
        res = q.order("price").execute()
        return res.data or []
    except Exception:
        return []


def create_membership_plan(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Create a new membership plan for a gym."""
    client = get_supabase_client()
    try:
        client.table("membership_plans").insert(data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

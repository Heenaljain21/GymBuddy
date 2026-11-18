"""Input validation utilities for GYM BUDDY.

Validates Indian mobile numbers, email addresses, and form payloads.
"""

from __future__ import annotations
import re
from typing import Dict, List, Tuple


def validate_phone(phone: str) -> bool:
    """Validate 10-digit Indian mobile number."""
    if not phone:
        return False
    digits = "".join(filter(str.isdigit, str(phone)))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return bool(re.match(r"^[6-9]\d{9}$", digits))


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return True  # Email is optional in some gym registrations
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def validate_member_form(data: Dict[str, any]) -> Tuple[bool, List[str]]:
    """Validate member registration form data.
    
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    
    name = (data.get("full_name") or "").strip()
    if not name or len(name) < 2:
        errors.append("Full Name is required (minimum 2 characters).")
        
    phone = data.get("phone") or ""
    if not validate_phone(phone):
        errors.append("A valid 10-digit Indian mobile number is required (starting with 6-9).")
        
    email = data.get("email") or ""
    if email and not validate_email(email):
        errors.append("Invalid email format.")
        
    age = data.get("age")
    if age is not None:
        try:
            age_int = int(age)
            if age_int < 10 or age_int > 100:
                errors.append("Age must be between 10 and 100.")
        except (ValueError, TypeError):
            errors.append("Age must be a valid number.")
            
    plan_id = data.get("plan_id")
    if not plan_id:
        errors.append("Please select a Membership Plan.")
        
    return len(errors) == 0, errors

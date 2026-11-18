"""Backend domain services package for GYM BUDDY."""

from .auth_service import sign_in, sign_out, is_authenticated
from .gym_service import get_gym_details, get_all_gyms, create_gym, get_membership_plans, create_membership_plan
from .member_service import register_member, get_members, search_members, get_member_by_qr
from .attendance_service import check_in, get_today_attendance, is_already_checked_in, get_member_attendance, get_monthly_attendance_count
from .payment_service import record_payment, get_payments, get_member_payments, get_revenue_stats
from .renewal_service import get_expiring_memberships, renew_membership, get_renewal_summary
from .workout_service import get_member_workout, save_workout_plan
from .diet_service import get_member_diet, save_diet_plan
from .inactivity_service import get_inactive_members, log_followup
from .report_service import (
    get_dashboard_stats,
    get_daily_revenue_chart,
    get_monthly_revenue_chart,
    get_attendance_trends,
    get_membership_distribution,
    get_member_growth_chart,
)

__all__ = [
    "sign_in",
    "sign_out",
    "is_authenticated",
    "get_gym_details",
    "get_all_gyms",
    "create_gym",
    "get_membership_plans",
    "create_membership_plan",
    "register_member",
    "get_members",
    "search_members",
    "get_member_by_qr",
    "check_in",
    "get_today_attendance",
    "is_already_checked_in",
    "get_member_attendance",
    "get_monthly_attendance_count",
    "record_payment",
    "get_payments",
    "get_member_payments",
    "get_revenue_stats",
    "get_expiring_memberships",
    "renew_membership",
    "get_renewal_summary",
    "get_member_workout",
    "save_workout_plan",
    "get_member_diet",
    "save_diet_plan",
    "get_inactive_members",
    "log_followup",
    "get_dashboard_stats",
    "get_daily_revenue_chart",
    "get_monthly_revenue_chart",
    "get_attendance_trends",
    "get_membership_distribution",
    "get_member_growth_chart",
]

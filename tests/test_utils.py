"""Unit tests for GYM BUDDY utility modules using unittest."""

import sys
import os
from datetime import date, timedelta
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import format_currency, format_phone, generate_whatsapp_link, clean_phone_for_whatsapp
from utils.validators import validate_phone, validate_email, validate_member_form
from utils.date_utils import days_remaining, days_since, format_date_display


class TestUtils(unittest.TestCase):

    def test_format_currency(self):
        self.assertEqual(format_currency(1500), "₹1,500.00")
        self.assertEqual(format_currency(14000.5), "₹14,000.50")
        self.assertEqual(format_currency(0), "₹0.00")
        self.assertEqual(format_currency(None), "₹0.00")

    def test_validate_phone(self):
        self.assertTrue(validate_phone("9876543210"))
        self.assertTrue(validate_phone("8123456789"))
        self.assertTrue(validate_phone("919876543210"))
        self.assertTrue(validate_phone("+91 98765 43210"))
        self.assertFalse(validate_phone("1234567890"))  # Must start with 6-9
        self.assertFalse(validate_phone("98765"))  # Too short

    def test_validate_email(self):
        self.assertTrue(validate_email("member@gymbuddy.io"))
        self.assertTrue(validate_email("user.name+tag@domain.co.in"))
        self.assertFalse(validate_email("invalid-email"))
        self.assertTrue(validate_email(""))  # Optional field

    def test_whatsapp_link_generator(self):
        link = generate_whatsapp_link("9876543210", "Hello Gym Buddy!")
        self.assertEqual("https://wa.me/919876543210?text=Hello%20Gym%20Buddy%21", link)

    def test_date_utilities(self):
        today = date.today()
        future = today + timedelta(days=10)
        past = today - timedelta(days=15)

        self.assertEqual(days_remaining(future), 10)
        self.assertEqual(days_remaining(past), -15)
        self.assertEqual(days_since(past), 15)
        self.assertEqual(days_since(today), 0)

    def test_member_form_validation(self):
        valid_data = {
            "full_name": "Karan Malhotra",
            "phone": "9876500007",
            "email": "karan@example.com",
            "age": 28,
            "plan_id": "plan-123",
        }
        is_valid, errs = validate_member_form(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errs), 0)

        invalid_data = {
            "full_name": "A",
            "phone": "12345",
            "age": 5,
            "plan_id": None,
        }
        is_valid, errs = validate_member_form(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreaterEqual(len(errs), 3)


if __name__ == "__main__":
    unittest.main()

"""Boots the whole Streamlit app headlessly and signs in as every demo role."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from streamlit.testing.v1 import AppTest

APP = os.path.join(ROOT, "app.py")


class TestAppSmoke(unittest.TestCase):

    def test_login_page_renders(self):
        at = AppTest.from_file(APP, default_timeout=60).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertIn("Sign in", [b.label for b in at.button])

    def test_each_demo_role_reaches_its_dashboard(self):
        for label in ("Owner", "Desk", "Trainer", "Member", "Admin"):
            with self.subTest(role=label):
                at = AppTest.from_file(APP, default_timeout=60).run()
                next(b for b in at.button if b.label == label).click().run()
                self.assertFalse(at.exception, [e.value for e in at.exception])
                self.assertNotIn("Sign in", [b.label for b in at.button])


if __name__ == "__main__":
    unittest.main()

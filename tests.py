# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import os
import unittest
from unittest import TestCase

from disclosure_extractor import (
    display_table,
    extract_financial_document,
    process_jef_document,
    process_judicial_watch,
)


class DisclosureTests(TestCase):
    """Test Financial Disclosures"""

    root_dir = os.path.dirname(os.path.realpath(__file__))
    assets_dir = os.path.join(root_dir, "tests", "test_assets")

    def test_judicial_watch(self):
        """Can we extract data from an old PDF"""
        pdf_path = os.path.join(self.assets_dir, "2004_judicial_watch.pdf")
        with open(pdf_path, "rb") as pdf:
            pdf_bytes = pdf.read()
        results = process_judicial_watch(pdf_bytes=pdf_bytes)
        self.assertTrue(
            results["success"], msg="Failed Judicial Watch Extraction"
        )
        display_table(results)

    def test_failing_checkboxes(self):
        """Can we process an ugly PDF?"""
        pdf_path = os.path.join(self.assets_dir, "2004_judicial_watch.pdf")
        results = extract_financial_document(file_path=pdf_path, resize=True)
        self.assertFalse(results["success"], msg="Somehow succeeded.")

    def test_extract_financial_document(self):
        """Test if we can process a complex PDF?"""
        pdf_path = os.path.join(self.assets_dir, "2011-Alito-J3.pdf")
        results = extract_financial_document(
            file_path=pdf_path, show_logs=False, resize=True
        )
        self.assertTrue(results["success"], msg="Process failed")
        display_table(results)

    def test_JEF_style_extraction(self):
        """Test if we can process a JEF processed PDF?"""
        pdf_path = os.path.join(self.assets_dir, "Lucero-C-J3.pdf")
        results = process_jef_document(
            file_path=pdf_path, calculate_wealth=True
        )
        self.assertTrue(results["success"], msg="Process failed")
        self.assertEqual(
            len(results["sections"]["Positions"]["rows"]),
            1,
            msg="Positions failed",
        )
        self.assertEqual(
            len(results["sections"]["Agreements"]["rows"]),
            0,
            msg="Agreements failed",
        )
        self.assertEqual(
            len(results["sections"]["Investments and Trusts"]["rows"]),
            84,
            msg="Investments failed",
        )
        self.assertEqual(
            results["sections"]["Investments and Trusts"]["rows"][0]["A"][
                "text"
            ],
            "Commercial Building, Alamosa County, CO",
            msg="Wrong investment",
        )
        self.assertEqual(
            results["Additional Information or Explanations"]["text"],
            """1) Line 5 - Land was purchased on January 1, 2013 for $50,174 from the estate of Maria Medina, property was subject to mortgage (part VI, line 1) that was paid-in-full during 2018. PART VII. #1 Estimated value based on comparative sales.""",
            msg="Addendum incorrect",
        )
        self.assertFalse(
            results["Additional Information or Explanations"]["is_redacted"],
            msg="Addendum redaction incorrect",
        )


if __name__ == "__main__":
    unittest.main()

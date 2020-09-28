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
    process_judicial_watch,
    print_results,
    process_financial_document,
)


class DisclosureTests(TestCase):
    """Test Financial Disclosures"""

    test_dir = os.path.dirname(os.path.realpath(__file__))
    assets_dir = os.path.join(test_dir, "test_assets")

    def test_judicial_watch(self):
        """Can we extract data from an old PDF"""
        pdf_path = os.path.join(self.assets_dir, "2004_judicial_watch.pdf")
        with open(pdf_path, "rb") as pdf:
            pdf_bytes = pdf.read()
        results = process_judicial_watch(pdf_bytes=pdf_bytes)
        print(results)
        print(pdf_path)
        print_results(results)

    def test_failing_checkboxes(self):
        """Can we process an ugly PDF?"""
        pdf_path = os.path.join(self.assets_dir, "2004_judicial_watch.pdf")
        with open(pdf_path, "rb") as pdf:
            pdf_bytes = pdf.read()
        results = process_financial_document(pdf_bytes=pdf_bytes)
        self.assertFalse(results["success"])

    def test_process_fd_call(self):
        """Test successfull parsing of  """
        pdf_path = os.path.join(self.assets_dir, "2011-Alito-J3.pdf")
        with open(pdf_path, "rb") as pdf:
            pdf_bytes = pdf.read()
        results = process_financial_document(pdf_bytes=pdf_bytes)
        self.assertTrue(results["success"])


if __name__ == "__main__":
    unittest.main()

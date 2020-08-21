# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from unittest import TestCase
from io import open

import unittest
import os
import re


class TEMPLATE_TEST(TestCase):
    """Obey the testing goat."""

    def test_something(self):
        """A testing template"""
        
        matches = True
        expected_matches = True
        self.assertEqual(matches, expected_matches)


if __name__ == "__main__":
    unittest.main()

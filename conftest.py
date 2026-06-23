"""Pytest configuration for the test suite.

Placing this file at the repository root makes pytest insert the root onto
sys.path during collection, so the tests can ``import logic_utils`` (and
app.py's own ``from logic_utils import ...`` resolves) no matter how pytest is
invoked. This replaces the manual sys.path manipulation the tests used to do.
"""

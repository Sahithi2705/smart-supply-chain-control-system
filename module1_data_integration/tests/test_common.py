import pandas as pd
from transformations.common import stable_key


def test_stable_key_is_deterministic():
    assert stable_key("Vendor A", "Site 1") == stable_key("Vendor A", "Site 1")


def test_stable_key_normalizes_case_and_whitespace():
    assert stable_key("Vendor A ", "Site 1") == stable_key("vendor a", "site 1")

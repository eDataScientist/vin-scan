"""Self-check for the VIN normalization/regex trust boundary. Run: .venv/bin/python check.py"""
import os

os.environ.setdefault("OPENROUTER_API_KEY", "unused-for-this-check")
from server import normalize_vin  # noqa: E402

VIN = "WBAEV53444KM12345"

assert normalize_vin(VIN) == VIN
assert normalize_vin(" wbaev 53444 km12345 ") == VIN, "spaces stripped"
assert normalize_vin("WBAEV-53444-KM12345") == VIN, "hyphens stripped"
assert normalize_vin("wbaev53444km12345") == VIN, "lowercase upcased"

assert normalize_vin(None) is None
assert normalize_vin("") is None
assert normalize_vin("SHORT") is None, "too short"
assert normalize_vin("WBAEV53444KM123456") is None, "18 chars"
assert normalize_vin("WBAEV53444KMI2345") is None, "I is not a VIN character"
assert normalize_vin("WBAEV53444KMO2345") is None, "O is not a VIN character"
assert normalize_vin("WBAEV53444KMQ2345") is None, "Q is not a VIN character"

print("check.py: all assertions passed")

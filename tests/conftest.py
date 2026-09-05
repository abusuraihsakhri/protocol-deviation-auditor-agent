"""
Pytest configuration — sets required environment variables before module import.
"""
import os

# Set audit secret key for HMAC-SHA256 audit trail before any module imports
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-for-testing-2026")

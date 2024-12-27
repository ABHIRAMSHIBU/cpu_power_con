import pytest

def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers",
        "privileged: mark test as requiring privileged (root) access"
    ) 
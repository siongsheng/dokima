"""Tests for user_service module using mock.patch with create=True.

These tests demonstrate that mock.patch with create=True can pass
even when the real implementation function is MISSING (delete_user).
The vet phase real_code_check should catch this regression.
"""
import sys
import os
from unittest.mock import patch

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@patch('user_service.get_user', create=True)
def test_get_user(mock_get_user):
    mock_get_user.return_value = {"id": 1, "name": "Mocked User"}
    from user_service import get_user
    result = get_user(1)
    assert result == {"id": 1, "name": "Mocked User"}
    mock_get_user.assert_called_once_with(1)


@patch('user_service.delete_user', create=True)
def test_delete_user(mock_delete_user):
    """delete_user is deliberately missing from user_service.py.
    This test passes because create=True creates the mock attribute
    even though the real function doesn't exist.
    The vet phase real_code_check should flag this."""
    mock_delete_user.return_value = True
    from user_service import delete_user
    result = delete_user(42)
    assert result is True
    mock_delete_user.assert_called_once_with(42)

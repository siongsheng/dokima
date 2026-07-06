"""Tests for calculator module using mock.patch with create=True.

These tests demonstrate that mock.patch with create=True can pass
even when the real implementation function exists — the vet phase
should verify that all referenced functions are actually importable.
"""
from unittest.mock import patch


@patch('calculator.add', create=True)
def test_add(mock_add):
    mock_add.return_value = 5
    from calculator import add
    result = add(2, 3)
    assert result == 5
    mock_add.assert_called_once_with(2, 3)


@patch('calculator.subtract', create=True)
def test_subtract(mock_subtract):
    mock_subtract.return_value = 2
    from calculator import subtract
    result = subtract(5, 3)
    assert result == 2
    mock_subtract.assert_called_once_with(5, 3)

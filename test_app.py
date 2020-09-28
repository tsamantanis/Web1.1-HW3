import pytest

from app import *

def test_index():
    """Test that the index page loads page """
    res = app.test_client().get('/')
    assert res.status_code == 200

    assert "What's the weather like today?" in res.get_data(as_text=True)

def test_get_letter_for_units():
    """Test get_letter_for_units function with "metric" as input"""
    assert "C" == get_letter_for_units("metric")

def test_get_letter_for_units():
    """Test get_letter_for_units function with "imperial" as input"""
    assert "F" == get_letter_for_units("imperial")


def test_results():
    """Test that the results page loads page and presents results"""
    res = app.test_client().get('/results')
    assert res.status_code == 200

    assert "Date" in res.get_data(as_text=True)
    assert "Athens, gr" in res.get_data(as_text=True)
    assert "Temperature" in res.get_data(as_text=True)
    assert "Wind Speed" in res.get_data(as_text=True)
    assert "Sunrise" in res.get_data(as_text=True)

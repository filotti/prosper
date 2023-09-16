"""
This module contains tests for the Prosper API.
It uses the pytest framework and mocks the requests made to the API.
"""

from unittest.mock import patch, ANY

import pytest
import requests

from prosper_api import (
    get_account_info,
    get_access_token,
    get_listings,
    invest_in_listing,
    PROSPER_ORDER_URL
    )


@patch('prosper_api.requests.get')
def test_get_account_info(mock_get):
    # Set up the mock to return a specific response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'available_cash_balance': 1000}

    # Call the function with the mock in place
    result = get_account_info('fake_token')

    # Check that the function returned the expected result
    assert result == {'available_cash_balance': 1000}

@patch('prosper_api.requests.get')
def test_get_account_info_error_response(mock_get):
    # Set up the mock to return a specific error response
    mock_get.return_value.status_code = 500  # Internal Server Error
    mock_get.return_value.raise_for_status.side_effect = requests.HTTPError  # Raise an error

    # Call the function with the mock in place
    with pytest.raises(requests.HTTPError):
        get_account_info('fake_token')

@patch('prosper_api.requests.post')
def test_get_access_token(mock_post):
    # Set up the mock to return a specific response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'access_token': 'fake_token'}

    # Call the function with the mock in place
    result = get_access_token(
        {
            'PROSPER_CLIENT_ID': 'fake_id', 
            'PROSPER_CLIENT_SECRET': 'fake_secret', 
            'PROSPER_USER': 'fake_user', 
            'PROSPER_PASSWORD': 'fake_password'
        }
    )

    # Check that the function returned the expected result
    assert result == 'fake_token'

@patch('prosper_api.requests.post')
def test_get_access_token_incorrect_password(mock_post):
    # Set up the mock to return a specific error response
    mock_post.return_value.status_code = 401  # Unauthorized
    mock_post.return_value.raise_for_status.side_effect = requests.HTTPError  # Raise an error

    # Call the function with the mock in place
    with pytest.raises(requests.HTTPError):
        get_access_token(
            {
                'PROSPER_CLIENT_ID': 'fake_id', 
                'PROSPER_CLIENT_SECRET': 'fake_secret', 
                'PROSPER_USER': 'fake_user', 
                'PROSPER_PASSWORD': 'wrong_password'
            }
        )


@patch('prosper_api.requests.get')
def test_get_listings(mock_get):
    # Set up the mock to return a specific response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'result': [{'listing_number': 1, 'amount': 100}]}

    # Call the function with the mock in place
    result = get_listings('fake_token', limit=1, prosper_rating=['A'])

    # Check that the function returned the expected result
    assert result == {'result': [{'listing_number': 1, 'amount': 100}]}

@patch('prosper_api.requests.get')
def test_get_listings_error_response(mock_get):
    # Set up the mock to return a specific error response
    mock_get.return_value.status_code = 500  # Internal Server Error
    mock_get.return_value.raise_for_status.side_effect = requests.HTTPError  # Raise an error

    # Call the function with the mock in place
    with pytest.raises(requests.HTTPError):
        get_listings('fake_token', limit=1, prosper_rating=['A'])

@patch('prosper_api.requests.post')
def test_invest_in_listing(mock_post):
    # Set up the mock to return a specific response
    mock_post.return_value.status_code = 200

    # Call the function with the mock in place
    invest_in_listing('fake_token', 1, 100)

    # Check that the function made the expected request
    mock_post.assert_called_once_with(PROSPER_ORDER_URL, headers=ANY, json=ANY)

@patch('prosper_api.requests.post')
def test_invest_in_listing_error_response(mock_post):
    # Set up the mock to return a specific error response
    mock_post.return_value.status_code = 500  # Internal Server Error
    mock_post.return_value.raise_for_status.side_effect = requests.HTTPError  # Raise an error

    # Call the function with the mock in place
    with pytest.raises(requests.HTTPError):
        invest_in_listing('fake_token', 1, 100)

"""
This module provides functions to interact with the Prosper API.
It includes functions to get an access token, retrieve account info,
retrieve listings, and invest in a listing.
"""

import requests

# Constants
PROSPER_ORDER_URL = "https://api.prosper.com/v1/orders/"
PROSPER_LISTING_URL = "https://api.prosper.com/listingsvc/v2/listings/"
PROSPER_ACCOUNT_URL = "https://api.prosper.com/v1/accounts/prosper/"
PROSPER_TOKEN_URL = "https://api.prosper.com/v1/security/oauth/token"

def get_access_token(secrets: dict) -> str:
    """Obtain access token for API calls."""

    payload_data = {
        "grant_type": "password",
        "client_id": secrets["PROSPER_CLIENT_ID"],
        "client_secret": secrets["PROSPER_CLIENT_SECRET"],
        "username": secrets["PROSPER_USER"],
        "password": secrets["PROSPER_PASSWORD"]
    }

    headers = {
        'accept': "application/json",
        'content-type': "application/x-www-form-urlencoded"
    }

    response = requests.post(PROSPER_TOKEN_URL, data=payload_data, headers=headers, timeout=10)

    # Handle non-200 status codes
    response.raise_for_status()

    return response.json()['access_token']

def get_account_info(access_token: str) -> dict:
    """Retrieve account information."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(PROSPER_ACCOUNT_URL, headers=headers, timeout=10)

    # Handle non-200 status codes
    response.raise_for_status()

    return response.json()

def get_listings(access_token: str, limit: int = 10, **criteria) -> dict:
    """Retrieve listings based on provided filters."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    params = {
        "limit": limit
    }

    # Add filters to the parameters
    for key, value in criteria.items():
        if isinstance(value, list):
            value = ','.join(value)
        params[key] = value

    response = requests.get(PROSPER_LISTING_URL, headers=headers, params=params, timeout=10)

    # Handle non-200 status codes
    response.raise_for_status()

    return response.json()

def invest_in_listing(access_token: str, listing_number: int, bid_amount: int):
    """Place a bid on a specific listing."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    data = {
        "bid_requests": [
            {
                "listing_id": listing_number,
                "bid_amount": bid_amount
            }
        ]
    }

    response = requests.post(PROSPER_ORDER_URL, headers=headers, json=data, timeout=10)

    if response.status_code == 200:
        print(f"Successfully bid {bid_amount} on listing {listing_number}")
    else:
        # Handle non-200 status codes
        response.raise_for_status()
        print("Error placing bid:")
        print(response.text)

import json
import os
import requests
import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import secretmanager

# Constants
PROSPER_ORDER_URL = "https://api.prosper.com/v1/orders/"
PROSPER_LISTING_URL = "https://api.prosper.com/listingsvc/v2/listings/"
PROSPER_ACCOUNT_URL = "https://api.prosper.com/v1/accounts/prosper/"
PROSPER_TOKEN_URL = "https://api.prosper.com/v1/security/oauth/token"
SECRET_NAMES = ["PROSPER_USER", "PROSPER_PASSWORD", "PROSPER_CLIENT_ID", "PROSPER_CLIENT_SECRET"]


@functions_framework.cloud_event
def subscribe(cloud_event: CloudEvent) -> None:
    main()


def main():
    """Main function to trigger investment process."""
    investment_amount_str = os.environ.get('INVESTMENT_AMOUNT')
    if not investment_amount_str:
        raise ValueError("INVESTMENT_AMOUNT environment variable is not set.")
    investment_amount = int(investment_amount_str)

    access_token = get_access_token()
    account_info = get_account_info(access_token)
    available_balance = account_info.get('available_cash_balance')
    if not available_balance:
        raise ValueError("Failed to fetch available_cash_balance from account_info.")

    if available_balance > investment_amount:
        invest(access_token, available_balance, investment_amount)
    else:
        print("Insufficient funds to invest.")


def invest(access_token: str, available_balance: float, investment_amount: int):
    """Invest in listings based on certain criteria."""
    raw_criteria = os.environ.get('INVESTMENT_CRITERIA')
    if not raw_criteria:
        raise ValueError("INVESTMENT_CRITERIA environment variable is not set.")

    criteria = json.loads(raw_criteria)
    listings = get_listings(access_token, **criteria)

    for listing in listings.get('result', []):
        if available_balance < investment_amount:
            print(f"Insufficient funds to invest. Available balance: {available_balance}")
            break
        available_balance -= investment_amount
        print("Investing in listing:")
        print(json.dumps(listing, indent=4, sort_keys=True))
        invest_in_listing(access_token, listing['listing_number'], investment_amount)


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

    response = requests.get(PROSPER_LISTING_URL, headers=headers, params=params)

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

    response = requests.post(PROSPER_ORDER_URL, headers=headers, json=data)

    if response.status_code == 200:
        print(f"Successfully bid {bid_amount} on listing {listing_number}")
    else:
        print("Error placing bid:")
        print(response.text)


def get_account_info(access_token: str) -> dict:
    """Retrieve account information."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(PROSPER_ACCOUNT_URL, headers=headers)

    # Handle non-200 status codes
    response.raise_for_status()

    return response.json()


def get_access_token() -> str:
    """Obtain access token for API calls."""
    secrets = get_secrets()

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

    response = requests.post(PROSPER_TOKEN_URL, data=payload_data, headers=headers)

    # Handle non-200 status codes
    response.raise_for_status()

    return response.json()['access_token']


def get_secrets() -> dict:
    """Retrieve secrets for authentication."""
    project_id = os.environ.get("GCP_PROJECT")
    if not project_id:
        raise ValueError("GCP_PROJECT environment variable is not set.")

    secret_manager_client = secretmanager.SecretManagerServiceClient()

    secrets = {}
    for secret_name in SECRET_NAMES:
        secret_value = secret_manager_client.access_secret_version(
            name=f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        ).payload.data.decode("UTF-8")

        if not secret_value:
            raise ValueError(f"{secret_name} value is not set in Secret Manager.")

        secrets[secret_name] = secret_value

    return secrets


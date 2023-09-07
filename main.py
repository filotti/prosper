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
    investment_amount = int(os.environ['INVESTMENT_AMOUNT'])
    access_token = get_access_token()
    account_info = get_account_info(access_token)
    available_balance = account_info['available_cash_balance']
    if available_balance > investment_amount:
        invest(access_token, available_balance, investment_amount)


def invest(access_token: str, available_balance: float, investment_amount: int):
    """Invest in listings based on certain criteria."""

    raw_criteria = os.environ.get('INVESTMENT_CRITERIA')
    criteria = json.loads(raw_criteria)

    listings = get_listings(access_token, **criteria)

    for listing in listings['result']:
        if available_balance < investment_amount:
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
    prosper_user, prosper_password, prosper_client_id, prosper_client_secret = get_secrets()
    payload = f"grant_type=password&client_id={prosper_client_id}&client_secret={prosper_client_secret}" \
              f"&username={prosper_user}&password={prosper_password}"
    headers = {'accept': "application/json", 'content-type': "application/x-www-form-urlencoded"}

    response = requests.request("POST", PROSPER_TOKEN_URL, data=payload, headers=headers)

    # Handle non-200 status codes
    response.raise_for_status()

    return response.json()['access_token']


def get_secrets() -> tuple:
    """Retrieve secrets for authentication."""
    project_id = os.environ["GCP_PROJECT"]
    secret_manager_client = secretmanager.SecretManagerServiceClient()

    secrets = {}
    for secret_name in SECRET_NAMES:
        secrets[secret_name] = secret_manager_client.access_secret_version(
            name=f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        ).payload.data.decode("UTF-8")

    return secrets["PROSPER_USER"], secrets["PROSPER_PASSWORD"], secrets["PROSPER_CLIENT_ID"], secrets[
        "PROSPER_CLIENT_SECRET"]

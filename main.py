import json
import os
import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import secretmanager
from prosper_api import get_access_token, get_account_info, get_listings, invest_in_listing

# Constants
SECRET_NAMES = ["PROSPER_USER", "PROSPER_PASSWORD", "PROSPER_CLIENT_ID", "PROSPER_CLIENT_SECRET"]


@functions_framework.cloud_event
def subscribe(cloud_event: CloudEvent) -> None:
    """This function is triggered by a cloud event and calls the main function."""
    main()


def main():
    """Main function to trigger investment process."""
    investment_amount_str = os.environ.get('INVESTMENT_AMOUNT')
    if not investment_amount_str:
        raise ValueError("INVESTMENT_AMOUNT environment variable is not set.")
    investment_amount = int(investment_amount_str)
    secrets = get_secrets()
    access_token = get_access_token(secrets)
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

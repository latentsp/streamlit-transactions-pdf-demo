import os
import requests
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_sync_request_options import TransactionsSyncRequestOptions

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')

_client = None
def get_client():
    global _client
    if _client is None:
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={
                'clientId': PLAID_CLIENT_ID,
                'secret': PLAID_SECRET,
                'plaidVersion': '2020-09-14'
            }
        )

        api_client = plaid.ApiClient(configuration)
        _client = plaid_api.PlaidApi(api_client)
    return _client


def create_public_token(user, password):
    response = requests.post(
        "https://sandbox.plaid.com/sandbox/public_token/create",
        json={
            "client_id": PLAID_CLIENT_ID,
            "secret": PLAID_SECRET,
            "institution_id": "ins_35",
            "initial_products": ["auth", "transactions"],
            "options": {
                "override_username": user,
                "override_password": password,
            }
        }
    )
    print(response.json())


def get_transactions(access_token: str):
    request = TransactionsSyncRequest(
        access_token=access_token,
        options=TransactionsSyncRequestOptions(
            include_original_description=True,
        ),
        count=100,
    )
    response = get_client().transactions_sync(request)
    added_transactions = response.added # removed? modified?
    for transaction in added_transactions:
        yield transaction.to_dict()

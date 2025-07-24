import json
from google import genai
from pydantic import BaseModel


IDENTIFY_INCOME_CATEGORY_PROMPT_FORMAT = """
You are a helpful assistant that selects the correct income category for a given transaction.

Income Categories:
{income_categories}

Transaction:
{transaction}
"""


GROUP_INCOME_SOURCES_PROMPT_FORMAT = """
You are a helpful assistant that groups income sources for a given list of transactions. Group by income category, place of work, etc.

Income Categories:
{income_categories}

Transactions:
{transactions}
"""



IDENTIFY_STRUCTURES_PROMPT_FORMAT = """
You are a helpful financial assistant. Your task is to analyze a list of transactions and identify recurring transfers that indicate money is being moved to another account belonging to the **same person**.

The goal is to find transfers that are movements of personal assets, not payments for goods, services, or loans.

<transaction_data>
{transaction_data}
</transaction_data>
"""


SUPPORTED_INCOME_CATEGORIES = [
    "refund",
    "selfEmployed1099",
    "uncategorizedIncome",
    "disabilityMaternityBenefits",
    "unemployment",
    "bankInterest",
    "governmentCashAssistance",
    "supplementalSecurityIncome",
    "socialSecurityBenefits",
    "veteransPensionBenefits",
    "militaryIncome",
    "childSupport",
    "loan",
    "cashbackReward",
    "transfer",
    "nonIncomeOther",
    "paycheckW2",
    "federalIrsPayment",
    "stateTaxRefund",
]


_genai_client = None
def get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


_taxonomy_rules = None
def get_taxonomy_rules():
    global _taxonomy_rules
    if _taxonomy_rules is None:
        with open("data/credit_taxonomy_rules.csv", "r") as f:
            taxonomy_rules = []
            for line in f:
                taxonomy_rules.append(line)
        _taxonomy_rules = "\n".join(taxonomy_rules)
    return _taxonomy_rules


class IncomeCategory(BaseModel):
    reasoning: str
    income_category: str


class IncomeSourceGroup(BaseModel):
    title: str
    income_category: str
    description: str
    transaction_ids: list[str]


class Structure(BaseModel):
    title: str
    transaction_ids: list[str]
    description: str


def identify_income_category(transaction: dict) -> str:
    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[
            IDENTIFY_INCOME_CATEGORY_PROMPT_FORMAT.format(
                transaction=json.dumps(transaction, indent=2, default=str),
                income_categories="\n".join(SUPPORTED_INCOME_CATEGORIES),
            )
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": IncomeCategory,
        },
    )
    return response.parsed.income_category


def group_income_sources(transactions: list[dict]) -> list[IncomeSourceGroup]:
    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[
            GROUP_INCOME_SOURCES_PROMPT_FORMAT.format(
                transactions=json.dumps(transactions, indent=2, default=str),
                income_categories="\n".join(SUPPORTED_INCOME_CATEGORIES),
            )
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[IncomeSourceGroup],
        },
    )
    return response.parsed


def identify_structures(transactions: list[dict]) -> list[Structure]:
    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[
            IDENTIFY_STRUCTURES_PROMPT_FORMAT.format(
                transaction_data=json.dumps(transactions, indent=2, default=str),
            )
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Structure],
        },
    )
    return response.parsed

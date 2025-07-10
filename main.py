import streamlit as st
from google import genai
import pandas as pd
from pydantic import BaseModel, Field   


class Transaction(BaseModel):
    date: str
    description: str
    amount: float
    is_credit: bool = Field(description="is credit or debit")
    category: str = Field(description="category of transaction")


class Structure(BaseModel):
    title: str
    transactions: list[Transaction]
    description: str


EXTRACT_TRANSACTIONS_PROMPT_FORMAT = """
You are a helpful and proactive financial assistant. 
Your goal is to analyze a user's bank statement and extract all the transactions.

Transaction Categories:
{transaction_categories}
"""

IDENTIFY_STRUCTURES_PROMPT_FORMAT = """
You are a helpful and proactive financial assistant. 
Your goal is to analyze a user's bank transactions to identify patterns.
You are specifically looking for regular, recurring transfers to the same recipient, which might indicate the user is moving money to another one of their own accounts. 
Your tone should be helpful and inquisitive, not accusatory.

Objective:
Analyze the provided list of bank account transactions to identify any patterns of recurring payments made to the same individual or entity. 
The pattern should be strong enough to suggest that the user might be regularly transferring funds to another account they potentially own.

Output:
Return a list of structures with the list of transactions that make up the structure.
If there are no potential structures, return an empty list.


<transaction_data>
{transaction_data}
</transaction_data>
"""

TRANSACTION_CATEGORIES = [
    "Food & Drink",
    "Restaurants & Cafes",
    "Groceries & Supermarkets",
    "Transportation",
    "Travel & Lodging",
    "Health & Medical",
    "Fitness & Sports",
    "Entertainment & Leisure",
    "Shopping & Retail",
    "Home & Garden",
    "Financial Services",
    "Insurance",
    "Utilities & Bills",
    "Education",
    "Children & Family",
    "Pets & Animals",
    "Automotive",
    "Professional Services",
    "Government & Non-Profit",
    "Technology & Electronics",
    "Personal Care & Beauty",
    "Real Estate & Property",
    "Taxes & Government",
    "Miscellaneous",
    "Outdoors & Nature",
    "Legal",
    "Banking & Finance",
]

_genai_client = None
def get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


def extract_transactions(pdf_bytes: bytes) -> list[Transaction]:
    client = get_genai_client()
    transaction_categories_str = "\n".join([f"- {t}" for t in TRANSACTION_CATEGORIES])
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[
            genai.types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            EXTRACT_TRANSACTIONS_PROMPT_FORMAT.format(transaction_categories=transaction_categories_str),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Transaction],
        },
    )
    return response.parsed


def identify_structures(transactions: list[Transaction]) -> list[Structure]:
    client = get_genai_client()
    transactions_str = "\n".join([t.model_dump_json(indent=2) for t in transactions])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            IDENTIFY_STRUCTURES_PROMPT_FORMAT.format(transaction_data=transactions_str),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Structure],
        },
    )   
    return response.parsed


def print_transactions(transactions: list[Transaction]):
    data_frame = pd.DataFrame([t.model_dump(exclude={"is_credit"}) for t in transactions])
    st.dataframe(data_frame)


uploaded_file = st.file_uploader("Choose file")
if uploaded_file:
    st.write("-" * 100)
    with st.spinner("Extracting transactions..."):
        transactions = extract_transactions(uploaded_file.getvalue())
        st.write("Transactions:")
        credit, debit = st.tabs(["Credit", "Debit"])
        with credit:
            print_transactions([t for t in transactions if t.is_credit])
        with debit:
            print_transactions([t for t in transactions if not t.is_credit])
    if transactions:
        st.write("-" * 100)
        with st.spinner("Identifying structures..."):
            structures = identify_structures(transactions)
            if any([structure.transactions for structure in structures]):
                st.write("Structures found:")
                for structure in structures:
                    if structure.transactions:
                        with st.expander(structure.title.replace("$", "\\$")):
                            print_transactions(structure.transactions)
                            st.write(structure.description.replace("$", "\\$"))
            else:
                st.write("No structures found")

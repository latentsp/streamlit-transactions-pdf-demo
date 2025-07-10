import streamlit as st
from google import genai
import pandas as pd
from pydantic import BaseModel


class Transaction(BaseModel):
    date: str
    description: str
    amount: float


class Structure(BaseModel):
    title: str
    transactions: list[Transaction]
    description: str


IDENTIFY_STRUCTURES_PROMPT_FORMAT = """
You are a helpful and proactive financial assistant AI. 
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

_genai_client = None
def get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


def extract_transactions(pdf_bytes: bytes) -> list[Transaction]:
    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[
            genai.types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            "Extract all the transactions from the pdf"
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


uploaded_file = st.file_uploader("Choose file")
if uploaded_file:
    st.write("-" * 100)
    with st.spinner("Extracting transactions..."):
        transactions = extract_transactions(uploaded_file.getvalue())
        st.write("Transactions:")
        data_frame = pd.DataFrame([t.model_dump() for t in transactions])
        st.dataframe(data_frame)
    if transactions:
        st.write("-" * 100)
        with st.spinner("Identifying structures..."):
            structures = identify_structures(transactions)
            if any([structure.transactions for structure in structures]):
                st.write("Structures found:")
                for structure in structures:
                    if structure.transactions:
                        with st.expander(structure.title.replace("$", "\\$")):
                            data_frame = pd.DataFrame([t.model_dump() for t in structure.transactions])
                            st.dataframe(data_frame)
                            st.write(structure.description.replace("$", "\\$"))
            else:
                st.write("No structures found")

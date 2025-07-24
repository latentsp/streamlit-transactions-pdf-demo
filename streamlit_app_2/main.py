import streamlit as st
import pandas as pd
from plaid_helper import get_transactions
from llm_helper import identify_structures, group_income_sources

def get_lean_transaction(transaction: dict):
    keys = {
        "merchant_name": "Name",
        "date": "Date",
        "original_description": "Description",
        "amount": "Amount",
        "income_category": "Income Category",
    }
    return {keys[k]: transaction[k] for k in keys if transaction.get(k) is not None}


access_token = st.text_input("Access Token")
if st.button("Load Transactions"):
    st.write("-" * 100)
    with st.spinner("Loading transactions..."):
        transactions = list(get_transactions(access_token))
        with st.expander("All transactions"):
            data_frame = pd.DataFrame([get_lean_transaction(t) for t in transactions])
            st.dataframe(data_frame)

    income_transactions = {}
    transfer_transactions = {}
    for transaction in transactions:
        transaction_id = transaction["transaction_id"]
        if transaction["amount"] < 0:
            income_transactions[transaction_id] = transaction
        else:
            transfer_transactions[transaction_id] = transaction

    st.write("-" * 100)
    with st.spinner("Identifying incomes..."):
        if income_transactions:
            income_sources = group_income_sources(income_transactions.values())
            st.write("Income:")
            for income_source in income_sources:
                with st.expander(income_source.title.replace("$", "\\$") + f" ({income_source.income_category})"):
                    st.write(income_source.description.replace("$", "\\$"))
                    data_frame = pd.DataFrame([get_lean_transaction(income_transactions[t]) for t in income_source.transaction_ids if t in income_transactions])
                    st.dataframe(data_frame)
        else:
            st.write("No income transactions found")

    st.write("-" * 100)
    with st.spinner("Identifying structures..."):
        structures = identify_structures(transfer_transactions.values())
        if any([structure.transaction_ids for structure in structures]):
            st.write("Structures found:")
            for structure in structures:
                if structure.transaction_ids:
                    with st.expander(structure.title.replace("$", "\\$")):
                        data_frame = pd.DataFrame([get_lean_transaction(transfer_transactions[t]) for t in structure.transaction_ids])
                        st.dataframe(data_frame)
                        st.write(structure.description.replace("$", "\\$"))
        else:
            st.write("No structures found")

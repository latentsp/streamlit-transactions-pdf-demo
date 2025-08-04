import streamlit as st
import pandas as pd


def get_columns_config(columns):
    base = {c: None for c in columns}
    base["transaction_date"] = st.column_config.DateColumn(label="Date")
    base["description"] = st.column_config.TextColumn(label="Description")
    base["amount"] = st.column_config.NumberColumn(label="Amount")
    base["income_category"] = st.column_config.TextColumn(label="SteadyIQ Income Category")
    base["llm_income_category_name"] = st.column_config.TextColumn(label="LLM Income Category")
    return base



UNCATEGORIZED_INCOME_ID = "184287dd-bed3-48c6-820a-8b4fe57a131c"


uploaded_file = st.file_uploader("Choose file", type=["csv"])
if uploaded_file:
    with st.spinner("Loading transactions..."):
        summary_container = st.container(border=True)
        transactions = pd.read_csv(uploaded_file)
        summary_container.metric("Total Transactions", len(transactions))
        col1, col2 = summary_container.columns(2, vertical_alignment="center", border=True)

        categorized_transactions_steadyiq = transactions[transactions["income_category_id"] != UNCATEGORIZED_INCOME_ID]
        categorized_percentage_steadyiq = 100 * len(categorized_transactions_steadyiq) / len(transactions)
        col1.metric("Categorized (SteadyIQ)", f"{len(categorized_transactions_steadyiq)} ({categorized_percentage_steadyiq:.2f}%)")
        categorized_transactions_llm = transactions[transactions["llm_income_category_id"] != UNCATEGORIZED_INCOME_ID]
        categorized_percentage_llm = 100 * len(categorized_transactions_llm) / len(transactions)
        categorized_delta = 100 * (categorized_percentage_llm / categorized_percentage_steadyiq - 1)
        col2.metric("Categorized (LLM)", f"{len(categorized_transactions_llm)} ({categorized_percentage_llm:.2f}%)", delta=f"{categorized_delta:.2f}%")
        
        col1, col2, col3 = summary_container.columns(3, vertical_alignment="center", border=True)
        num_matches = categorized_transactions_steadyiq["match"].sum()
        col1.metric("Total Matches (of categorized)", int(num_matches))
        num_missmatches = len(categorized_transactions_steadyiq) - num_matches
        col2.metric("Total Missmatches (of categorized)", int(num_missmatches))
        col3.metric("Match Rate (of categorized)", f"{num_matches/len(categorized_transactions_steadyiq)*100:.2f}%")
        
        missmatches_container = st.container(border=True)
        missmatched_transactions = categorized_transactions_steadyiq[categorized_transactions_steadyiq["match"] == False]
        missmatches_container.write("Missmatches:")
        missmatches_container.dataframe(missmatched_transactions, column_config=get_columns_config(missmatched_transactions.columns))

        new_categorizations_container = st.container(border=True)
        uncategorized_transactions = transactions[transactions["income_category_id"] == UNCATEGORIZED_INCOME_ID]
        newly_categorized_transactions = uncategorized_transactions[uncategorized_transactions["llm_income_category_id"] != UNCATEGORIZED_INCOME_ID]
        new_categorizations_container.write("Newly categorized transactions:")
        new_categorizations_container.dataframe(newly_categorized_transactions, column_config=get_columns_config(newly_categorized_transactions.columns))

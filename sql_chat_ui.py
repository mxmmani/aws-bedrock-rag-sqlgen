import streamlit as st
import sql_query_chain
import re
import mssql_helper
import pandas as pd
import logging
from logging.handlers import RotatingFileHandler

# Configure logging with rotation
log_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=2)  # 5 MB per file, max 2 files
logging.basicConfig(handlers=[log_handler], level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def ask_question(question):
    sql_chain_response = sql_query_chain.sql_chain(question)
    return sql_chain_response

def is_query_present(response):
    pattern = r'\bSQLQuery:\s*(.+)'
    return re.search(pattern, response, re.IGNORECASE | re.DOTALL)

def extract_query(response):
    query_text = ""
    pattern = r'\bSQLQuery:\s*(SELECT .+)'  # Adjusted regex pattern to capture only SELECT queries
    match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
    if match:
        query_text = match.group(1).strip()  # Extracts only the SQL query
    return query_text


def run_query(query):
    try:
        logging.info(query)  # Log only the query
        status, columns, query_result = mssql_helper.run_query(query)
        if query_result and status == "success":
            df = pd.DataFrame(query_result, columns=columns)
            return df
    except Exception as e:
        logging.error("Error in run_query: %s", str(e))
        raise


# Initialize chat history
hello_message = f"""Hello 👋. I am HR assistant. I can take a natural language question as input, analyze and get back to you with results!
Here are a few examples of questions I can help answer by generating a MSSQL query:

- What is the average absence duration per employee?

- Calculate Bradford score for each employee

- List the top five outliers?"""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": hello_message, "type": "text"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("type", "text") == "code":
            st.code(message["content"], language="sql")
        else:
            st.markdown(message["content"])

prompt = st.chat_input("Write your question")

if prompt:
     # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        response_list = []
        response = ask_question(prompt)
        response_list.append(response)

        for response in response_list:
            full_response += response
            message_placeholder.code(full_response + "▌", language="sql")
        message_placeholder.code(full_response, language="sql")
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        if is_query_present(response):
            query = extract_query(response)
            if query:
               df = run_query(query=query)
               if df is not None and not df.empty:
                   message_placeholder.dataframe(df)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "code"})

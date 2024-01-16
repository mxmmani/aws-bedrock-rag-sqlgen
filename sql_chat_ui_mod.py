import streamlit as st
import sql_query_chain_mod
import re
import mssql_helper
import pandas as pd
import logging
from logging.handlers import RotatingFileHandler

# Configure logging with rotation
log_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=2)  
logging.basicConfig(handlers=[log_handler], level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def ask_question(question):
    return sql_query_chain_mod.sql_chain(question)

def is_query_present(response):
    pattern = r'\bSQLQuery:\s*(.+)'
    return re.search(pattern, response, re.IGNORECASE | re.DOTALL)

def extract_query(response):
    pattern = r'\bSQLQuery:\s*(SELECT .+?;)'
    match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def run_query(query):
    try:
        logging.info(query)
        print('\n<start_chat_ui> Running Query - ')
        print(query)
        return mssql_helper.run_query(query)
    except Exception as e:
        logging.error("Error in run_query: %s", str(e))
        raise

def get_descriptive_response_from_model(original_prompt, query_result_df):
    query_result_str = query_result_df.to_json(orient="records")
    print('\n<start_chat_ui> Query Results as String - ')
    print(query_result_str)
    logging.info(query_result_str)
    model_input = {
        "original_prompt": original_prompt,
        "query_result": query_result_str
    }
    print('\n<start_chat_ui> Final Model Input - ')
    print(model_input)    
    return sql_query_chain_mod.get_model_response(model_input)

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
        st.markdown(message["content"])

prompt = st.chat_input("Write your question")
logging.info(prompt)
print ('\n<sql_chat_ui> Prompt: ')
print(prompt)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = ask_question(prompt)
        print ('\n<sql_chat_ui> Response: ')
        print(response)
        if is_query_present(response):
            query = extract_query(response)
            if query:
                status, columns, query_result = run_query(query)
                print('\n<start_chat_ui> Query Result and Status!!! ')
                print(pd.DataFrame(query_result, columns=columns))
                print(status)
                if query_result and status == "success":
                    df = pd.DataFrame(query_result, columns=columns)
                    descriptive_response = get_descriptive_response_from_model(prompt, df)
                    print('\n<start_chat_ui> Descriptive Response!!! ')
                    print(descriptive_response)
                    st.markdown(descriptive_response)
                    st.session_state.messages.append({"role": "assistant", "content": descriptive_response, "type": "text"})
                    
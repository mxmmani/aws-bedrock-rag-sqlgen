import boto3
import botocore
import time
from langchain.document_loaders import TextLoader
from langchain.embeddings import BedrockEmbeddings
from langchain.llms import Bedrock
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from opensearchpy import OpenSearch, helpers
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

client = boto3.client('opensearchserverless')
service = 'aoss'
region = 'us-east-1'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)

# OpenSearch Configuration
host = 'tjiy2vj1scpfe6yup2ul.us-east-1.aoss.amazonaws.com'  # Use your Serverless domain endpoint
port = 443  # Typically 443 for HTTPS
use_ssl = True

# OpenSearch Client
opensearch_client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    use_ssl=use_ssl,
    verify_certs=True,
    http_auth=awsauth,
    connection_class=RequestsHttpConnection    
)
print('<sql_query_chain> Client initialized as follows:')
print(opensearch_client)

# Function to convert Document to a dictionary
def document_to_dict(doc):
    return {
        "page_content": doc.page_content,
        "metadata": doc.metadata
    }

# Function to Index Documents (Updated Method)
def index_documents(docs):
    # Check if the index exists, and create it if it doesn't
    index_name = 'empindex'
    if not opensearch_client.indices.exists(index=index_name):
        opensearch_client.indices.create(index=index_name)
        print(f"Index '{index_name}' created.")
    else:
        print(f"Index '{index_name}' already exists.")

    for doc in docs:
        response = opensearch_client.index(
            index=index_name, 
            body=document_to_dict(doc)
        )
        print('<sql_query_chain> Document added:', response)
        
# Replace vectorstore_retriever with OpenSearch Query Function
def opensearch_retriever(query, index_name="empindex", search_kwargs={"size": 1}):
    response = opensearch_client.search(
        index=index_name,
        body={
            "query": {
                "match": {
                    "page_content": query  
                }
            }
        },
        **search_kwargs
    )
    return response['hits']['hits']

#embeddings_model_id = "amazon.titan-embed-text-v1"
credentials_profile_name = "default"

#bedrock_embedding = BedrockEmbeddings(
#    credentials_profile_name=credentials_profile_name,
#    model_id=embeddings_model_id
#)

anthropic_claude_llm = Bedrock(
    credentials_profile_name=credentials_profile_name,
    model_id="anthropic.claude-v2"
)

TEMPLATE = """You are an expert in writing syntactically correct MSSQL queries and have great knowledge of the Employee Attendance System!
Given an input question, first create a syntactically correct MSSQL query to run and then return the query.
If asked to calculate the Bradford Score, calculate it as the square of the number of separate instances of absence (S) multiplied by the total number of days of absence (D) for each employee.
Ensure to use only existing columns and tables from the provided context and replace 'EmployeeID' with 'EmployeeName' in the queries.
Avoid wrapping table names with square brackets and ensure that each query ends with a semicolon.
Make sure that the query is syntactically correct and use the best of your knowledge. Avoid hallucinations!
Use the following format:

Question: "Question here"
SQLQuery: "SQL Query to run"

Answer the question based on the following context:
-- Database Schema
CREATE DATABASE employeedb;
--
CREATE TABLE EmployeeAbsence 
(
 EmployeeID INT,
 EmployeeName NVARCHAR(255),
 AbsenceCode INT,
 AbsenceName NVARCHAR(255),
 Duration INT,
 StartDate DATE
);

Some examples of SQL queries that correspond to questions are:

-- Calculate the Total Absence Duration for Each Employee
SELECT EmployeeName, SUM(Duration) AS TotalAbsenceDuration 
FROM employeedb.dbo.EmployeeAbsence 
GROUP BY EmployeeName;

-- Total Number of Absence Days for Each Employee
SELECT EmployeeName, SUM(Duration) AS TotalAbsenceDays
FROM employeedb.dbo.EmployeeAbsence
GROUP BY EmployeeName;

-- Count of Absences for Each Type of Absence
SELECT AbsenceCode, COUNT(*) AS NumberOfAbsences
FROM employeedb.dbo.EmployeeAbsence
GROUP BY AbsenceCode;

-- Total Number of Employees Who Have Taken Each Type of Absence
SELECT AbsenceCode, COUNT(DISTINCT EmployeeName) AS TotalEmployees
FROM employeedb.dbo.EmployeeAbsence
GROUP BY AbsenceCode;

Question: {question}"""

custom_prompt_template = PromptTemplate(
    input_variables=["context", "question"], template=TEMPLATE
)

print('\n<sql_query_chain> Template initialized: '+TEMPLATE)

# Load the DDL document and split it into chunks
loader = TextLoader("employee_ddl.sql")
documents = loader.load()

print('\n<sql_query_chain> Loaded the DDL document: ')
print(loader)
print(documents)

# Split document into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=0, separators=[" ", ",", "\n"]
)
docs = text_splitter.split_documents(documents)

print('\n<sql_query_chain> Splitting into Chunks: ')
print(text_splitter)
print(docs)

# Convert documents to dictionary and Index them into OpenSearch
index_documents(docs)
print('\n<sql_query_chain> Indexing Completed')

model = anthropic_claude_llm
prompt = ChatPromptTemplate.from_template(TEMPLATE)

# Function to interact with the anthropic_claude_llm model
def get_model_response(model_input):
    """
    Send the combined input (original_prompt and query_result) to the anthropic_claude_llm model
    and return the model's response.
    """
    # Combine the original prompt and query results into a single string
    combined_prompt = f"Original question: {model_input['original_prompt']}\nQuery results: {model_input['query_result']}\n\nPlease provide a summary:"

    # Pass the combined prompt as the 'text' argument to the predict method
    model_response = anthropic_claude_llm.predict(text=combined_prompt)  # Adjust this line as per your model's API

    # If the response from the model is a string, directly use it as the descriptive response
    descriptive_response = model_response if isinstance(model_response, str) else "No descriptive response generated."

    return descriptive_response
    
# Define the sql_chain function
def sql_chain(question):
    chain = (
        {
            "context": opensearch_retriever,  
            "question": RunnablePassthrough()
        }
        | prompt
        | model
        | StrOutputParser()
    )
    return chain.invoke(question)

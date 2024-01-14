from langchain.document_loaders import TextLoader
from langchain.embeddings import BedrockEmbeddings
from langchain.llms import Bedrock
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

#from opensearchpy import OpenSearch
#import json

embeddings_model_id = "amazon.titan-embed-text-v1"
credentials_profile_name = "default"
region_name = "us-east-1"

bedrock_embedding = BedrockEmbeddings(
    credentials_profile_name=credentials_profile_name,
    region_name=region_name,
    model_id=embeddings_model_id
)

anthropic_claude_llm = Bedrock(
    credentials_profile_name=credentials_profile_name,
    model_id="anthropic.claude-v2"
)

#While generating query, make sure it is supported by SQLite or else just reply that you cannot achieve this.

TEMPLATE = """You are an MSSQL expert and have great knowledge of Employee Attendance System!
Given an input question, first create a syntactically correct MSSQL query to run and then return the query.
Make sure to use only existing columns and tables. 
Try to inlcude EmployeeName column in the query instead of EmployeeID. 
Do not wrap table names with square brackets and make sure to end queries with ;.
Ensure that the query is syntactically correct and use the best of your knowledge. If you cannot form a query, just say no.
Use the following format:

Question: "Question here"
SQLQuery: "SQL Query to run"

Answer the question based on the following context:
{context}

Some examples of SQL queries that correspond to questions are:

-- Calculate the Total Absence Duration for Each Employee
SELECT EmployeeID, SUM(Duration) AS TotalAbsenceDuration FROM employeedb.dbo.EmployeeAbsence GROUP BY EmployeeID;

-- Total Number of Absence Days for Each Employee
SELECT EmployeeID, SUM(Duration) AS TotalAbsenceDays
FROM employeedb.dbo.EmployeeAbsence
GROUP BY EmployeeID;

-- Count of Absences for Each Type of Absence
SELECT AbsenceCode, COUNT(*) AS NumberOfAbsences
FROM employeedb.dbo.EmployeeAbsence
GROUP BY AbsenceCode;

-- Total Number of Employees Who Have Taken Each Type of Absence
SELECT AbsenceCode, COUNT(DISTINCT EmployeeID) AS TotalEmployees
FROM employeedb.dbo.EmployeeAbsence
GROUP BY AbsenceCode;

Question: {question}"""

custom_prompt_template = PromptTemplate(
    input_variables=["context", "question"], template=TEMPLATE
)

# Load the DDL document and split it into chunks
loader = TextLoader("employee_ddl.sql")
documents = loader.load()

# Split document into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=0, separators=[" ", ",", "\n"]
)
docs = text_splitter.split_documents(documents)

# Load the embeddings into Chroma in-memory vector store
vectorstore = Chroma.from_documents(docs, embedding=bedrock_embedding)
vectorstore_retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

# Assuming OpenSearch connection setup here
#os = OpenSearch(
#    hosts=[{'host': 'localhost', 'port': 9200}],
#    http_compress=True  # Enables gzip compression for request bodies
#)

# Load the DDL document and split it into chunks
#loader = TextLoader("employee_ddl.sql")
#documents = loader.load()
#text_splitter = RecursiveCharacterTextSplitter(
#    chunk_size=1000, chunk_overlap=0, separators=[" ", ",", "\n"]
#)
#docs = text_splitter.split_documents(documents)

# Index documents and their embeddings in OpenSearch
#for i, doc in enumerate(docs):
#    embedding = bedrock_embedding(doc)  # Generate embedding for the document
#    body = {
#        "document": doc,
#        "embedding": embedding.tolist()  # Convert embedding to list if it's not
#    }
#    os.index(index="your_index", id=i, body=json.dumps(body))

# Function to perform vector search in OpenSearch
#def vector_search(query_vector, k=1):
 #   search_body = {
  #      "size": k,
   #     "query": {
    #        "knn": {
    #            "field": "embedding",
    #            "vector": query_vector,
    #            "k": k
    #        }
    #    }
    #}
    #response = os.search(index="your_index", body=search_body)
    #vectorstore_retriever = response

# Example usage
# query_vector = [0.1, 0.2, 0.3, ...]  # Your query vector
# results = vector_search(query_vector, k=1)


model = anthropic_claude_llm
prompt = ChatPromptTemplate.from_template(TEMPLATE)
chain = (
    {
        "context": vectorstore_retriever,
        "question": RunnablePassthrough()
    }
    | prompt
    | model
    | StrOutputParser()
)


def sql_chain(question):
    chain = (
        {
            "context": vectorstore_retriever,
            "question": RunnablePassthrough()
        }
        | prompt
        | model
        | StrOutputParser()
    )
    return chain.invoke(question)

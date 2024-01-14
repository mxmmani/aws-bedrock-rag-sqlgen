# SQL Query Generation for Enhanced Analytical Queries using RAG and Streamlit
# Overview
Retrieval Augmented Generation (RAG) models have revolutionized conversational AI with their ability to generate coherent responses. However, they fall short in handling analytical queries effectively, particularly in scenarios requiring complex data analysis and reasoning. This limitation is a significant challenge in enterprise settings where precise, data-driven decision-making is crucial.

# Solution
This project presents a novel solution to enhance RAG's analytical query handling capabilities. By integrating a Streamlit app and advanced SQL query generation techniques, we transform the way RAG interacts with databases, enabling it to process and respond to complex analytical queries. Our approach is inspired by the [SQL Query Generator](https://github.com/aws-samples/amazon-bedrock-samples/tree/02502abfc42d873aa560c30fa0cc03aa8fb904f7/rag-solutions/sql-query-generator) in Amazon Bedrock Samples, which demonstrates the potential of this integration.

# Key Features and Implementation
Streamlit for User Interaction: A Streamlit application serves as the interface for users to input natural language queries, offering a seamless and intuitive user experience.

Advanced SQL Query Generation: The core of our solution lies in converting natural language queries into SQL queries. This enables RAG to fetch relevant data from databases efficiently, thereby providing accurate analytical responses.

Database: Our system is designed to work with Microsoft SQL Server RDS. This change is aimed at enhancing scalability, security, and performance, making the system more suitable for enterprise-level applications.

# Getting Started
Instructions for setting up the project, including the installation of necessary dependencies, configuration of the Streamlit app, and connection to the Microsoft SQL Server RDS, can be found in the subsequent sections.

## Contents

There are key components of the implementation:

* sql_chat_ui.py - Streamlit application in Python
* sql_query_chain.py - Supporting file to make calls to Bedrock to run the SQL chain
* requirements.txt - Requirements file, and a data file to search against
* mssql_helper.py - MSSQL helper file to run queries
* employee_ddl.sql - Context file for the LLM to understand the SQL schema

## Requirements

You need an AWS account with following Bedrock models enabled;
* amazon.titan-embed-text-v1
* anthropic.claude-v2

You need to [setup your AWS profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) and setup your "default" profile with the AWS account credentials where you have above Bedrock models enabled

## Setup

From the command line, run the following in the code folder:

```
pip3 install -r requirements.txt -U
```

## Running

From the command line, run the following in the code folder:

```
streamlit run sql_chat_ui.py
```

You should now be able to access the Streamlit web application from your browser.

## Try a few prompts from the web application:

* What is the average absence duration per employee?
* Calculate Bradford score for each employee
* List the top five outliers?
